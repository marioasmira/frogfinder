#!/usr/bin/env python3

# import the necessary packages
import json
from datetime import datetime
from time import sleep
from sys import exit
from multiprocessing import Process, Pipe, Queue
from frogutils.environment import Environment
from frogutils.dirhandle import make_folder
from frogutils.parameters import Parameters
from frogutils.recorder import Recorder
from frogutils.display import Display
from frogutils.pinhandle import PinHandle
from RPi.GPIO import setwarnings, cleanup


class Frogfinder:
    def __init__(self) -> None:
        try:
            config = json.load(open("configuration.json"))
        except OSError:
            print(
                "Couldn't open the conf.json file. Mkae sure it's in the same directory."
            )

        self.pars = Parameters(config)
        del config
        setwarnings(False)
        self.pars.setup_GPIO()

        # make directory for day
        video_folder = (
            self.pars.get_value("video_path") + datetime.now().strftime("%Y%m%d") + "/"
        )
        print(video_folder)
        make_folder(video_folder)

        # set up data file
        data_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_file = open(
            (
                self.pars.get_value("video_path")
                + data_string
                + "_"
                + str(self.pars.get_value("min_motion_frames"))
                + "_"
                + str(self.pars.get_value("detection_range")[1])
                + ".csv"
            ),
            "w+",
        )
        self.data_file.write("time,motion_counter,iter,contour\n")

        self.env_file = open((data_string + "_env.csv"), "w+")
        self.env_file.write("time,temperature,humidity\n")

        self.recorder = Recorder(self.pars)
        self.environment = Environment(self.pars)
        self.display = Display()
        self.pinhandler = PinHandle()
        self.env_pipe, self.disp_pipe = Pipe()
        self.led_queue = Queue()

    def run(self):

        p_env = Process(
            target=self.environment.loop,
            args=(self.pars, self.env_file, self.env_pipe, self.led_queue),
        )
        p_disp = Process(target=self.display.digits, args=(self.pars, self.disp_pipe))
        p_vid = Process(
            target=self.recorder.detect,
            args=(self.pars, self.data_file, self.led_queue),
        )
        p_led = Process(target=self.pinhandler.run, args=(self.pars, self.led_queue))

        p_vid.start()
        p_env.start()
        p_disp.start()
        p_led.start()

        while True:
            key_press = input("Write 'quit' to exit the program.\n")
            if key_press == "quit":
                break
            else:
                sleep(0.05)

        p_disp.terminate()
        p_env.terminate()
        p_vid.terminate()
        p_led.terminate()
        p_disp.join()
        p_env.join()
        p_vid.join()
        p_led.join()

    def cleanup(self):
        print("[INFO] Exiting program...")
        self.pars.cleanup_pins()
        self.data_file.close()
        self.env_file.close()
        cleanup()
        print("[INFO] Done.")
        exit(0)


def main():
    try:
        finder = Frogfinder()
        finder.run()

    finally:
        finder.cleanup()


if __name__ == "__main__":
    main()
