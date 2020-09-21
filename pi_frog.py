# import the necessary packages
from pyimagesearch.tempimage import TempImage
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import imutils
import json
import time
import cv2

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
            help="path to the JSON configuration file")
args = vars(ap.parse_args())

# filter warnings, load the configuration and initialize the Dropbox
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))
video = conf["video_path"]
# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print("[INFO] warming up...")
time.sleep(conf["camera_warmup_time"])
avg = None
motionCounter = 0

# set up data file
data_file = open((time.strftime("%Y%m%d_%H%M%S") + "_" +
    str(conf["min_motion_frames"]) + "_" +
    str(conf["min_area"]) + ".csv"), "w+")
data_file.write("time,motionCounter,iter,contour\n")
if conf["debug"]:
    print("time,motionCounter,iter,contour\n")

# start loop
while True:
    #capture frames from the camera
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image and initialize
        # the timestamp and occupied/unoccupied text
        frame = f.array
        timestamp = datetime.datetime.now()
        text = "No frog"
        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        # if the average frame is None, initialize it
        if avg is None:
            print("[INFO] starting background model...")
            avg = gray.copy().astype("float")
            rawCapture.truncate(0)
            continue

        # accumulate the weighted average between the current frame and
        # previous frames, then compute the difference between the current
        # frame and running average
        cv2.accumulateWeighted(gray, avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
            cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)


        # loop over the contours
        counter = 0
        if len(cnts) < conf["max_areas"]:
            for c in cnts:
                data_file.write(time.strftime("%Y%m%d_%H%M%S") + "," +
                        str(motionCounter) + "," +
                        str(counter) + "," +
                        str(cv2.contourArea(c)) + "\n")
                if conf["debug"]:
                        print(time.strftime("%Y%m%d_%H%M%S") + "    " +
                            str(motionCounter) + "    " +
                            str(counter) + "    " +
                            str(cv2.contourArea(c)))
                # if the contour is too small, ignore it
                counter += 1
                if ((cv2.contourArea(c) > conf["min_area"]) and (cv2.contourArea(c) < conf["max_area"])):
                    # and update the text
                    text = "Frog!"
                else:
                    continue

        if text == "Frog!":
            motionCounter += 1
            # check to see if the number of frames with consistent motion is
            # high enough
            if (motionCounter >= conf["min_motion_frames"]):
                print("Got one!")
                break
        else:
            motionCounter = 0

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)


    # change resolution and framerate for HD
    print("[INFO] Changing camera resolution and framerate...")
    camera.resolution = tuple(conf["capture_resolution"])
    camera.framerate = conf["capture_fps"]
    video_name = video + time.strftime("%Y%m%d_%H%M%S") + ".h264"

    # record video
    print("[INFO] Start recording.")
    camera.start_recording(video_name)
    camera.wait_recording(conf["upload_seconds"])
    camera.stop_recording()
    print("[INFO] Finished recording!")
    print("[INFO] Returning camera to search values.")
    
    # return values to originals
    camera.resolution = tuple(conf["resolution"])
    camera.framerate = conf["fps"]
    rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))
    motionCounter = 0
    avg = None

    # warmup to new resolution
    time.sleep(conf["camera_warmup_time"])

