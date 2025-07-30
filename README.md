# PianoGuard DCM-1 Factory Setup Instructions

## Required Tools

- Mac with ESP-IDF v4.4.4 set up
- USB-C cable for ESP32-S3-WROOM connection
- This repo checked out locally
- Environment variable: `PIANOGUARD_FACTORY_KEY`

## Step-by-Step Setup

### 1. Connect ESP32

Plug in the ESP32-S3. It should appear as `/dev/cu.usbmodem101` or similar.

### 2. Set Factory Key

Export the factory key if not already in shell:

```bash
export PIANOGUARD_FACTORY_KEY=DEVKEY123
```

### 3. Flash Device via Factory App

Run from ESP-IDF project root:

```bash
~/Projects/pianoguard-factory-tool/factory_app.py
```

This will:
- Build firmware
- Generate spiffs from `spiffs_image/`
- Flash all partitions (bootloader, partition table, app, spiffs)
- Read MAC address via efuse
- Register device with backend

### 4. Verify Registration

Console should end with:

```
✅ Factory flash and registration complete
```

Backend will log the device ID based on MAC. You can cross-reference via:

```bash
curl https://dev1.pgapi.net/devices
```

### 5. Apply Labels

Print and apply the label with the device’s MAC or serial number.

## Done

The device will boot into captive portal mode and wait for user Wi-Fi provisioning.

