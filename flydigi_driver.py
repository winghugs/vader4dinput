#!/usr/bin/env python3
import uinput
import time
import os
import re
import subprocess

# device id stuff
vendorId = "04b4"
productId = "2412"
hidPhysTargetRegex = r".*input2$"

# finding the hidraw device to read from
def findHidrawDevice():
    for device in os.listdir("/dev"):
        if device.startswith("hidraw"):
            try:
                with open(f"/sys/class/hidraw/{device}/device/uevent", "r") as ueventFile:
                    ueventContent = ueventFile.read()
                    hidIdMatch = re.search(r"HID_ID=0003:0000([0-9A-Fa-f]{4}):0000([0-9A-Fa-f]{4})", ueventContent)
                    hidPhysMatch = re.search(r"HID_PHYS=(.+)", ueventContent)

                    if hidIdMatch and hidPhysMatch:
                        deviceVendor = hidIdMatch.group(1).lower()
                        deviceProduct = hidIdMatch.group(2).lower()
                        deviceHidPhys = hidPhysMatch.group(1)

                        if deviceVendor == vendorId.lower() and deviceProduct == productId.lower() and re.search(hidPhysTargetRegex, deviceHidPhys):
                            inputDeviceBasePath = re.search(r"(.*/input2)", deviceHidPhys).group(1)
                            return f"/dev/{device}", inputDeviceBasePath

            except FileNotFoundError:
                pass
    return None, None

# trying to hide the original controller via udev to only use virutal output so it can get picked up by inputplumber
def hideDeviceFromEvdev():
    try:
        udevRule = 'SUBSYSTEM=="input", ATTRS{idVendor}=="04b4", ATTRS{idProduct}=="2412", MODE="0666", ENV{LIBINPUT_IGNORE}="1"\n'
        udevRule2 = 'KERNEL=="uinput", ATTRS{name}=="Vader4Pro DInput", ENV{ID_MODEL}="Vader4Pro DInput"'
        udevRulePath = "/etc/udev/rules.d/99-TMP-flydigi-vader4pro.rules"

        # write udev rule to file
        with open(udevRulePath, "w") as ruleFile:
            ruleFile.write(udevRule)
            ruleFile.write(udevRule2)

        # reload udev rules
        subprocess.run(["udevadm", "control", "--reload-rules"], check=True)
        subprocess.run(["udevadm", "trigger"], check=True)

        print("successfully hidden from udev.")

    except subprocess.CalledProcessError as e:
        print(f"command execution failed: {e}")
    except Exception as e:
        print(f"hiding device failed: {e}")

def cleanupUdevRule():
    try:
        udevRulePath = "/etc/udev/rules.d/99-TMP-flydigi-vader4pro.rules"
        os.remove(udevRulePath)
        subprocess.run(["udevadm", "control", "--reload-rules"], check=True)
        subprocess.run(["udevadm", "trigger"], check=True)

        print("udev restored.")

    except FileNotFoundError:
        print("udev rule file not found")
    except subprocess.CalledProcessError as e:
        print(f"command execution failed: {e}")
    except Exception as e:
        print(f"error removing udev rule: {e}")

# uinput initial setup
try:
    events = (
        uinput.BTN_SOUTH,
        uinput.BTN_EAST,
        uinput.BTN_NORTH,
        uinput.BTN_WEST,
        uinput.BTN_TL,
        uinput.BTN_TR,
        uinput.BTN_TL2,
        uinput.BTN_TR2,
        uinput.BTN_SELECT,
        uinput.BTN_START,
        uinput.BTN_MODE,
        uinput.BTN_DPAD_UP,
        uinput.BTN_DPAD_DOWN,
        uinput.BTN_DPAD_LEFT,
        uinput.BTN_DPAD_RIGHT,
        uinput.ABS_X + (-127, 127, 0, 127),
        uinput.ABS_Y + (-127, 127, 0, 127),
        uinput.ABS_RX + (-127, 127, 0, 127),
        uinput.ABS_RY + (-127, 127, 0, 127),
        uinput.ABS_Z + (0, 255, 0, 0),
        uinput.ABS_RZ + (0, 255, 0, 0),
        uinput.BTN_TRIGGER_HAPPY5,
        uinput.BTN_TRIGGER_HAPPY6,
        uinput.BTN_TRIGGER_HAPPY7,
        uinput.BTN_TRIGGER_HAPPY8,
        uinput.BTN_TRIGGER_HAPPY9,
        uinput.BTN_TRIGGER_HAPPY10,
        uinput.BTN_TRIGGER_HAPPY13,
        uinput.BTN_THUMBL,
        uinput.BTN_THUMBR
    )
    device = uinput.Device(events, name="Vader4Pro DInput")
    print("uinput device created")
