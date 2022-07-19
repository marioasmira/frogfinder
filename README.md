# Simple tracker to record after movement

This small script that detects movement between frames and starts a picamera recording.

## Description

This project started as a way to record a pet frog without having the camera recording at all times. Following along with an [example](https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/) on how to track motion with only motion (PIR would be okay to track mammals or birds, but frogs are not the best thing to track with an infrared sensor).  
I started this script as a copy of the original example and modified as needed for my purposes. I started by removing the Dropbox part of the code as well as the temporary file handling. I then added a way to stop the detection loop and to start a video recording.  
As it is now, this script scans the video feed of a picamera and detects motion above a certain threshold. It then changes resolution and framerate to start recording video for a specified length of time. Afterwards, the script goes back to motion detection and continues the loop. This results in several video files with the specified length of time which can be stored in the SD card, a mounted USB external drive or even a NAS.  
This has been running reliably for a few years now, so it is relatively reliable.

## Getting Started

### Dependencies

* This script has been only used in both a Raspberry Pi Zero W and a Raspberry Pi Zero 2 W running the default Raspberry Pi OS (current version as of writing is July 2022).
* Opencv
* imutils (can be found [here](https://github.com/jrosebr1/imutils))
* all dependencies of the above

### Installing

* To run this script you need to first enable the picamera in the `raspi-config` menu.
* Assuming all dependencies are already installed, you can just clone this repository with

```bash
git clone https://github.com/marioasmira/frogfinder
```

### Executing program

* Start by focusing the picamera to the correct surface where you will be detecting movement.
* Modify whichever relevant parameters in the `configuration.json` file:
  * `debug`: true or false, to print the values evaluated for capture onscreen;
  * `video_path`: the absolute path to where you want to save your video files;
  * `upload_seconds`: float number, to specify duration in seconds for video recording after motion is detected;
  * `min_motion_frames`: integer, the number of consecutive frames where motion is detected before starting to record;
  * `camera_warmup_time`: float number, to specify the duration in seconds to let the camera warmup before starting work;
  * `delta_thresh`: integer, used to specify the threshold at which to indicate there is a difference between frames;
  * `shutter_speed`: integer, shutter speed in micro seconds to synchronize capture and lights connected directly to main. Default value set to European 50 Mhz.
  * `detection_resolution`: [width, height], the resolution to use during the motion detection phase;
  * `detection_fps`: integer, framerate to use during the detection phase;
  * `detection_times`: integer, two values to specify between which hours the detection should run. It only uses the hour number so if the second number is 15, it will record until 15:59;
  * `capture_resolution`: [width, height], the resolution to use during the recording phase;
  * `capture_fps`: integer, framerate to use during the recording phase;
  * `detection_range`: integer, two values to specify the minimum and maximum area in the difference between frames to be considered as relevant motion (a frog moving);
  * `on_led_pin`: integer, indicate which pin in the GPIO should indicate if the program is running;
  * `record_led_pin`: integer, indicate which pin in the GPIO should indicate if the program is recording a video;
  * `temp_led_pin`: integer, indicate which pin in the GPIO should indicate if the temperature is too high or too low;
  * `hum_led_pin`: integer, indicate which pin in the GPIO should indicate if the humidity is too high or too low;
  * `pause_led_pin`: integer, indicate which pin in the GPIO should indicate if the program has the detection loop paused;
  * `button_pin`: integer, indicate which pin in the GPIO is connected to the detection loo pause button;
  * `dht_device_pin`: integer, indicate which pin in the GPIO is connected to the DHT device;
  * `env_save_time`: integer, how frequently (in seconds) should the program check temperature and humidity;
  * `humidity_interval`: integer, two values to specify the minimum and maximum humidity to keep the humidity LED off;
  * `temperature_interval`: integer, two values to specify the minimum and maximum humidity to keep the temperature LED off;
  * `display_pins`: integer, seven (7) pins to indicate which pins in the GPIO should control the 7 segment display;
  * `digit_pins`: integer, four (4) pins to indicate which pins in the GPIO should control the 4 digits in the 7 segment display;
  * `display_dot_pin`: integer, indicate which pin in the GPIO should control the dot (.) in the 7 segment display;
  * `heating_pin`: integer, indicate which pin in the GPIO should control the terrarium heating element. This pin should be connected to a relay since the Raspberry Pi will not be able to power a heating element;
  * `heating_minimum`: integer, values to specify the maximum temperature at which the heating element is off;
  * `remaining_pins`: integer, unused pins as of now. Might be changed to control lighting;
* After the parameters are chosen it is just a matter of running:

```bash
./frogfinder.py
```

## Authors

* Mário Artur Mira

## Version History

* 0.1
  * Initial Release
* 0.2
  * Tidied up the logic and how pins and displays are controlled.

## References

Adrian Rosebrock, *Home surveillance and motion detection with the Raspberry Pi, Python, OpenCV, and Dropbox*, PyImageSearch, [https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/](https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/), accessed on 19 September 2020
