#import json
import RPi.GPIO as GPIO

class Parameters:
    values = {}
    pins = {}

    def __init__(self, config) -> None:

        self.values["debug"] = config["debug"]

        # video values
        self.values["video_path"] = config["video_path"]
        self.values["upload_seconds"] = config["upload_seconds"]
        self.values["min_motion_frames"] = config["min_motion_frames"]
        self.values["camera_warmup_time"] = config["camera_warmup_time"]
        self.values["delta_threshold"] = config["delta_threshold"]
        self.values["shutter_speed"] = config["shutter_speed"]
        self.values["detection_resolution"] = config["detection_resolution"]
        self.values["detection_fps"] = config["detection_fps"]
        self.values["detection_times"] = config["detection_times"]
        self.values["capture_resolution"] = config["capture_resolution"]
        self.values["capture_fps"] = config["capture_fps"]
        self.values["detection_range"] = config["detection_range"]
        self.values["max_areas"] = config["max_areas"]

        # environment values
        self.values["env_save_time"] = config["env_save_time"]
        self.values["humidity_interval"] = config["humidity_interval"]
        self.values["temperature_interval"] = config["temperature_interval"]

        # add pins to dictionary
        self.pins["on_led_pin"] = config["on_led_pin"]
        self.pins["record_led_pin"] = config["record_led_pin"]
        self.pins["temp_led_pin"] = config["temp_led_pin"]
        self.pins["hum_led_pin"] = config["hum_led_pin"]
        self.pins["pause_led_pin"] = config["pause_led_pin"]
        self.pins["button_pin"] = config["button_pin"]
        self.pins["dht_device_pin"] = config["dht_device_pin"]
        self.pins["display_pins"] = config["display_pins"]
        self.pins["digit_pins"] = config["digit_pins"]
        self.pins["display_dot_pin"] = config["display_dot_pin"]
        self.pins["dioder_pins"] = config["dioder_pins"]
        

    def setup_GPIO(self) -> None:
        # define pins and GPIO setup
        GPIO.setmode(GPIO.BCM)

        for k in self.pins.keys():
            if(k == "button_pin"):
                GPIO.setup(self.pins[k], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            elif(k == "dht_device_pin"):
                GPIO.setup(self.pins[k], GPIO.IN)
            else:
                pins = self.pins[k]
                if(isinstance(pins, int)):
                    GPIO.setup(pins, GPIO.OUT)
                else:
                    for pin in pins:
                        GPIO.setup(pin, GPIO.OUT)

    def get_pin(self, str):
        return self.pins[str]

    def get_value(self, str):
        return self.values[str]

