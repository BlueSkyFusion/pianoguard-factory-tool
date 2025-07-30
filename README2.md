# PianoGuard Factory Provisioning Tool

This GUI tool is used in the factory to flash, hash, and register DCM-1 units for PianoGuard.

## ✅ Current Status

- [x] GUI launches successfully under Python 3.11 + Tkinter 8.6
- [x] Device MAC address read and hashed to ID
- [x] Flashing simulated (replace with esptool ops)
- [x] Label display and output placeholder active
- [ ] Backend `/api/factory/provision` POST endpoint not responding (404) – needs dev1 backend fix

## 🖥️ Requirements

- Python 3.11.9 (do **not** use 3.10.x)
- Tkinter (8.6 or newer)
- pip packages: `requests`, `pillow`, `qrcode`, `esptool`

## 🧪 Tested On

- macOS Sonoma on Apple Silicon (M1)
- Python installed from [official installer](https://www.python.org)
- Tk 8.6.13 manually validated

## 🛠️ Local Setup

```bash
cd pianoguard-factory-tool
python3.11 -m venv venv
source venv/bin/activate
pip install requests pillow qrcode esptool
python factory_app.py

