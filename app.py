import os
import sys

from evdev import ecodes, KeyEvent
import evdev
import qhue

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

INPUT_DEVICE = "/dev/input/by-id/usb-Apple_Computer__Inc._IR_Receiver-event-ir"

HUE_BRIDGE_IP = "192.168.189.160"
HUE_CONF_PATH = "~/.qhue.conf"

HUE_BRI_DELTA = 32

# --------------------------------------------------------------------------- #
# The actual code
# --------------------------------------------------------------------------- #

# Connect to hue
hue_username = None
config_path = os.path.expanduser(HUE_CONF_PATH)
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        hue_username = f.read()
else:
    while True:
        try:
            hue_username = qhue.create_new_username(HUE_BRIDGE_IP)
            break
        except qhue.QhueException as err:
            print("Error occurred while creating a new username: {}".format(err))

    with open(config_path, "w") as f:
        f.write(hue_username)

hue = qhue.Bridge(HUE_BRIDGE_IP, hue_username)

all_light_group = hue.groups[0]
light_group = hue.groups[1]
ceiling_group = hue.groups[2]

# Open the input device
dev = evdev.InputDevice(INPUT_DEVICE)

# Grab exclusive access to all events so gnome doesn't throw a fit
with dev.grab_context():
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = KeyEvent(event)

            if key_event.keystate == KeyEvent.key_up:
                continue

            print(key_event)

            code = key_event.keycode
            down_event = (key_event.keystate == KeyEvent.key_down)

            try:
                if code == "KEY_ENTER" and down_event:
                    # Toggle normal light state
                    toggle = not light_group()['action']['on']
                    light_group.action(on=toggle)
                elif code == "KEY_VOLUMEUP":
                    state = light_group()['action']
                    bri = state['bri']
                    if state['on']:
                        bri += HUE_BRI_DELTA
                        if bri > 255:
                            continue
                    light_group.action(on=True, bri=bri)
                elif code == "KEY_VOLUMEDOWN":
                    state = light_group()['action']
                    bri = state['bri']
                    if state['on']:
                        bri -= HUE_BRI_DELTA
                        if bri < 0:
                            continue
                    light_group.action(on=True, bri=bri)
                elif code == "KEY_PLAYPAUSE":
                    # Turn on ALL lights
                    # all_light_group.action(on=True)
                    pass
                elif code == "KEY_FORWARD":
                    # Turn on all ceiling lights
                    ceiling_group.action(on=True)
                elif code == "KEY_BACK":
                    # Turn of all ceiling lights
                    ceiling_group.action(on=False)
                elif code == "KEY_MENU":
                    # Turn off ALL lights (thx wakeup scene)
                    all_light_group.action(on=False)
                else:
                    print("Unknown event!")

            except qhue.QhueException as e:
                print(e)

