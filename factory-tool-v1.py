#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
#
# factory-tool-v1.py
#
# Created on: 2025-07-29
# Edited on: 2025-07-29
#     Author: Andwardo
#     Version: v1.1.1
#
# v1.1.1 - Integrated full ESP32 flash and spiffs sequence into factory app logic
#

import subprocess
import os
import sys

DEFAULT_PORT = "/dev/cu.usbmodem101"
MK_SPIFFS = os.path.expanduser("~/mkspiffs/bin/mkspiffs")
ESPTOOL = os.path.expanduser("~/.espressif/python_env/idf4.4_py3.9_env/bin/python") +           " " + os.path.expanduser("~/esp-idf-v4.4.4/components/esptool_py/esptool/esptool.py")

def run(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def build_project():
    run("idf.py build")

def create_spiffs():
    run(f"{MK_SPIFFS} -c ./spiffs_image -b 4096 -p 256 -s 0x80000 ./spiffs.bin")

def flash_certs(port):
    run(f"esptool.py --port {port} write_flash 0x180000 spiffs.bin")

def flash_all(port):
    run(f"{ESPTOOL} --chip esp32s3 --port {port} --baud 460800 "
        "write_flash --flash_mode dio --flash_size detect --flash_freq 80m "
        "0x8000 build/partition_table/partition-table.bin "
        "0xa0000 build/PianoGuard_DCM-1.bin "
        "0x12000 spiffs.bin")

def flash_app_only(port):
    run(f"esptool.py --chip esp32s3 --port {port} --baud 921600 "
        "write_flash 0x10000 build/PianoGuard_DCM-1.bin")

def read_mac(port):
    run(f"espefuse.py -p {port} summary")

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PORT
    print(f"Using port: {port}")

    build_project()
    create_spiffs()
    flash_certs(port)
    flash_all(port)
    read_mac(port)

if __name__ == "__main__":
    main()
