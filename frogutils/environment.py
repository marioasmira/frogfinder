from frogutils.parameters import Parameters
from Adafruit_DHT import DHT11, read_retry
from datetime import datetime
from parameters import Parameters
from frogutils.ledhandle import LED_OFF, LED_ON 
from frogutils.recorder import is_between
from time import sleep

class Environment:
    def __init__(self, pars: Parameters) -> None:
        # define temperature and humidity device
        self.dht_device = DHT11

        self.previous_time = datetime.now()
        self.humidity, self.temperature = read_retry(
            self.dht_device, pars.get_pin("dht_device_pin"))

    def loop(self, pars: Parameters, env_file, env_pipe):
        env_pipe.send([int(self.temperature), int(self.humidity)])

        while True:
            now_time = datetime.now()
            second_difference = (now_time - self.previous_time).total_seconds()
            if second_difference >= pars.get_value("env_save_time"):
                self.previous_time = datetime.now()
                self.humidity, self.temperature = read_retry(self.dht_device, pars.get_pin("dht_device_pin"))
                frame_time  = datetime.now()    # each frame can have more than one area
                formated_frame_time = frame_time.strftime("%Y/%m/%d_%H:%M:%S.%f")

                if self.humidity is not None and self.temperature is not None:
                    env_file.write(formated_frame_time + "," +
                            "{0:0.0f}".format(self.temperature) + "," +
                            "{0:0.0f}".format(self.humidity) + "\n")
                    if pars.get_value("debug"):
                        print(formated_frame_time + ", " +
                            "{0:0.0f}".format(self.temperature) + "C, " +
                            "{0:0.0f}".format(self.humidity) + "%")                        
                    if(not is_between(self.humidity, pars.get_value("humidity_interval"))):
                        LED_ON(pars.get_pin("hum_led_pin"))
                    else:
                        LED_OFF(pars.get_pin("hum_led_pin"))
                    if(not is_between(self.temperature, pars.get_value("temperature_interval"))):
                        LED_ON(pars.get_pin("temp_led_pin"))
                    else:
                        LED_OFF(pars.get_pin("temp_led_pin"))
                    env_pipe.send([int(self.temperature), int(self.humidity)])

            sleep(1)



                    
