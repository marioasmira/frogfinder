# Simple tracker to record after movement

This small script that detects movement between frames and starts a picamera recording.

## Description

This project started as a way to record a pet frog without having the camera recording at all times. Following along with an [example](https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/) on how to track motion with only motion (PIR would be okay to track mammals or birds, but frogs are not the best thing to track with an infrared sensor).  
I started this script as a copy of the original example and modified as needed for my purposes. I started by removing the Dropbox part of the code as well as the temporary file handling. I then added a way to stop the detection loop and to start a video recording.  
As it is now, this script scans the video feed of a picamera and detects motion above a certain threshold. It then changes resolution and framerate to start recording video for a specified length of time. Afterwards, the script goes back to motion detection and continues the loop. This results in several video files with the specified length of time which can be stored in the SD card, a mounted USB external drive or even a NAS.

## Getting Started

### Dependencies

* This script has been only used in a Raspberry Pi Zero W running the default Raspberry Pi OS (current version as of writing is August 2020).
* Opencv
* imutils (can be found [here](https://github.com/jrosebr1/imutils))
* all dependencies of the above

### Installing

* To run this script you need to first enable the picamera in the `raspi-config` menu.
* Assuming all dependencies are already installed, you can just clone this repository with
```
git clone https://github.com/marioasmira/frogfinder
```

### Executing program

* Start by focusing the picamera to the correct surface where you will be detecting movement.
* Modify whichever relevant parameters in the `conf.json` file:
  - `debug`: true or false, to print the values evaluated for capture onscreen; 
  * `video_path`: the absolute path to where you want to save your video files;
  * `upload_seconds`: float number, to specify duration in seconds for video recording after motion is detected;
  * `min_motion_frames`: integer, the number of consecutive frames where motion is detected before starting to record;
  * `camera_warmup_time`: float number, to specify the duration in seconds to let the camera warmup before starting work;
  * `delta_thresh`: integer, used to specify the threshold at which to indicate there is a difference between frames;
  * `detection_resolution`: [width, height], the resolution to use during the motion detection phase;
  * `detection_fps`: integer, framerate to use during the detection phase;
  * `capture_resolution`: [width, height], the resolution to use during the recording phase;
  * `capture_fps`: integer, framerate to use during the recording phase;
  * `min_area`: integer, minimum area in the difference between frames to be considered as relevant motion (a frog moving);
  * `max_area`: integer, maximum area in the difference between frames to be considered as relevant motion (the camera shifting);
  * `max_areas`: integer, the number of areas in the difference between frames to be considered. 
* After the parameters are chosen it is just a matter of running:
```
python3 pi_frog.py --conf conf.json
```

## Authors

* Mário Artur Mira

## Version History

* 0.1
    * Initial Release

## References

Adrian Rosebrock, *Home surveillance and motion detection with the Raspberry Pi, Python, OpenCV, and Dropbox*, PyImageSearch, [https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/]https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/, accessed on 19 September 2020
