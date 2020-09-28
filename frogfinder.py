# import the necessary packages
import frogutils.dirhandle as dirhandle
import frogutils.ledhandle as ledhandle 
import frogutils.streamhandle as streamhandle 
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import json
from datetime import datetime
import time
import sys
import os
import RPi.GPIO as GPIO
import board
import adafruit_dht

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

# define temperature and humidity device
#dht_device = adafruit_dht.DHT11(board.D24)

# initialize the camera and grab a reference to the raw camera capture
cam = PiCamera()
cam.resolution = tuple(conf["detection_resolution"])
cam.framerate = conf["detection_fps"]
raw_capture = PiRGBArray(cam, size=tuple(conf["detection_resolution"]))
video = conf["video_path"]
cam.shutter_speed = 30000
# allow the camera to warmup, then initialize the average frame, and frame motion counter
print("[INFO] Warming up...")
time.sleep(conf["camera_warmup_time"])
avg = None
motion_counter = 0

# get date
data_time = datetime.now()
date_string = data_time.strftime("%Y%m%d")

# make directory for day
video_folder = video + date_string + "/"
dirhandle.make_folder(video_folder)

# set up data file
data_string =  data_time.strftime("%Y%m%d_%H%M%S")
data_file = open((data_string + "_" +
    str(conf["min_motion_frames"]) + "_" +
    str(conf["min_area"]) + ".csv"), "w+")
data_file.write("time,motion_counter,iter,contour\n")

try:
    # start loop
    while True:
        ledhandle.LED_ON(conf["on_led_pin"])

        # check if still the same day
        check_data_time = datetime.now()
        check_date_string = check_data_time.strftime("%Y%m%d")

        # if it's a different day, make a new folder
        if check_date_string != date_string:
            date_string = check_date_string
            # make directory for day
            video_folder = video + date_string + "/"
            dirhandle.make_folder(video_folder)

        # check if motion and if button is pressed
        will_pause = streamhandle.stream_track(cam, raw_capture, conf, data_file, avg, motion_counter)

        # if going to pause turn on led and wait for resume press
        if will_pause:
            print("[INFO] Paused!")
            ledhandle.LED_ON(conf["pause_led_pin"])
            time.sleep(2)
            GPIO.setup(conf["button_pin"], GPIO.IN, pull_up_down = GPIO.PUD_UP)
            continuing = False 
            while(not continuing):
                continuing = not GPIO.input(conf["button_pin"])
            print("[INFO] Continuing...")
            time.sleep(2)
            ledhandle.LED_OFF(conf["pause_led_pin"])

        # otherwise starts a recording
        else:
            # change resolution and framerate for HD
            print("[INFO] Changing camera resolution and framerate...")
            cam.resolution = tuple(conf["capture_resolution"])
            cam.framerate = conf["capture_fps"]
            video_time = datetime.now()
            video_name = video_folder + video_time.strftime("%Y%m%d_%H%M%S") + ".h264"


            ledhandle.LED_ON(conf["record_led_pin"])
            # record video
            print("[INFO] Start recording.")
            cam.start_recording(video_name)
            cam.wait_recording(conf["upload_seconds"])
            cam.stop_recording()
            print("[INFO] Finished recording!")
            print("[INFO] Returning camera to search values.")
            
            ledhandle.LED_OFF(conf["record_led_pin"])
            # return values to originals
            cam.resolution = tuple(conf["detection_resolution"])
            cam.framerate = conf["detection_fps"]
            raw_capture = PiRGBArray(cam, size=tuple(conf["detection_resolution"]))
            motion_counter = 0
            avg = None

finally:
    ledhandle.LED_OFF(conf["on_led_pin"])
    ledhandle.LED_OFF(conf["record_led_pin"])
    ledhandle.LED_OFF(conf["temp_led_pin"])
    ledhandle.LED_OFF(conf["hum_led_pin"])
    ledhandle.LED_OFF(conf["pause_led_pin"])
    cam.close()
    data_file.close()
    GPIO.cleanup()
