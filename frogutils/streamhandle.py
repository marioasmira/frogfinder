import imutils
import cv2
from datetime import datetime
import RPi.GPIO as GPIO
import time

def stream_track(cam, raw_capture, conf, data_file, avg, motion_counter):
    GPIO.setup(conf["button_pin"], GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    #capture frames from the camera
    for f in cam.capture_continuous(raw_capture, format="bgr", use_video_port=True):
        button_off = GPIO.input(conf["button_pin"])
        if button_off:
            print("[INFO] Pausing...")
            time.sleep(2)
            raw_capture.truncate(0)
            return True

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
        #if len(cnts) < conf["max_areas"]:
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
                return False
        else:
            motion_counter = 0

        # clear the stream in preparation for the next frame
        raw_capture.truncate(0)