except Exception as e:
    print(f"udev device creation failed: {e}")
    exit(1)

# process the button fields
def processButtonField(value, buttonMap):
    for button, buttonValue in buttonMap.items():
        if value & buttonValue:
            device.emit(button, 1)
        else:
            device.emit(button, 0)

# main
try:
    hideDeviceFromEvdev()
    hidrawPath, inputDeviceBasePath = findHidrawDevice()
    print(f"hidraw path: {hidrawPath}")
    if hidrawPath is not None:
        hidrawFile = open(hidrawPath, "rb")
        print(f"hidraw file opened: {hidrawFile}")

        while True:
            try:
                data = hidrawFile.read(64)
                if len(data) != 64:
                    continue

                buttonData7 = data[7]
                buttonData8 = data[8]
                buttonData9 = data[9]
                buttonData10 = data[10]

                processButtonField(buttonData7,
                                   {uinput.BTN_TRIGGER_HAPPY9: 1,
                                    uinput.BTN_TRIGGER_HAPPY10: 2,
                                    uinput.BTN_TRIGGER_HAPPY7: 4,
                                    uinput.BTN_TRIGGER_HAPPY8: 16,
                                    uinput.BTN_TRIGGER_HAPPY6: 32,
                                    uinput.BTN_TRIGGER_HAPPY5: 8})
                processButtonField(buttonData8,
                                   {uinput.BTN_TRIGGER_HAPPY13: 1,
                                    uinput.BTN_MODE: 8})
                processButtonField(buttonData9,
                                   {uinput.BTN_EAST: 32,
                                    uinput.BTN_SOUTH: 16,
                                    uinput.BTN_WEST: 128,
                                    uinput.BTN_SELECT: 64,
                                    uinput.BTN_DPAD_UP: 1,
                                    uinput.BTN_DPAD_RIGHT: 2,
                                    uinput.BTN_DPAD_DOWN: 4,
                                    uinput.BTN_DPAD_LEFT: 8})
                processButtonField(buttonData10,
                                   {uinput.BTN_START: 2,
                                    uinput.BTN_NORTH: 1,
                                    uinput.BTN_TL: 4,
                                    uinput.BTN_TR: 8,
                                    uinput.BTN_TL2: 16,
                                    uinput.BTN_TR2: 32,
                                    uinput.BTN_THUMBL: 64,
                                    uinput.BTN_THUMBR: 128})

                # axis
                device.emit(uinput.ABS_X, data[17] - 127)
                device.emit(uinput.ABS_Y, data[19] - 127)
                device.emit(uinput.ABS_RX, data[21] - 127)
                device.emit(uinput.ABS_RY, data[22] - 127)
                device.emit(uinput.ABS_Z, data[23])
                device.emit(uinput.ABS_RZ, data[24])

                device.syn()

            except FileNotFoundError:
                print(f"{hidrawPath} not found.")
                break
            except KeyboardInterrupt:
                print("closing hidraw file...")
                if 'hidrawFile' in locals():
                    hidrawFile.close()
                break
            except Exception as e:
                print(f"error: {e}")
                break
    else:
        print("hidraw device not found.")

except Exception as e:
    print(f"error: {e}")

finally:
    cleanupUdevRule()
