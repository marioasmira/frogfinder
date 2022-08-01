from Adafruit_DHT import DHT22, read_retry
from datetime import datetime
from frogutils.parameters import Parameters
from frogutils.compare import is_between
from time import sleep


class Environment:
    def __init__(self, pars: Parameters) -> None:
        # define temperature and humidity device
        self.dht_device = DHT22

        self.previous_time = datetime.now()
        self.humidity, self.temperature = read_retry(
            self.dht_device, pars.get_pin("dht_device_pin")
        )
        self.currently_heating = False

    def loop(self, pars: Parameters, env_file, env_pipe, led_queue):
        self.output(pars, env_pipe, env_file)
        self.check_humidity(pars, led_queue)
        self.check_temperature(pars, led_queue)

        while True:
            now_time = datetime.now()
            second_difference = (now_time - self.previous_time).total_seconds()
            if second_difference >= pars.get_value("env_save_time"):
                self.previous_time = now_time
                self.humidity, self.temperature = read_retry(
                    self.dht_device, pars.get_pin("dht_device_pin")
                )

                if self.humidity is not None and self.temperature is not None:
                    self.output(pars, env_pipe, env_file)
                    self.check_humidity(pars, led_queue)
                    self.check_temperature(pars, led_queue)

            sleep(1)

    def check_temperature(self, pars: Parameters, led_queue):
        # turn on heating if it is too cold
        if self.temperature <= pars.values["heating_minimum"]:
            led_queue.put(["heating_pin", False])
            self.currently_heating = True
        # keep heating on if within 2 degrees of temperature
        elif (
            self.currently_heating
            and self.temperature <= pars.values["heating_minimum"] + 2
        ):
            led_queue.put(["heating_pin", False])
        # turn of heating if the temperature is correct
        else:
            led_queue.put(["heating_pin", True])
            self.currently_heating = False

        # turn on temperature led if outside the temperature interval
        if not is_between(self.temperature, pars.get_value("temperature_interval")):
            led_queue.put(["temp_led_pin", True])
        else:
            led_queue.put(["temp_led_pin", False])

    def check_humidity(self, pars: Parameters, led_queue):
        # turn on humidity led if outside the humidity interval
        if not is_between(self.humidity, pars.get_value("humidity_interval")):
            led_queue.put(["hum_led_pin", True])
        else:
            led_queue.put(["hum_led_pin", False])

    def output(self, pars: Parameters, env_pipe, env_file):
        env_pipe.send([int(self.temperature), int(self.humidity)])

        formated_frame_time = datetime.now().strftime("%Y/%m/%d_%H:%M:%S.%f")
        env_file.write(
            formated_frame_time
            + ","
            + "{0:0.0f}".format(self.temperature)
            + ","
            + "{0:0.0f}".format(self.humidity)
            + "\n"
        )
        if pars.get_value("debug"):
            print(
                formated_frame_time
                + ", "
                + "{0:0.0f}".format(self.temperature)
                + "C, "
                + "{0:0.0f}".format(self.humidity)
                + "%"
            )
