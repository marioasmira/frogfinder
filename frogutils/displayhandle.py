import RPi.GPIO as GPIO
import time

# each list displays one digit from 0-9
digit_array = [[0,0,0,0,0,0,1],\
        [1,0,0,1,1,1,1],\
        [0,0,1,0,0,1,0],\
        [0,0,0,0,1,1,0],\
        [1,0,0,1,1,0,0],\
        [0,1,0,0,1,0,0],\
        [0,1,0,0,0,0,0],\
        [0,0,0,1,1,1,1],\
        [0,0,0,0,0,0,0],\
        [0,0,0,0,1,0,0]]

def display(conf, val1, val2):
    # turn the two values into a list
    list1 = [int(x) for x in str(val1)]
    # if there's only one digit add a zero before
    if len(list1) < 2:
        list1.insert(0,0)
    list2 = [int(x) for x in str(val2)]
    # if there's only one digit add a zero before
    if len(list2) < 2:
        list2.insert(0,0)
    digit_list = list1 + list2

    # reset display
    for pin in conf["display_pins"]:
        GPIO.output(pin,True)
    for pin in conf["digit_pins"]:
        GPIO.output(pin,False)
    GPIO.output(conf["display_dot_pin"], True)

    for n in range(1, 1000):
        for pos in range(0, 4):
            GPIO.output(conf["digit_pins"][pos], True)
            val = digit_list[pos]

            for led in range(0, 7):
                GPIO.output(conf["display_pins"][led], digit_array[val][led])
            time.sleep(0.005)
            GPIO.output(conf["digit_pins"][pos], False)
