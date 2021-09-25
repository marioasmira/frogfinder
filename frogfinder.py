#!/usr/bin/env python3

# import the necessary packages
import frogutils.dirhandle as dirhandle
import frogutils.ledhandle as ledhandle
import frogutils.streamhandle as streamhandle
from json import json
from datetime import datetime
import time
import sys
import Adafruit_DHT
from multiprocessing import Process
from parameters import Parameters

try:
    try:
        conf = json.load(open("configuration.json"))
    except OSError:
        print("Couldn't open the conf.json file. Mkae sure it's in the same directory.")

    pars = Parameters(config=conf)
    del conf

    pars.setup_GPIO()

    # define temperature and humidity device
    dht_device = Adafruit_DHT.DHT11

    # get date
    data_time = datetime.now()
    date_string = data_time.strftime("%Y%m%d")

    # make directory for day
    video = conf["video_path"]
    video_folder = video + date_string + "/"
    dirhandle.make_folder(video_folder)

    # set up data file
    data_string = data_time.strftime("%Y%m%d_%H%M%S")
    data_file = open((video + data_string + "_" +
                      str(conf["min_motion_frames"]) + "_" +
                      str(conf["min_area"]) + ".csv"), "w+")
    data_file.write("time,motion_counter,iter,contour\n")

    env_file = open((data_string + "_env.csv"), "w+")
    env_file.write("time,temperature,humidity\n")

    stop_threads = False
    p_env = Process(target=streamhandle.save_env, args=(
        env_file, dht_device, conf, lambda: stop_threads))
    p_vid = Process(target=streamhandle.detect_and_record, args=(
        conf, data_file, video_folder, date_string, lambda: stop_threads))

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
    ledhandle.LED_OFF(conf["on_led_pin"])
    ledhandle.LED_OFF(conf["record_led_pin"])
    ledhandle.LED_OFF(conf["temp_led_pin"])
    ledhandle.LED_OFF(conf["hum_led_pin"])
    ledhandle.LED_OFF(conf["pause_led_pin"])
    for pin in conf["display_pins"]:
        GPIO.output(pin, True)  # setting pins for segments
    for pin in conf["digit_pins"]:
        GPIO.output(pin, True)  # setting pins for digit selector
    GPIO.output(conf["display_dot_pin"], True)  # setting dot pin
    for pin in conf["dioder_pins"]:
        ledhandle.LED_OFF(pin)
    data_file.close()
    env_file.close()
    GPIO.cleanup()
    print("[INFO] Done.")
    sys.exit(0)
