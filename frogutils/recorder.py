from multiprocessing.queues import Queue
from frogutils.parameters import Parameters
from picamera import PiCamera
from picamera.array import PiRGBArray
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime
from frogutils.dirhandle import make_folder
import imutils
import cv2
from frogutils.compare import is_between


class Recorder:
    motion_counter = 0
    avg = None
    video_path: str
    video_folder: str

    def __init__(self, pars: Parameters) -> None:
        # initialize the camera and grab a reference to the raw camera capture
        self.video_path = pars.get_value("video_path")
        self.video_folder = self.video_path + datetime.now().strftime("%Y%m%d") + "/"

    def detect(self, pars: Parameters, data_file: str, led_queue: Queue) -> None:
        camera = PiCamera(
            resolution=tuple(pars.get_value("detection_resolution")),
            framerate=pars.get_value("detection_fps"),
        )
        camera.shutter_speed = pars.get_value("shutter_speed")

        # allow the camera to warmup, then initialize the average frame, and frame motion counter
        date_string = datetime.now().strftime("%Y%m%d")
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Warming up...")
        sleep(pars.get_value("camera_warmup_time"))

        # start loop
        while True:
            led_queue.put(["on_led_pin", True])

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
            will_pause = self.stream_parse(camera, pars, data_file)

            # if going to pause turn on led and wait for resume press
            if will_pause:
                current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                print("[INFO] " + current_time + " Paused!")

                # change leds to show pause
                led_queue.put(["pause_led_pin", True])
                led_queue.put(["on_led_pin", False])
                sleep(2)

                # wait for the button press to resume
                GPIO.setup(
                    pars.get_pin("button_pin"), GPIO.IN, pull_up_down=GPIO.PUD_DOWN
                )
                paused = True
                while paused:
                    paused = not GPIO.input(pars.get_pin("button_pin"))

                # inform and return leds to normal
                current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                print("[INFO] " + current_time + " Continuing...")
                led_queue.put(["pause_led_pin", False])
                led_queue.put(["on_led_pin", True])
                sleep(2)

            # otherwise starts a recording
            else:
                self.record(camera, pars, led_queue)

    def stream_parse(self, camera: PiCamera, pars: Parameters, data_file: str) -> bool:
        # set values to originals
        camera.resolution = tuple(pars.get_value("detection_resolution"))
        camera.framerate = pars.get_value("detection_fps")
        raw_capture = PiRGBArray(
            camera, size=tuple(pars.get_value("detection_resolution"))
        )
        self.motion_counter = 0
        self.avg = None

        return self.monitor_stream(pars, camera, raw_capture, data_file)

    def record(self, camera, pars: Parameters, led_queue) -> None:
        # change resolution and framerate for HD
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Changing camera resolution and framerate...")
        camera.resolution = tuple(pars.get_value("capture_resolution"))
        camera.framerate = pars.get_value("capture_fps")
        video_time = datetime.now()
        video_name = self.video_folder + video_time.strftime("%Y%m%d_%H%M%S") + ".h264"
        print(video_name)
        led_queue.put(["record_led_pin", True])
        led_queue.put(["on_led_pin", False])
        # record video
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Start recording.")
        camera.start_recording(video_name)
        camera.wait_recording(pars.get_value("upload_seconds"))
        camera.stop_recording()
        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        print("[INFO] " + current_time + " Finished recording!")
        print("[INFO] " + current_time + " Returning camera to search values.")

        led_queue.put(["record_led_pin", False])
        led_queue.put(["on_led_pin", True])

    def monitor_stream(
        self,
        pars: Parameters,
        camera: PiCamera,
        raw_capture: PiRGBArray,
        data_file: str,
    ) -> bool:
        # setup the pause button
        GPIO.setup(pars.get_pin("button_pin"), GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # capture frames from the camera
        for f in camera.capture_continuous(
            raw_capture, format="bgr", use_video_port=True
        ):
            # return True if Pause button was pressed
            button_off = GPIO.input(pars.get_pin("button_pin"))
            if button_off:
                current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                print("[INFO] " + current_time + " Pausing...")
                sleep(1)
                raw_capture.truncate(0)
                return True

            now_time = datetime.now()
            if is_between(now_time.hour, pars.get_value("detection_times")):
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
                thresh = cv2.threshold(
                    frame_delta,
                    pars.get_value("delta_threshold"),
                    255,
                    cv2.THRESH_BINARY,
                )[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                cnts = cv2.findContours(
                    thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                cnts = imutils.grab_contours(cnts)

                # loop over the contours
                counter = 0  # to print how many areas were picked up as motion
                frame_time = datetime.now()  # each frame can have more than one area
                formated_frame_time = frame_time.strftime("%Y/%m/%d_%H:%M:%S.%f")

                if pars.get_value("debug"):
                    smallformated_frame_time = frame_time.strftime("%H:%M:%S%f")

                    if len(cnts) > 0:
                        ##### trying to save contours to a file
                        #create an empty image for contours
                        img_contours = frame
                        # draw the contours on the empty image
                        cv2.drawContours(img_contours, cnts, -1, (0,255,0), 3)
                        #save image
                        cv2.imwrite('test_images/'+ smallformated_frame_time + str(counter) + 'col.jpg', img_contours)
                        #create an empty image for contours
                        img_contours = gray
                        # draw the contours on the empty image
                        cv2.drawContours(img_contours, cnts, -1, (0,255,0), 3)
                        #save image
                        cv2.imwrite('test_images/'+ smallformated_frame_time + str(counter) + 'gray.jpg', img_contours)

                for c in cnts:
                    data_file.write(
                        formated_frame_time
                        + ","
                        + str(self.motion_counter)
                        + ","
                        + str(counter)
                        + ","
                        + str(cv2.contourArea(c))
                        + "\n"
                    )
                    if pars.get_value("debug"):
                        print(
                            formated_frame_time
                            + "    "
                            + str(self.motion_counter)
                            + "    "
                            + str(counter)
                            + "    "
                            + str(cv2.contourArea(c))
                        )
                    # if the contour is too small, ignore it
                    counter += 1
                    if is_between(
                        cv2.contourArea(c), pars.get_value("detection_range")
                    ):
                        # and update the text
                        presence = True
                    else:
                        continue

                if presence:
                    self.motion_counter += 1
                    # check to see if the number of frames with consistent motion is high enough
                    if self.motion_counter >= pars.get_value("min_motion_frames"):
                        current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                        print("[INFO] " + current_time + " Got one!")
                        return False
                else:
                    self.motion_counter = 0

                # clear the stream in preparation for the next frame
                raw_capture.truncate(0)

            else:
                raw_capture.truncate(0)
                sleep(60)
