#!/usr/bin/env python3

/**
 * File: factory-tool-v1.3.py
 * Description: Flash ESP32, write certs, and extract MAC for factory registration.
 * Created on: 2025-07-25
 * Edited on: 2025-07-27
 * Version: v1.3
 * Author: R. Andrew Ballard (c) 2025 "Andwardo"
 * Added regex-based MAC address extraction fix for espefuse.py output
 **/

import subprocess
import os
import sys
import re

PORT = os.environ.get("ESPPORT", "/dev/cu.usbmodem101")

def run(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def build_project():
    run("idf.py build")

def create_spiffs():
    run("~/mkspiffs/bin/mkspiffs -c ./spiffs_image -b 4096 -p 256 -s 0x80000 ./spiffs.bin")

def flash_spiffs():
    run(f"esptool.py --port {PORT} write_flash 0x180000 spiffs.bin")

def flash_all():
    run(f"/Users/andrewballard/.espressif/python_env/idf4.4_py3.9_env/bin/python /Users/andrewballard/esp-idf-v4.4.4/components/esptool_py/esptool/esptool.py "
        f"--chip esp32s3 --port {PORT} --baud 460800 write_flash --flash_mode dio --flash_size detect --flash_freq 80m "
        f"0x8000 build/partition_table/partition-table.bin "
        f"0xa0000 build/PianoGuard_DCM-1.bin "
        f"0x12000 spiffs.bin")

def read_mac(port):
    output = subprocess.check_output(
        f"espefuse.py -p {port} summary",
        shell=True,
        text=True
    )
    match = re.search(r'MAC \(BLOCK1\).*?([0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}}:[0-9a-f]{{2}})', output, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).lower()
    raise RuntimeError("MAC address not found")

def main():
    print(f"Using port: {PORT}")
    build_project()
    create_spiffs()
    flash_spiffs()
    flash_all()
    mac = read_mac(PORT)
    print(f"✅ MAC Address: {mac}")

if __name__ == "__main__":
    main()
