import imutils
import cv2
from datetime import datetime
import RPi.GPIO as GPIO
import time
from Adafruit_DHT import DHT11, read_retry
import frogutils.ledhandle as ledhandle 
import frogutils.displayhandle as displayhandle
import frogutils.dirhandle as dirhandle
from picamera.array import PiRGBArray
from picamera import PiCamera
from parameters import Parameters

def is_between(time, time_range) -> bool:
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]


def save_env(env_file, pars: Parameters, stop_thread):
    # define temperature and humidity device
    dht_device = DHT11

    previous_time = datetime.now()
    humidity, temperature = read_retry(
        dht_device, pars.get_pin("dht_device_pin"))
    while True:
        # breaks function if program will close
        if stop_thread == True:
            return

        now_time = datetime.now()
        second_difference = (now_time - previous_time).total_seconds()
        if second_difference >= pars.get_value("env_save_time"):
            previous_time = datetime.now()
            humidity, temperature = read_retry(dht_device, pars.get_pin("dht_device_pin"))
            frame_time  = datetime.now()    # each frame can have more than one area
            formated_frame_time = frame_time.strftime("%Y/%m/%d_%H:%M:%S.%f")
            if humidity is not None and temperature is not None:
                env_file.write(formated_frame_time + "," +
                        "{0:0.0f}".format(temperature) + "," +
                        "{0:0.0f}".format(humidity) + "\n")
                if pars.get_value("debug"):
                    print(formated_frame_time + ", " +
                        "{0:0.0f}".format(temperature) + "C, " +
                        "{0:0.0f}".format(humidity) + "%")
                if(not is_between(humidity, pars.get_value("humidity_interval"))):
                    ledhandle.LED_ON(pars.get_pin("hum_led_pin"))
                else:
                    ledhandle.LED_OFF(pars.get_pin("hum_led_pin"))
                if(not is_between(temperature, pars.get_value("temperature_interval"))):
                    ledhandle.LED_ON(pars.get_pin("temp_led_pin"))
                else:
                    ledhandle.LED_OFF(pars.get_pin("temp_led_pin"))
        else:
            if humidity is not None and temperature is not None:
                displayhandle.display(pars, int(temperature), int(humidity), 1)

def stream_parse(cam, raw_capture, pars: Parameters, data_file, avg, motion_counter, stop_thread):
    #GPIO.setup(conf["button_pin"], GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

    #capture frames from the camera
    for f in cam.capture_continuous(raw_capture, format="bgr", use_video_port=True):
        # breaks function if program will close
        if stop_thread == True:
            raw_capture.truncate(0)
            break

        button_off = GPIO.input(pars.get_pin("button_pin"))
        if button_off:
            print("[INFO] Pausing...")
            time.sleep(1)
            raw_capture.truncate(0)
            return True

        now_time = datetime.now()
        if is_between(now_time.hour, pars.get_value("detection_times")):
            # breaks function if program will close
            if stop_thread == True:
                raw_capture.truncate(0)
                break

            for color in pars.get_pin("dioder_pins"):
                ledhandle.LED_ON(color)
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
            thresh = cv2.threshold(frame_delta, pars.get_value("delta_threshold"), 255,
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
                if pars.get_value("debug"):
                        print(formated_frame_time + "    " +
                            str(motion_counter) + "    " +
                            str(counter) + "    " +
                            str(cv2.contourArea(c)))
                # if the contour is too small, ignore it
                counter += 1
                if (is_between(cv2.contourArea(c), pars.get_value("detection_range"))):
                    # and update the text
                    presence = True
                else:
                    continue

            if presence:
                motion_counter += 1
                # check to see if the number of frames with consistent motion is high enough
                if (motion_counter >= pars.get_value("min_motion_frames")):
                    print("[INFO] Got one!")
                    return False
            else:
                motion_counter = 0

            # clear the stream in preparation for the next frame
            raw_capture.truncate(0)

        else:
            for color in pars.get_pin("dioder_pins"):
                ledhandle.LED_OFF(color)
            raw_capture.truncate(0)

def detect_and_record(pars: Parameters, data_file, video_folder, date_string, stop_thread):
    # initialize the camera and grab a reference to the raw camera capture
    cam = PiCamera()
    cam.resolution = tuple(pars.get_value("detection_resolution"))
    cam.framerate = pars.get_value("detection_fps")
    cam.shutter_speed = 30000
    raw_capture = PiRGBArray(cam, size=tuple(pars.get_value("detection_resolution")))
    video = pars.get_value("video_path")
    
    # allow the camera to warmup, then initialize the average frame, and frame motion counter
    print("[INFO] Warming up...")
    time.sleep(pars.get_value("camera_warmup_time"))
    avg = None
    motion_counter = 0
    # start loop
    while True:
        ledhandle.LED_ON(pars.get_pin("on_led_pin"))

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
        will_pause = stream_parse(cam, raw_capture, pars, data_file, avg, motion_counter, stop_thread)

        if stop_thread == True:
            return

        # if going to pause turn on led and wait for resume press
        if will_pause:
            print("[INFO] Paused!")
            ledhandle.LED_ON(pars.get_pin("pause_led_pin"))
            ledhandle.LED_OFF(pars.get_pin("on_led_pin"))
            time.sleep(2)
            GPIO.setup(pars.get_pin("button_pin"), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            paused = True 
            while(paused):
                paused = not GPIO.input(pars.get_pin("button_pin"))
            print("[INFO] Continuing...")
            ledhandle.LED_OFF(pars.get_pin("pause_led_pin"))
            ledhandle.LED_ON(pars.get_pin("on_led_pin"))
            time.sleep(2)

        # otherwise starts a recording
        else:
            # change resolution and framerate for HD
            print("[INFO] Changing camera resolution and framerate...")
            cam.resolution = tuple(pars.get_value("capture_resolution"))
            cam.framerate = pars.get_value("capture_fps")
            video_time = datetime.now()
            video_name = video_folder + video_time.strftime("%Y%m%d_%H%M%S") + ".h264"


            ledhandle.LED_ON(pars.get_pin("record_led_pin"))
            ledhandle.LED_OFF(pars.get_pin("on_led_pin"))
            # record video
            print("[INFO] Start recording.")
            cam.start_recording(video_name)
            cam.wait_recording(pars.get_value("upload_seconds"))
            cam.stop_recording()
            print("[INFO] Finished recording!")
            print("[INFO] Returning camera to search values.")
            
            ledhandle.LED_OFF(pars.get_pin("record_led_pin"))
            ledhandle.LED_ON(pars.get_pin("on_led_pin"))
            # return values to originals
            cam.resolution = tuple(pars.get_value("detection_resolution"))
            cam.framerate = pars.get_value("detection_fps")
            raw_capture = PiRGBArray(cam, size=tuple(pars.get_value("detection_resolution")))
            motion_counter = 0
            avg = None


