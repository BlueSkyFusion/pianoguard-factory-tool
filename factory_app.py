#!/usr/bin/env python3
"""
 * File: factory_app.py
 * Description: PianoGuard factory flashing and registration utility.
 * Created on: 2025-07-25
 * Edited on: 2025-07-27
 * Version: v1.4
 * Author: R. Andrew Ballard (c) 2025 "Andwardo"
 * Summarize the edits in this version
 * - Added .env support using python-dotenv to load PIANOGUARD_FACTORY_KEY
"""

import os
import subprocess
import re
import requests
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

PORT = "/dev/cu.usbmodem101"
SERIAL_NUMBER = "TEST123"
FACTORY_KEY = os.getenv("PIANOGUARD_FACTORY_KEY", "DEVKEY123")
FLASH_CMD = f"""
~/.espressif/python_env/idf4.4_py3.9_env/bin/python ~/esp-idf-v4.4.4/components/esptool_py/esptool/esptool.py \\
  --chip esp32s3 --port {PORT} --baud 460800 \\
  write_flash --flash_mode dio --flash_size detect --flash_freq 80m \\
  0x0 build/bootloader/bootloader.bin \\
  0x8000 build/partition_table/partition-table.bin \\
  0xf000 build/ota_data_initial.bin \\
  0xa0000 build/PianoGuard_DCM-1.bin
"""

SPIFFS_CMD = f"esptool.py --port {PORT} write_flash 0x12000 spiffs.bin"

def run(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def build_project():
    run("idf.py build")

def make_spiffs():
    run("~/mkspiffs/bin/mkspiffs -c ./spiffs_image -b 4096 -p 256 -s 0x80000 ./spiffs.bin")

def flash_firmware():
    run(FLASH_CMD)

def flash_spiffs():
    run(SPIFFS_CMD)

def read_mac(port):
    print(f"Reading MAC address on {port}")
    output = subprocess.check_output(["espefuse.py", "-p", port, "summary"], text=True)
    match = re.search(r"MAC \(BLOCK1\)\s+Factory MAC Address\s+= ([0-9a-f:]+)", output, re.IGNORECASE)
    if match:
        return match.group(1).replace(":", "").upper()
    raise RuntimeError("MAC address not found")

def register_device(mac, serial):
    print(f"Registering device with MAC={mac}")
    payload = {
        "factory_key": FACTORY_KEY,
        "serial": serial,
        "mac": mac
    }
    resp = requests.post("https://dev1.pgapi.net/register-device", json=payload)
    print(resp.text)
    if not resp.ok:
        raise RuntimeError("Registration failed")

def main():
    print(f"Using port: {PORT}")
    build_project()
    make_spiffs()
    flash_firmware()
    flash_spiffs()
    mac = read_mac(PORT)
    register_device(mac, SERIAL_NUMBER)
    print("✅ Factory flash and registration complete")

if __name__ == "__main__":
    main()