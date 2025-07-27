/**
 * File: factory_tool.py
 * Description: Factory tool for provisioning PianoGuard DCM-1 devices.
 * Created on: 2025-07-25
 * Edited on:  2025-07-27
 * Version: v1.0.1
 * Author: R. Andrew Ballard (c) 2025 "Andwardo"
 * Automates: ESP32 provisioning, TLS cert retrieval, SPIFFS generation, flashing, device registration, label printing.
 **/

import os
import json
import time
import serial.tools.list_ports
import requests
import qrcode
import sqlite3
import subprocess
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
from escpos.printer import Usb

load_dotenv()

# Configuration
FACTORY_KEY = os.getenv("PIANOGUARD_FACTORY_KEY")
REGISTER_ENDPOINT = "https://dev1.pgapi.net/register-device"
CERT_API = "https://dev1.pgapi.net/generate-cert"
DB_PATH = "./factory_log.db"
PARTITION_DIR = "./partitions"
SPIFFS_DIR = "./spiffs"
SERIAL_PORT = None  # Auto-detected
ESPTOOL_PY = "esptool.py"
LABEL_PRINTER = Usb(0x04b8, 0x0e15)  # Example Epson config

def detect_device_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "USB" in p.device or "tty" in p.device:
            return p.device
    raise RuntimeError("ESP32 device not found.")

def request_cert(device_id):
    resp = requests.post(CERT_API, json={"device_id": device_id, "factory_key": FACTORY_KEY})
    resp.raise_for_status()
    return resp.json()

def create_spiffs(cert_data):
    os.makedirs(SPIFFS_DIR, exist_ok=True)
    with open(os.path.join(SPIFFS_DIR, "client.crt"), "w") as f:
        f.write(cert_data["cert"])
    with open(os.path.join(SPIFFS_DIR, "client.key"), "w") as f:
        f.write(cert_data["key"])
    with open(os.path.join(SPIFFS_DIR, "root_ca.pem"), "w") as f:
        f.write(cert_data["ca"])
    subprocess.run([
        "python3", "mkspiffs.py",
        "-c", SPIFFS_DIR,
        "-b", "4096", "-p", "256", "-s", "0x100000",
        os.path.join(PARTITION_DIR, "spiffs.bin")
    ], check=True)

def flash_device(serial_port, device_id):
    bin_paths = {
        "bootloader": os.path.join(PARTITION_DIR, "bootloader.bin"),
        "partition": os.path.join(PARTITION_DIR, "partition-table.bin"),
        "app": os.path.join(PARTITION_DIR, "app.bin"),
        "spiffs": os.path.join(PARTITION_DIR, "spiffs.bin")
    }
    flash_cmd = [
        ESPTOOL_PY, "--chip", "esp32", "--port", serial_port, "--baud", "460800", "write_flash",
        "-z", "0x1000", bin_paths["bootloader"],
        "0x8000", bin_paths["partition"],
        "0x10000", bin_paths["app"],
        "0x290000", bin_paths["spiffs"]
    ]
    subprocess.run(flash_cmd, check=True)

def register_device(device_id, serial):
    resp = requests.post(REGISTER_ENDPOINT, json={"factory_key": FACTORY_KEY, "serial": serial})
    resp.raise_for_status()
    return resp.json()

def log_to_db(device_id, serial):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS devices (device_id TEXT, serial TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO devices (device_id, serial) VALUES (?, ?)", (device_id, serial))
    conn.commit()
    conn.close()

def print_label(device_id, serial):
    qr = qrcode.make(serial)
    qr_path = f"/tmp/{serial}.png"
    qr.save(qr_path)
    LABEL_PRINTER.image(qr_path)
    LABEL_PRINTER.text(f"Serial: {serial}\nDevice: {device_id}\n")
    LABEL_PRINTER.cut()

def main():
    root = tk.Tk()
    root.withdraw()
    serial_port = detect_device_port()
    messagebox.showinfo("DCM-1 Factory", "ESP32 detected. Provisioning...")

    device_id = input("Enter Device ID: ").strip()
    serial_num = input("Enter Human Serial Number: ").strip()

    try:
        certs = request_cert(device_id)
        create_spiffs(certs)
        flash_device(serial_port, device_id)
        register_device(device_id, serial_num)
        log_to_db(device_id, serial_num)
        print_label(device_id, serial_num)
        messagebox.showinfo("Success", "Device provisioned and registered.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        raise

if __name__ == "__main__":
    main()
