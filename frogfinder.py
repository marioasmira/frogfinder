# import the necessary packages
import frogutils.dirhandle as dirhandle
import frogutils.ledhandle as ledhandle 
import frogutils.streamhandle as streamhandle 
import argparse
import warnings
import json
from datetime import datetime
import time
import sys
import os
import RPi.GPIO as GPIO
import Adafruit_DHT
from multiprocessing import Process

try:
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True,
                help="path to the JSON configuration file")
    args = vars(ap.parse_args())

    # filter warnings
    if not sys.warnoptions:
        warnings.filterwarnings("ignore")

    # import configuration options
    conf = json.load(open(args["conf"]))

    # define pins and GPIO setup
    GPIO.setmode(GPIO.BCM)

    # inside a try-finally to make sure the pins are cleaned up in case of wrong pins
    GPIO.setup(conf["on_led_pin"], GPIO.OUT)
    GPIO.setup(conf["record_led_pin"], GPIO.OUT)
    GPIO.setup(conf["temp_led_pin"], GPIO.OUT)
    GPIO.setup(conf["hum_led_pin"], GPIO.OUT)
    GPIO.setup(conf["pause_led_pin"], GPIO.OUT)
    GPIO.setup(conf["button_pin"], GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(conf["dht_device_pin"], GPIO.IN)
    for pin in conf["display_pins"]:
      GPIO.setup(pin,GPIO.OUT) # setting pins for segments
    for pin in conf["digit_pins"]:
      GPIO.setup(pin,GPIO.OUT) # setting pins for digit selector
    GPIO.setup(conf["display_dot_pin"],GPIO.OUT) # setting dot pin

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
    data_string =  data_time.strftime("%Y%m%d_%H%M%S")
    data_file = open((data_string + "_" +
        str(conf["min_motion_frames"]) + "_" +
        str(conf["min_area"]) + ".csv"), "w+")
    data_file.write("time,motion_counter,iter,contour\n")

    env_file = open((data_string + "_env.csv"), "w+")
    env_file.write("time,temperature,humidity\n")

    p_env = Process(target = streamhandle.save_env, args = (env_file, dht_device, conf))
    p_vid = Process(target = streamhandle.detect_and_record, args = (conf, data_file, video_folder, date_string))

    p_vid.start()
    p_env.start()

    p_env.join()
    p_vid.join()

finally:
    p_env.terminate()
    p_vid.terminate()
    p_env.join()
    p_vid.join()
    ledhandle.LED_OFF(conf["on_led_pin"])
    ledhandle.LED_OFF(conf["record_led_pin"])
    ledhandle.LED_OFF(conf["temp_led_pin"])
    ledhandle.LED_OFF(conf["hum_led_pin"])
    ledhandle.LED_OFF(conf["pause_led_pin"])
    for pin in conf["display_pins"]:
      GPIO.output(pin, True) # setting pins for segments
    for pin in conf["digit_pins"]:
      GPIO.output(pin, True) # setting pins for digit selector
    GPIO.output(conf["display_dot_pin"], True) # setting dot pin
    cam.close()
    data_file.close()
    env_file.close()
    GPIO.cleanup()
