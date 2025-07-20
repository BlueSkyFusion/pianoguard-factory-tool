#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3

import os
import subprocess
import hashlib
import json
import requests
import qrcode
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

FIRMWARE_PATH = os.path.join(os.path.dirname(__file__), "firmware", "firmware.bin")
LABELS_DIR = os.path.join(os.path.dirname(__file__), "labels")
API_SERVER_URL = "https://your-api-server.com/api/v1/register"
FACTORY_API_KEY = os.environ.get("PIANOGUARD_FACTORY_KEY", "your_super_secret_factory_key")
UNIT_COUNTER_PATH = os.path.join(LABELS_DIR, "unit_counter.txt")

os.makedirs(LABELS_DIR, exist_ok=True)

def flash_firmware(port):
    print(">>> [STEP 1/5] Flashing Firmware...")
    if not os.path.isfile(FIRMWARE_PATH):
        raise FileNotFoundError("Firmware binary not found. Build it first.")

    cmd = [
        "esptool.py",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", "460800",
        "write_flash", "-z", "0x1000",
        FIRMWARE_PATH
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("Firmware flashing failed.")
    print("SUCCESS: Firmware flash complete.")

def get_mac_address(port):
    print(">>> [STEP 2/5] Reading MAC Address...")
    cmd = [
        "esptool.py",
        "--port", port,
        "read_mac"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("Failed to read MAC address.")

    for line in result.stdout.splitlines():
        if "MAC:" in line:
            mac = line.split("MAC:")[-1].strip()
            print(f"SUCCESS: Found MAC Address: {mac}")
            return mac
    raise Exception("MAC address not found.")

def hash_device_id(mac):
    print(f">>> [STEP 3/5] Hashing Device ID from MAC ({mac})...")
    hashed = hashlib.sha256(mac.encode()).hexdigest()[:16].upper()
    print(f"SUCCESS: Hashed to {hashed}")
    return hashed

def post_to_api(device_id):
    print(">>> [STEP 4/5] Pre-registering Device in Database...")
    headers = {
        "Authorization": f"Bearer {FACTORY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "device_id": device_id
    }
    response = requests.post(API_SERVER_URL, headers=headers, data=json.dumps(payload))
    print(f"API Response Status: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"API error: {response.text}")
    print("SUCCESS: API call successful.", response.text)

def get_next_unit_number():
    try:
        with open(UNIT_COUNTER_PATH, "r") as f:
            count = int(f.read().strip()) + 1
    except FileNotFoundError:
        count = 1
    with open(UNIT_COUNTER_PATH, "w") as f:
        f.write(str(count))
    return count

def generate_qr_label(device_id):
    print(">>> [STEP 5/5] Generating Label Info...")
    unit_number = get_next_unit_number()
    short_id = device_id[-8:]
    label_name = f"device_{unit_number:03d}_{short_id}.png"
    label_path = os.path.join(LABELS_DIR, label_name)

    img = qrcode.make(device_id)
    img.save(label_path)

    label_txt_path = label_path.replace(".png", ".txt")
    with open(label_txt_path, "w") as f:
        f.write(device_id)

    print(f"SUCCESS: Printed label: {label_path}")
    print("SUCCESS: Label info generated and saved.")
    return label_path, short_id

def run_factory_process(port, log_widget, id_label):
    try:
        log_widget.delete("1.0", tk.END)

        flash_firmware(port)
        log_widget.insert(tk.END, "Firmware flashed.\n")
        log_widget.update()

        mac = get_mac_address(port)
        log_widget.insert(tk.END, f"MAC Address: {mac}\n")
        log_widget.update()

        device_id = hash_device_id(mac)
        log_widget.insert(tk.END, f"Device ID: {device_id}\n")
        log_widget.update()

        post_to_api(device_id)
        log_widget.insert(tk.END, "API call successful.\n")
        log_widget.update()

        _, short_id = generate_qr_label(device_id)
        id_label.config(text=f"Human-Readable ID: {short_id}")
        log_widget.insert(tk.END, f"QR label created: {short_id}\n")

        messagebox.showinfo("Success", "Device provisioning completed successfully!")

    except Exception as e:
        log_widget.insert(tk.END, f"---!!!-!!!---\nERROR: {str(e)}\n---!!!-!!!---\n")
        messagebox.showerror("Error", f"An error occurred: {e}")

def create_gui():
    root = tk.Tk()
    root.title("PianoGuard Factory Provisioning Tool v1.1")

    frm = ttk.Frame(root, padding=10)
    frm.grid()

    port_label = ttk.Label(frm, text="ESP32 Serial Port:")
    port_label.grid(column=0, row=0, sticky="w")

    port_entry = ttk.Entry(frm, width=40)
    port_entry.insert(0, "/dev/cu.usbmodem101")
    port_entry.grid(column=0, row=1, columnspan=2, sticky="we", pady=5)

    start_button = ttk.Button(
        frm,
        text="Start Full Provisioning Process",
        command=lambda: run_factory_process(port_entry.get(), log_output, id_output)
    )
    start_button.grid(column=0, row=2, columnspan=2, pady=10)

    log_output = tk.Text(frm, height=15, width=80, bg="black", fg="white")
    log_output.grid(column=0, row=3, columnspan=2)

    ttk.Label(frm, text="Generated Label Info:").grid(column=0, row=4, sticky="w")
    id_output = ttk.Label(frm, text="Human-Readable ID: -", font=("Courier", 14))
    id_output.grid(column=0, row=5, sticky="w")

    root.mainloop()

if __name__ == "__main__":
    create_gui()