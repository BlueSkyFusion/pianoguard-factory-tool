#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3

import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import requests
import qrcode
import json
import time

API_SERVER_URL = "https://pgapi.net/api/factory/provision"
FACTORY_API_KEY = os.environ.get("PIANOGUARD_FACTORY_KEY", "your_super_secret_factory_key")

def flash_firmware(port):
    print(">>> [STEP 1/5] Flashing Firmware...")
    firmware_path = "firmware/firmware.bin"
    if not os.path.exists(firmware_path):
        raise FileNotFoundError("Firmware binary not found. Build it first.")

    cmd = [
        "esptool.py",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", "460800",
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash", "-z", "0x1000",
        firmware_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("Firmware flashing failed.")
    print("SUCCESS: Firmware flash complete.")

# ... rest of the original code (unchanged)