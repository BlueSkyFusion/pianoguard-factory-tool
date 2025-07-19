# headless_test.py
from factory_app import FactoryProvisioningApp
import tkinter as tk

class DummyRoot:
    def update_idletasks(self): pass
    def title(self, x): pass
    def geometry(self, x): pass

app = FactoryProvisioningApp(DummyRoot())

port = "/dev/cu.usbmodem101"  # or whatever your working port is

print("Running provisioning workflow on:", port)
app.log = print  # redirect log output to terminal

app.get_mac_address(port)
