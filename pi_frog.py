# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import imutils
import json
from datetime import datetime
import time
import cv2
import sys
import os

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

# initialize the camera and grab a reference to the raw camera capture
cam = PiCamera()
cam.resolution = tuple(conf["detection_resolution"])
cam.framerate = conf["detection_fps"]
raw_capture = PiRGBArray(cam, size=tuple(conf["detection_resolution"]))
video = conf["video_path"]

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
if not os.path.exists(video_folder):
    try:
        os.makedirs(video_folder)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

# set up data file
data_string =  data_time.strftime("%Y%m%d_%H%M%S")
data_file = open((data_string + "_" +
    str(conf["min_motion_frames"]) + "_" +
    str(conf["min_area"]) + ".csv"), "w+")
data_file.write("time,motion_counter,iter,contour\n")

try:
    # start loop
    while True:
        #capture frames from the camera
        for f in cam.capture_continuous(raw_capture, format="bgr", use_video_port=True):
            # grab the raw NumPy array representing the image and initialize
            # the timestamp and occupied/unoccupied text
            frame = f.array
            presence = False

            # resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # if the average frame is None, initialize it
            if avg is None:
                print("[INFO] Starting background model...")
                avg = gray.copy().astype("float")
                raw_capture.truncate(0)
                continue

            # accumulate the weighted average between the current frame and
            # previous frames, then compute the difference between the current
            # frame and running average
            cv2.accumulateWeighted(gray, avg, 0.5)
            frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

            # threshold the delta image, dilate the thresholded image to fill
            # in holes, then find contours on thresholded image
            thresh = cv2.threshold(frame_delta, conf["delta_thresh"], 255,
                cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)


            # loop over the contours
            counter = 0 # to print how many areas were picked up as motion
            frame_time  = datetime.now()    # each frame can have more than one area
            formated_frame_time = frame_time.strftime("%Y/%m/%d_%H:%M:%S.%f")
            if len(cnts) < conf["max_areas"]:
                for c in cnts:
                    data_file.write(formated_frame_time + "," +
                            str(motion_counter) + "," +
                            str(counter) + "," +
                            str(cv2.contourArea(c)) + "\n")
                    if conf["debug"]:
                            print(formated_frame_time + "    " +
                                str(motion_counter) + "    " +
                                str(counter) + "    " +
                                str(cv2.contourArea(c)))
                    # if the contour is too small, ignore it
                    counter += 1
                    if ((cv2.contourArea(c) > conf["min_area"]) and (cv2.contourArea(c) < conf["max_area"])):
                        # and update the text
                        presence = True
                    else:
                        continue

            if presence:
                motion_counter += 1
                # check to see if the number of frames with consistent motion is high enough
                if (motion_counter >= conf["min_motion_frames"]):
                    print("[INFO] Got one!")
                    break
            else:
                motion_counter = 0

            # clear the stream in preparation for the next frame
            raw_capture.truncate(0)


        # change resolution and framerate for HD
        print("[INFO] Changing camera resolution and framerate...")
        cam.resolution = tuple(conf["capture_resolution"])
        cam.framerate = conf["capture_fps"]
        video_time = datetime.now()
        video_name = video_folder + video_time.strftime("%Y%m%d_%H%M%S") + ".h264"

        # record video
        print("[INFO] Start recording.")
        cam.start_recording(video_name)
        cam.wait_recording(conf["upload_seconds"])
        cam.stop_recording()
        print("[INFO] Finished recording!")
        print("[INFO] Returning camera to search values.")
        
        # return values to originals
        cam.resolution = tuple(conf["detection_resolution"])
        cam.framerate = conf["detection_fps"]
        raw_capture = PiRGBArray(cam, size=tuple(conf["detection_resolution"]))
        motion_counter = 0
        avg = None



finally:
    cam.close()
    data_file.close()
