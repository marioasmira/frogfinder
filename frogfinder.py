#!/usr/bin/env python3

# import the necessary packages
from frogutils.environment import Environment
import frogutils.dirhandle as dirhandle
#import frogutils.streamhandle as streamhandle
import json
from datetime import datetime
import time
import sys
from multiprocessing import Process
from frogutils.parameters import Parameters
from frogutils.recorder import Recorder
from frogutils.environment import Environment
import RPi.GPIO as GPIO

try:
    try:
        config = json.load(open("configuration.json"))
    except OSError:
        print("Couldn't open the conf.json file. Mkae sure it's in the same directory.")

    pars = Parameters(config)
    del config
    GPIO.setwarnings(False)
    pars.setup_GPIO()

    # get date
    data_time = datetime.now()
    date_string = data_time.strftime("%Y%m%d")

    # make directory for day
    video = pars.get_value("video_path")
    video_folder = video + date_string + "/"
    dirhandle.make_folder(video_folder)

    # set up data file
    data_string = data_time.strftime("%Y%m%d_%H%M%S")
    data_file = open((video + data_string + "_" +
                      str(pars.get_value("min_motion_frames")) + "_" +
                      str(pars.get_value("detection_range")[1]) + ".csv"), "w+")
    data_file.write("time,motion_counter,iter,contour\n")

    env_file = open((data_string + "_env.csv"), "w+")
    env_file.write("time,temperature,humidity\n")

    recorder = Recorder(pars)
    environment = Environment(pars)

    stop_threads = False
    p_env = Process(target=environment.loop, args=(
        env_file, pars, lambda: stop_threads))
    p_vid = Process(target=recorder.detect, args=(
        pars, data_file, date_string, lambda: stop_threads))

    p_vid.start()
    p_env.start()

    while True:
      key_press = input("Write 'quit' to exit the program.\n")
      if key_press == "quit":
        stop_threads = True
        break
      else:
        time.sleep(0.05)
        
    p_env.terminate()
    p_vid.terminate()
    p_env.join()
    p_vid.join()

finally:
    print("[INFO] Exiting program...")
    pars.cleanup_pins()
    data_file.close()
    env_file.close()
    GPIO.cleanup()
    print("[INFO] Done.")
    sys.exit(0)
