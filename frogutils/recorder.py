from parameters import Parameters
from picamera import PiCamera
from picamera.array import PiRGBArray
import RPi.GPIO as GPIO
from parameters import Parameters
from time import sleep
from datetime import datetime
from frogutils.ledhandle import LED_OFF, LED_ON 
from frogutils.dirhandle import make_folder
import imutils
import cv2

def is_between(time, time_range) -> bool:
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]

class Recorder:
    motion_counter = 0
    avg = None
    camera: PiCamera
    video_path: str
    video_folder: str

    def __init__(self, pars: Parameters) -> None:
        # initialize the camera and grab a reference to the raw camera capture
        self.video_path = pars.get_value("video_path")
        self.video_folder = self.video_path + datetime.now().strftime("%Y%m%d") + "/"

    def detect(self, pars: Parameters, data_file, date_string,  stop_thread):
        camera = PiCamera()
        camera.resolution = tuple(pars.get_value("detection_resolution"))
        camera.framerate = pars.get_value("detection_fps")
        camera.shutter_speed = pars.get_value("shutter_speed")

        # allow the camera to warmup, then initialize the average frame, and frame motion counter
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Warming up...")
        sleep(pars.get_value("camera_warmup_time"))

        # start loop
        while True:
            LED_ON(pars.get_pin("on_led_pin"))

            # check if still the same day
            check_data_time = datetime.now()
            check_date_string = check_data_time.strftime("%Y%m%d")

            # if it's a different day, make a new folder
            if check_date_string != date_string:
                date_string = check_date_string
                # make directory for day
                self.video_folder = self.video_path + date_string + "/"
                make_folder(self.video_folder)

            # check if motion and if button is pressed
            will_pause = self.stream_parse(camera, pars, data_file, stop_thread)

            if stop_thread == True:
                return

            # if going to pause turn on led and wait for resume press
            if will_pause:
                current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                print("[INFO] " + current_time + " Paused!")
                LED_ON(pars.get_pin("pause_led_pin"))
                LED_OFF(pars.get_pin("on_led_pin"))
                sleep(2)
                GPIO.setup(pars.get_pin("button_pin"), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                paused = True 
                while(paused):
                    paused = not GPIO.input(pars.get_pin("button_pin"))
                current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                print("[INFO] " + current_time + " Continuing...")
                LED_OFF(pars.get_pin("pause_led_pin"))
                LED_ON(pars.get_pin("on_led_pin"))
                sleep(2)

            # otherwise starts a recording
            else:
                self.record(camera)
                
    def stream_parse(self, camera, pars: Parameters, data_file, stop_thread):
        GPIO.setup(pars.get_pin("button_pin"), GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        # return values to originals
        camera.resolution = tuple(pars.get_value("detection_resolution"))
        camera.framerate = pars.get_value("detection_fps")
        raw_capture = PiRGBArray(camera, size=tuple(pars.get_value("detection_resolution")))
        self.motion_counter = 0
        self.avg = None

        #capture frames from the camera
        for f in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
            # breaks function if program will close
            if stop_thread == True:
                raw_capture.truncate(0)
                break

            button_off = GPIO.input(pars.get_pin("button_pin"))
            if button_off:
                current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                print("[INFO] " + current_time + " Pausing...")
                sleep(1)
                raw_capture.truncate(0)
                return True

            now_time = datetime.now()
            if is_between(now_time.hour, pars.get_value("detection_times")):
                # breaks function if program will close
                if stop_thread == True:
                    raw_capture.truncate(0)
                    break

                for color in pars.get_pin("dioder_pins"):
                    LED_ON(color)
                # grab the raw NumPy array representing the image and initialize
                # the timestamp and occupied/unoccupied text
                frame = f.array
                presence = False
                # resize the frame, convert it to grayscale, and blur it
                frame = imutils.resize(frame, width=500)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                # if the average frame is None, initialize it
                if self.avg is None:
                    current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                    print("[INFO] " + current_time + " Starting background model...")
                    self.avg = gray.copy().astype("float")
                    raw_capture.truncate(0)
                    continue

                # accumulate the weighted average between the current frame and
                # previous frames, then compute the difference between the current
                # frame and running average
                cv2.accumulateWeighted(gray, self.avg, 0.5)
                frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

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
                        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                        print("[INFO] " + current_time + " Got one!")
                        return False
                else:
                    motion_counter = 0

                # clear the stream in preparation for the next frame
                raw_capture.truncate(0)

            else:
                for color in pars.get_pin("dioder_pins"):
                    LED_OFF(color)
                raw_capture.truncate(0)

    def record(self, camera, pars: Parameters):
        # change resolution and framerate for HD
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Changing camera resolution and framerate...")
        camera.resolution = tuple(pars.get_value("capture_resolution"))
        camera.framerate = pars.get_value("capture_fps")
        video_time = datetime.now()
        video_name = self.video_folder + video_time.strftime("%Y%m%d_%H%M%S") + ".h264"


        LED_ON(pars.get_pin("record_led_pin"))
        LED_OFF(pars.get_pin("on_led_pin"))
        # record video
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Start recording.")
        camera.start_recording(video_name)
        camera.wait_recording(pars.get_value("upload_seconds"))
        camera.stop_recording()
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Finished recording!")
        print("[INFO] " + current_time + " Returning camera to search values.")
        
        LED_OFF(pars.get_pin("record_led_pin"))
        LED_ON(pars.get_pin("on_led_pin"))

