import json
import logging
import os.path

FILE_PATH = "private/settings.json"

# defaults used if no individual settings defined in JSON file in path above
val = {
    "nr_of_leds": 46,
    "theta_dir_gpio": 4,
    "led_brightness": 1.0,  # 1.0 = no reduction, 0.0 = dark
    "do_homing_on_startup": True,
    "simulate_led_hw": False,
    "simulate_axes_hw": False
}


def init():
    global val
    if os.path.exists(FILE_PATH):
        json = read_settings_file()
        val.update(json)


def read_settings_file():
    with open(FILE_PATH, "r") as jsonfile:
        return json.load(jsonfile)


# Logging is not ready during init(), therefore log later
def dump_config_to_log():
    logging.info("Sandtrails settings: " + str(val))


# run statically so config is available in static parts of code
init()
