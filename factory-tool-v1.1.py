#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
#
# factory-tool-v1.1.py
#
# Created on: 2025-07-27
# Edited on: 2025-07-27
#     Author: R. Andrew Ballard (c) 2025 "Andwardo"
#     Version: v1.1.1
# Adds response confirmation and error reporting for factory registration
#

import os
import subprocess
import sys
import json
import requests

DEFAULT_PORT = "/dev/cu.usbmodem101"
API_URL = "https://dev1.pgapi.net/api/factory/provision"
FACTORY_KEY = os.environ.get("PIANOGUARD_FACTORY_KEY")

def run(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def build_project():
    run("idf.py build")

def create_spiffs():
    run("~/mkspiffs/bin/mkspiffs -c ./spiffs_image -b 4096 -p 256 -s 0x80000 ./spiffs.bin")

def flash_spiffs(port):
    run(f"esptool.py --port {port} write_flash 0x180000 spiffs.bin")

def flash_all(port):
    run(f"""~/.espressif/python_env/idf4.4_py3.9_env/bin/python ~/esp-idf-v4.4.4/components/esptool_py/esptool/esptool.py \
  --chip esp32s3 --port {port} --baud 460800 \
  write_flash --flash_mode dio --flash_size detect --flash_freq 80m \
  0x8000   build/partition_table/partition-table.bin \
  0xa0000  build/PianoGuard_DCM-1.bin \
  0x12000  spiffs.bin""")

def read_mac(port):
    result = subprocess.run(f"espefuse.py -p {port} summary", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = result.stdout
    for line in output.splitlines():
        if "Factory MAC Address" in line or "MAC (BLOCK1)" in line:
            parts = line.split("=")
            if len(parts) >= 2:
                mac = parts[1].strip().split(" ")[0]
                print(f"MAC Address: {mac}")
                return mac
    raise RuntimeError("MAC address not found")

def hash_mac(mac):
    import hashlib
    return hashlib.sha256(mac.encode("utf-8")).hexdigest()

def post_to_server(mac_hash):
    if not FACTORY_KEY:
        print("ERROR: PIANOGUARD_FACTORY_KEY not set in environment.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "x-factory-api-key": FACTORY_KEY
    }
    payload = {
        "mac_hash": mac_hash
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            print(f"\n---!!!-!!!---\nRESPONSE: {json.dumps(data)}\n---!!!-!!!---")
        else:
            print(f"ERROR: API responded with: {data}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request failed: {e}")
        sys.exit(1)

def main():
    port = os.environ.get("ESPPORT", DEFAULT_PORT)
    print(f"Using port: {port}")
    build_project()
    create_spiffs()
    flash_spiffs(port)
    flash_all(port)
    mac = read_mac(port)
    mac_hash = hash_mac(mac)
    post_to_server(mac_hash)

if __name__ == "__main__":
    main()
