#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
"""
 * File: factory-tool-v1.2.py
 * Description: PianoGuard DCM-1 base firmware and cert flasher.
 * Created on: 2025-07-25
 * Edited on: 2025-07-27
 * Version: v1.2.0
 * Author: R. Andrew Ballard (c) 2025 "Andwardo"
 * Fixes MAC extraction from espefuse.py summary output
"""

import subprocess
import os
import re
import sys

PORT = os.environ.get("ESPPORT", "/dev/cu.usbmodem101")
IDF_ENV = "~/.espressif/python_env/idf4.4_py3.9_env/bin/python"
ESPIDF = "~/esp-idf-v4.4.4/components/esptool_py/esptool/esptool.py"
MK_SPIFFS = "~/mkspiffs/bin/mkspiffs"
BUILD_DIR = "./build"
SPIFFS_IMAGE_DIR = "./spiffs_image"
SPIFFS_BIN = "./spiffs.bin"
APP_BIN = os.path.join(BUILD_DIR, "PianoGuard_DCM-1.bin")
PART_TABLE = os.path.join(BUILD_DIR, "partition_table/partition-table.bin")

def run(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def build_project():
    run("idf.py build")

def make_spiffs():
    run(f"{MK_SPIFFS} -c {SPIFFS_IMAGE_DIR} -b 4096 -p 256 -s 0x80000 {SPIFFS_BIN}")

def flash_certs():
    run(f"esptool.py --port {PORT} write_flash 0x180000 {SPIFFS_BIN}")

def flash_all():
    cmd = (
        f"{IDF_ENV} {ESPIDF} "
        f"--chip esp32s3 --port {PORT} --baud 460800 "
        f"write_flash --flash_mode dio --flash_size detect --flash_freq 80m "
        f"0x8000 {PART_TABLE} "
        f"0xa0000 {APP_BIN} "
        f"0x12000 {SPIFFS_BIN}"
    )
    run(cmd)

def read_mac(port):
    try:
        result = subprocess.run(
            ["espefuse.py", "-p", port, "summary"],
            capture_output=True,
            text=True,
            check=True
        )
        match = re.search(r"MAC \(BLOCK1\).*=\s+([0-9a-f:]{17})", result.stdout, re.IGNORECASE)
        if match:
            mac = match.group(1)
            print(f"MAC Address: {mac}")
            return mac
    except subprocess.CalledProcessError as e:
        print("Failed to read MAC:", e)
    raise RuntimeError("MAC address not found")

def main():
    print(f"Using port: {PORT}")
    build_project()
    make_spiffs()
    flash_certs()
    flash_all()
    mac = read_mac(PORT)
    print(f"Device MAC: {mac}")

if __name__ == "__main__":
    main()
