"""
factory_app.py

Created on: 2025-06-25
Edited on: 2025-07-25
Version: v1.0.3
Author: R. Andrew Ballard (c) 2025 "Andwardo"
Now prints both QR code and text label with human-readable ID to printer
"""

import os
import tkinter as tk
from tkinter import messagebox
import requests
import qrcode
import hashlib
import subprocess

from dotenv import load_dotenv
load_dotenv()

FACTORY_KEY = os.getenv("PIANOGUARD_FACTORY_KEY")
API_URL = "https://dev1.pgapi.net/register-device"


def get_mac_address():
    cmd = "system_profiler SPHardwareDataType | awk '/MAC Address/ { print $3 }'"
    mac = subprocess.check_output(cmd, shell=True).decode().strip()
    return mac


def generate_device_id(mac_address):
    return hashlib.sha256(mac_address.encode()).hexdigest().upper()[:16]


def register_device(serial):
    payload = {
        "factory_key": FACTORY_KEY,
        "serial": serial
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

    except requests.exceptions.HTTPError as err:
        try:
            return {"error": response.json()}
        except Exception:
            return {"error": str(err)}


def print_assets(device_id, mac_address):
    short_id = device_id[-6:]

    qr = qrcode.make(device_id)
    qr_path = f"{device_id}.png"
    qr.save(qr_path)

    label_path = f"{device_id}_label.txt"
    with open(label_path, "w") as f:
        f.write("PianoGuard Device\n")
        f.write(f"ID: {short_id}\n")
        f.write(f"MAC: {mac_address}\n")

    subprocess.run(["lp", qr_path])
    subprocess.run(["lp", label_path])


def main():
    mac = get_mac_address()
    device_id = generate_device_id(mac)

    print(f"Firmware flashed.\nMAC Address: {mac}\nDevice ID: {device_id}")

    result = register_device(device_id)

    print("---!!!-!!!---")
    print("RESPONSE:", result)
    print("---!!!-!!!---")

    root = tk.Tk()
    root.withdraw()

    if "status" in result and result["status"] == "ok":
        print_assets(device_id, mac)
        messagebox.showinfo("Success", f"Device {device_id[-6:]} registered and printed.")
    else:
        messagebox.showerror("Error", f"API error: {result}")


if __name__ == "__main__":
    main()