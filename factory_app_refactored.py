#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
#
# factory_app_refactored.py
#
# Created on: 2025-06-25
# Edited on: 2025-07-20
#     Author: Andwardo
#     Version: v1.1.0
#
# v1.1.0 - Refactored for maintainability, CLI extensibility, and firmware version control
#

import subprocess
import hashlib
import requests
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont

API_SERVER_URL = "https://45.56.69.50"
FACTORY_API_KEY = os.environ.get("PIANOGUARD_FACTORY_KEY", "your_super_secret_factory_key")
DEFAULT_PORT = "/dev/cu.usbmodem101"
LABEL_DIR = "labels"
COUNTER_FILE = os.path.join(LABEL_DIR, "unit_counter.txt")

class FactoryProvisioningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PianoGuard Factory Provisioning Tool v1.1")
        self.root.geometry("600x700")

        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        os.makedirs(LABEL_DIR, exist_ok=True)
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="ESP32 Serial Port:", font=("Helvetica", 12)).pack(pady=5, anchor="w")
        self.port_entry = ttk.Entry(main_frame, font=("Helvetica", 12), width=50)
        self.port_entry.insert(0, DEFAULT_PORT)
        self.port_entry.pack(pady=5, fill=tk.X)

        self.run_button = ttk.Button(main_frame, text="Start Full Provisioning Process", command=self.run_provisioning_workflow, style="Accent.TButton")
        self.run_button.pack(pady=20, fill=tk.X, ipady=10)
        self.style.configure("Accent.TButton", font=("Helvetica", 14, "bold"), foreground="white", background="#007bff")

        ttk.Separator(main_frame, orient="horizontal").pack(pady=10, fill=tk.X)

        ttk.Label(main_frame, text="Process Log:", font=("Helvetica", 12)).pack(pady=5, anchor="w")
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, font=("Courier", 10))
        self.log_text.pack(pady=5, fill=tk.BOTH, expand=True)

        self.label_frame = ttk.LabelFrame(main_frame, text="Generated Label Info", padding="10")
        self.label_frame.pack(pady=10, fill=tk.X)
        self.qr_code_label = ttk.Label(self.label_frame)
        self.qr_code_label.pack(pady=10)
        self.human_readable_id_label = ttk.Label(self.label_frame, text="Human-Readable ID: -", font=("Courier", 14, "bold"))
        self.human_readable_id_label.pack(pady=5)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run_provisioning_workflow(self):
        self.run_button.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        port = self.port_entry.get()

        if not port:
            messagebox.showerror("Error", "Serial port cannot be empty.")
            self.run_button.config(state=tk.NORMAL)
            return

        try:
            self.log(">>> [STEP 1/5] Flashing Firmware...")
            self.flash_firmware(port)
            self.log("SUCCESS: Firmware flash complete.")

            self.log("\n>>> [STEP 2/5] Reading MAC Address...")
            mac_address = self.get_mac_address(port)

            self.log(f"\n>>> [STEP 3/5] Hashing Device ID from MAC ({mac_address})...")
            device_id_hash = self.hash_id(mac_address)

            self.log(f"\n>>> [STEP 4/5] Pre-registering Device in Database...")
            if self.pre_register_device_in_db(device_id_hash):
                self.log(f"\n>>> [STEP 5/5] Generating Label Info...")
                self.generate_label_info(device_id_hash)
            else:
                raise RuntimeError("Could not pre-register device. Aborting.")

            messagebox.showinfo("Success", "Device provisioning completed successfully!")

        except Exception as e:
            self.log(f"\n---!!!-!!!---\nERROR: {e}\n---!!!-!!!---")
            messagebox.showerror("Provisioning Failed", f"An error occurred: {e}")
        finally:
            self.run_button.config(state=tk.NORMAL)

    def flash_firmware(self, port):
        firmware_bin = "build/firmware.bin"
        if not os.path.exists(firmware_bin):
            raise RuntimeError("Firmware binary not found. Build it first.")
        cmd = [
            "esptool.py", "--chip", "esp32s3", "--port", port, "--baud", "460800", "write_flash",
            "0x0", "build/bootloader/bootloader.bin",
            "0x8000", "build/partition_table/partition-table.bin",
            "0x10000", firmware_bin
        ]
        subprocess.run(cmd, check=True, timeout=60)

    def get_mac_address(self, port):
        cmd = ["esptool.py", "--port", port, "read_mac"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        for line in result.stdout.splitlines():
            if "MAC:" in line:
                mac = line.split("MAC:")[1].strip()
                self.log(f"SUCCESS: Found MAC Address: {mac}")
                return mac
        raise RuntimeError("MAC address not found.")

    def hash_id(self, input_string):
        sha256 = hashlib.sha256(input_string.encode("utf-8")).hexdigest()
        self.log(f"SUCCESS: Hashed to {sha256[:20]}...")
        return sha256

    def pre_register_device_in_db(self, device_id):
        url = f"{API_SERVER_URL}/api/factory/provision"
        headers = {"Content-Type": "application/json", "x-factory-api-key": FACTORY_API_KEY}
        payload = {"mac_hash": device_id}

        response = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
        self.log(f"API Response Status: {response.status_code}")
        response.raise_for_status()
        self.log(f"SUCCESS: {response.json().get('message')}")
        return True

    def get_next_unit_number(self):
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE) as f:
                count = int(f.read().strip()) + 1
        else:
            count = 1
        with open(COUNTER_FILE, "w") as f:
            f.write(str(count))
        return f"{count:03}"

    def generate_label_info(self, full_hash):
        short_id = f"{full_hash[:4].upper()}-{full_hash[4:8].upper()}"
        self.human_readable_id_label.config(text=f"Human-Readable ID: {short_id}")

        qr_img = self._create_qr_image(full_hash)
        labeled_img = self._add_text_below_image(qr_img, short_id)

        unit_num = self.get_next_unit_number()
        base_path = os.path.join(LABEL_DIR, f"device_{unit_num}_{short_id}")
        self._save_qr_assets(labeled_img, base_path, full_hash, short_id)

        if platform.system() == "Darwin":
            self._attempt_print(f"{base_path}.png")
        else:
            self.log("INFO: Auto-printing only supported on macOS")

        self.qr_photo_image = ImageTk.PhotoImage(labeled_img)
        self.qr_code_label.config(image=self.qr_photo_image)
        self.log("SUCCESS: Label info generated and saved.")

    def _create_qr_image(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=2
        )
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert('RGB')

    def _add_text_below_image(self, image, text):
        width, height = image.size
        font_size = 16
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        new_image = Image.new("RGB", (width, height + text_height + 10), "white")
        new_image.paste(image, (0, 0))
        draw = ImageDraw.Draw(new_image)
        draw.text(((width - text_width) / 2, height + 5), text, fill="black", font=font)
        return new_image

    def _save_qr_assets(self, img, base_path, full_hash, short_id):
        img.save(f"{base_path}.png")
        with open(f"{base_path}.txt", "w") as f:
            f.write(f"MAC Hash: {full_hash}\n")
            f.write(f"Human-Readable ID: {short_id}\n")

    def _attempt_print(self, img_path):
        try:
            subprocess.run(["lp", img_path], check=True)
            self.log(f"SUCCESS: Printed label: {img_path}")
        except subprocess.CalledProcessError as e:
            self.log(f"WARNING: Print failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FactoryProvisioningApp(root)
    root.mainloop()
