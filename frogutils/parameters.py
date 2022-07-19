import json
import RPi.GPIO as GPIO
from frogutils.pinhandle import PIN_OFF, PIN_ON


class Parameters:
    """Class to hold all information to use for the program

    Attributes
    ----------
    values : dictionary list of int and str
        Holds the names of parameters to be used together with their respective values.
    pins : dictionary list of int
        Holds the names of pins to be used together with their respective values.

    Methods
    -------
    setup_GPIO()
        Sets up all GPIO pins present in 'pins'.

    cleanup_pins()
        Cleans up all GPIO pins present in 'pins'.

    get_pin(name)
        Returns the pin number of 'name'.

    get_value(name)
        Returns the value of 'name'.

    """

    values = {}
    pins = {}

    def __init__(self, config: json) -> None:
        """Imports parameter values and names from json into the appropriate list

        Parameters
        ----------
        config : json
            A json file from which to import parameter values.

        """

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
        self.values["heating_minimum"] = config["heating_minimum"]

        # environment values
        self.values["env_save_time"] = config["env_save_time"]
        self.values["humidity_interval"] = config["humidity_interval"]
        self.values["temperature_interval"] = config["temperature_interval"]

        # add pins to dictionary
        # status pins
        self.pins["on_led_pin"] = config["on_led_pin"]
        self.pins["record_led_pin"] = config["record_led_pin"]
        self.pins["temp_led_pin"] = config["temp_led_pin"]
        self.pins["hum_led_pin"] = config["hum_led_pin"]
        self.pins["pause_led_pin"] = config["pause_led_pin"]

        # environment monitoring pins
        self.pins["dht_device_pin"] = config["dht_device_pin"]
        self.pins["heating_pin"] = config["heating_pin"]

        # video tracking pins
        self.pins["button_pin"] = config["button_pin"]

        # display pins
        self.pins["display_pins"] = config["display_pins"]
        self.pins["digit_pins"] = config["digit_pins"]
        self.pins["display_dot_pin"] = config["display_dot_pin"]

        # currently unused pins
        self.pins["remaining_pins"] = config["remaining_pins"]

    def setup_GPIO(self) -> None:
        """Sets up all GPIO pins present in 'pins'."""

        # define pins and GPIO setup
        GPIO.setmode(GPIO.BCM)

        for k in self.pins.keys():
            if k == "button_pin":
                GPIO.setup(self.pins[k], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            elif k == "dht_device_pin":
                GPIO.setup(self.pins[k], GPIO.IN)
            else:
                pins = self.pins[k]
                if isinstance(pins, int):
                    GPIO.setup(pins, GPIO.OUT)
                else:
                    for pin in pins:
                        GPIO.setup(pin, GPIO.OUT)

    def cleanup_pins(self) -> None:
        """Cleans up all GPIO pins present in 'pins'."""

        for k in self.pins.keys():
            if k == "button_pin":
                continue
            elif k == "pause_led_pin":
                continue
            elif k == "dht_device_pin":
                continue
            elif k == "display_pins":
                pins = self.pins[k]
                for pin in pins:
                    PIN_ON(pin)
            elif k == "digit_pins":
                pins = self.pins[k]
                for pin in pins:
                    PIN_ON(pin)
            elif k == "display_dot_pin":
                PIN_ON(self.pins[k])
            else:
                pins = self.pins[k]
                if isinstance(pins, int):
                    PIN_OFF(pins)
                else:
                    for pin in pins:
                        PIN_OFF(pin)

    def get_pin(self, name: str) -> int:
        """Returns the pin number of 'name'

        Parameters
        ----------
        name : str
            The name of the pin to be seached.

        Returns
        ----------
        int
            The pin number correspondent to 'name'.

        """

        return self.pins[name]

    # can return int (parameters) or str (path for files)
    def get_value(self, name: str):
        """Returns the value of 'name'

        Parameters
        ----------
        name : str
            The name of the value to be seached.

        Returns
        ----------
        int or str
            The value correspondent to 'name'. Can be an int or a str denoting a directory/

        """
        return self.values[name]
