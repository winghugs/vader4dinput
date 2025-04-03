#!/usr/bin/env python3
import uinput
import time
import os
import re

# Device identification
vendor_id = "04b4"
product_id = "2412"
hid_phys_target = "usb-0000:0b:00.3-3.3.1.2/input2"

# Function to find the hidraw device
def find_hidraw_device():
    for device in os.listdir("/dev"):
        if device.startswith("hidraw"):
            try:
                with open(f"/sys/class/hidraw/{device}/device/uevent", "r") as uevent_file:
                    uevent_content = uevent_file.read()
                    hid_id_match = re.search(r"HID_ID=0003:0000([0-9A-Fa-f]{4}):0000([0-9A-Fa-f]{4})", uevent_content)
                    hid_phys_match = re.search(r"HID_PHYS=(.+)", uevent_content)

                    if hid_id_match and hid_phys_match:
                        device_vendor = hid_id_match.group(1).lower()
                        device_product = hid_id_match.group(2).lower()
                        device_hid_phys = hid_phys_match.group(1)

                        if device_vendor == vendor_id.lower() and device_product == product_id.lower() and device_hid_phys == hid_phys_target:
                            return f"/dev/{device}"

            except FileNotFoundError:
                pass
    return None

# uinput setup
try:
    events = (
        uinput.BTN_SOUTH, uinput.BTN_EAST, uinput.BTN_NORTH, uinput.BTN_WEST,
        uinput.BTN_TL, uinput.BTN_TR, uinput.BTN_TL2, uinput.BTN_TR2,
        uinput.BTN_SELECT, uinput.BTN_START, uinput.BTN_MODE,
        uinput.BTN_DPAD_UP, uinput.BTN_DPAD_DOWN, uinput.BTN_DPAD_LEFT, uinput.BTN_DPAD_RIGHT,
        uinput.ABS_X + (-127, 127, 0, 127), uinput.ABS_Y + (-127, 127, 0, 127),
        uinput.ABS_RX + (-127, 127, 0, 127), uinput.ABS_RY + (-127, 127, 0, 127),
        uinput.ABS_Z + (0, 255, 0, 0), uinput.ABS_RZ + (0, 255, 0, 0),
        uinput.BTN_TRIGGER_HAPPY1, uinput.BTN_TRIGGER_HAPPY2, uinput.BTN_TRIGGER_HAPPY3, uinput.BTN_TRIGGER_HAPPY4,
        uinput.BTN_TRIGGER_HAPPY5, uinput.BTN_TRIGGER_HAPPY6, uinput.BTN_TRIGGER_HAPPY7,
        uinput.BTN_THUMBL, uinput.BTN_THUMBR
    )
    device = uinput.Device(events, name="Vader4Pro DInput")
    print("uinput device created successfully.")
except Exception as e:
    print(f"Error creating uinput device: {e}")
    exit(1)

# Button field processing
def process_button_field(value, button_map):
    for button, button_value in button_map.items():
        if value & button_value:
            device.emit(button, 1)
        else:
            device.emit(button, 0)

# Main loop
try:
    hidraw_path = find_hidraw_device()
    print(f"Hidraw path: {hidraw_path}")
    hidraw_file = open(hidraw_path, "rb")
    print(f"hidraw file opened: {hidraw_file}")

    while True:
        try:
            data = hidraw_file.read(64)
            if len(data) != 64:
                continue

            # Isolate button data
            button_data_7 = data[7]
            button_data_8 = data[8]
            button_data_9 = data[9]
            button_data_10 = data[10]

            # Button fields (Corrected button mappings)
            process_button_field(button_data_7, {uinput.BTN_TRIGGER_HAPPY5: 1, uinput.BTN_TRIGGER_HAPPY6: 2, uinput.BTN_TRIGGER_HAPPY1: 8, uinput.BTN_TRIGGER_HAPPY2: 32, uinput.BTN_TRIGGER_HAPPY4: 16, uinput.BTN_TRIGGER_HAPPY3: 4})
            process_button_field(button_data_8, {uinput.BTN_TRIGGER_HAPPY7: 1, uinput.BTN_MODE: 8})
            process_button_field(button_data_9, {uinput.BTN_EAST: 32, uinput.BTN_SOUTH: 16, uinput.BTN_WEST: 128, uinput.BTN_SELECT: 64, uinput.BTN_DPAD_UP: 1, uinput.BTN_DPAD_RIGHT: 2, uinput.BTN_DPAD_DOWN: 4, uinput.BTN_DPAD_LEFT: 8})
            process_button_field(button_data_10, {uinput.BTN_START: 2, uinput.BTN_NORTH: 1, uinput.BTN_TL: 4, uinput.BTN_TR: 8, uinput.BTN_TL2: 16, uinput.BTN_TR2: 32, uinput.BTN_THUMBL: 64, uinput.BTN_THUMBR: 128})

            # Axis and motion controls
            device.emit(uinput.ABS_X, data[17] - 127)
            device.emit(uinput.ABS_Y, data[19] - 127)
            device.emit(uinput.ABS_RX, data[21] - 127)
            device.emit(uinput.ABS_RY, data[22] - 127)
            device.emit(uinput.ABS_Z, data[23])
            device.emit(uinput.ABS_RZ, data[24])

            device.syn()

        except FileNotFoundError:
            print(f"Error: {hidraw_path} not found.")
            break
        except KeyboardInterrupt:
            print("Closing hidraw file")
            if 'hidraw_file' in locals():
                hidraw_file.close()
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

except Exception as e:
    print(f"An unexpected error occurred outside the while loop: {e}")
