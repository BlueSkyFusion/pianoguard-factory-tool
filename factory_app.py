# factory_app.py
import subprocess
import hashlib
import requests
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import qrcode
from PIL import Image, ImageTk

# --- Configuration ---
API_SERVER_URL = "http://45.56.69.50:3001"
# IMPORTANT: The API key should be set as an environment variable on the factory PC.
# Fallback to a default key for development purposes ONLY.
FACTORY_API_KEY = os.environ.get("PIANOGUARD_FACTORY_KEY", "your_super_secret_factory_key")

class FactoryProvisioningApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PianoGuard Factory Provisioning Tool v1.0")
        self.root.geometry("600x700")

        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="ESP32 Serial Port:", font=("Helvetica", 12)).pack(pady=5, anchor="w")
        self.port_entry = ttk.Entry(main_frame, font=("Helvetica", 12), width=50)
        # Default port for macOS. Factory PC would likely use a COM port.
        self.port_entry.insert(0, "/dev/tty.SLAB_USBtoUART") 
        self.port_entry.pack(pady=5, fill=tk.X)

        self.run_button = ttk.Button(main_frame, text="Start Full Provisioning Process", command=self.run_provisioning_workflow, style="Accent.TButton")
        self.run_button.pack(pady=20, fill=tk.X, ipady=10)
        self.style.configure("Accent.TButton", font=("Helvetica", 14, "bold"), foreground="white", background="#007bff")

        ttk.Separator(main_frame, orient="horizontal").pack(pady=10, fill=tk.X)

        ttk.Label(main_frame, text="Process Log:", font=("Helvetica", 12)).pack(pady=5, anchor="w")
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, font=("Courier", 10))
        self.log_text.pack(pady=5, fill=tk.BOTH, expand=True)

        self.label_frame = ttk.LabelFrame(main_frame, text="Generated Label Info", padding="10")
        self.label_frame.pack(pady=10, fill=tk.X)
        self.qr_code_label = ttk.Label(self.label_frame)
        self.qr_code_label.pack(pady=10)
        self.human_readable_id_label = ttk.Label(self.label_frame, text="Human-Readable ID: -", font=("Courier", 14, "bold"))
        self.human_readable_id_label.pack(pady=5)


    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run_provisioning_workflow(self):
        self.run_button.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END) # Clear log
        port = self.port_entry.get()

        if not port:
            messagebox.showerror("Error", "Serial port cannot be empty.")
            self.run_button.config(state=tk.NORMAL)
            return

        try:
            self.log(">>> [STEP 1/5] Flashing Firmware...")
            # self.flash_firmware(port) # Uncomment when ready
            self.log("SUCCESS: Firmware flash complete (simulated).")

            self.log("\n>>> [STEP 2/5] Reading MAC Address...")
            mac_address = self.get_mac_address(port)

            self.log(f"\n>>> [STEP 3/5] Hashing Device ID from MAC ({mac_address})...")
            device_id_hash = self.hash_id(mac_address)

            self.log(f"\n>>> [STEP 4/5] Pre-registering Device in Database...")
            if self.pre_register_device_in_db(device_id_hash):
                self.log(f"\n>>> [STEP 5/5] Generating Label Info...")
                self.generate_label_info(device_id_hash)
            else:
                raise RuntimeError("Could not pre-register device. Aborting.")

            messagebox.showinfo("Success", "Device provisioning completed successfully!")

        except Exception as e:
            self.log(f"\n---!!!-!!!---\nERROR: {e}\n---!!!-!!!---")
            messagebox.showerror("Provisioning Failed", f"An error occurred: {e}")
        finally:
            self.run_button.config(state=tk.NORMAL)

    def get_mac_address(self, port):
        try:
            command = ["esptool.py", "--port", port, "read_mac"]
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
            for line in result.stdout.splitlines():
                if "MAC:" in line:
                    mac = line.split("MAC:")[1].strip()
                    self.log(f"SUCCESS: Found MAC Address: {mac}")
                    return mac
            raise RuntimeError("Could not find MAC address in esptool.py output.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("esptool.py timed out. Check connection.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"esptool.py failed. Is device on {port}?\nError: {e.stderr}")

    def hash_id(self, input_string):
        sha256 = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
        self.log(f"SUCCESS: Hashed to {sha256[:20]}...")
        return sha256

    def pre_register_device_in_db(self, device_id):
        url = f"{API_SERVER_URL}/api/factory/provision"
        headers = {"Content-Type": "application/json", "x-factory-api-key": FACTORY_API_KEY}
        payload = {"device_id": device_id}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            self.log(f"API Response Status: {response.status_code}")
            response.raise_for_status()
            self.log(f"SUCCESS: API call successful. {response.json().get('message')}")
            return True
        except requests.exceptions.RequestException as e:
            error_text = str(e)
            if e.response is not None:
                error_text += f"\nResponse Body: {e.response.text}"
            raise RuntimeError(f"API call failed: {error_text}")

    def generate_label_info(self, full_hash):
        short_id = f"{full_hash[0:4].upper()}-{full_hash[4:8].upper()}"
        self.human_readable_id_label.config(text=f"Human-Readable ID: {short_id}")

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=2)
        qr.add_data(full_hash)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        self.qr_photo_image = ImageTk.PhotoImage(img)
        self.qr_code_label.config(image=self.qr_photo_image)
        self.log("SUCCESS: Label info generated.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FactoryProvisioningApp(root)
    root.mainloop()
