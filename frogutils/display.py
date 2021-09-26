import RPi.GPIO as GPIO
import time
from frogutils.parameters import Parameters
from multiprocessing import Pipe


class Display:
    """Class to control the 4 digit 7 segment display

    Attributes
    ----------
    digit_array : 2 dimentional array of int
        10x7 array that holds the pattern to display each digit with 7 segments.

    Methods
    -------
    digits(pars, pipe)
        Reads output from the pipe and displays the information on the display.

    """

    digit_array = [
        [1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0],
        [1, 1, 0, 1, 1, 0, 1],
        [1, 1, 1, 1, 0, 0, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [1, 0, 1, 1, 0, 1, 1],
        [1, 0, 1, 1, 1, 1, 1],
        [1, 1, 1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 0, 1, 1],
    ]

    def __init__(self) -> None:
        pass

    def digits(self, pars: Parameters, pipe: Pipe) -> None:
        """Reads output from the pipe and displays the information on the display

        Parameters
        ----------
        pars : Parameter
            The parameter object from which to get GPIO pin information.
        pipe : Pipe
            The pipe from which to receive the information to display.

        """

        # reset display
        for pin in pars.get_pin("display_pins"):
            GPIO.output(pin, False)
        for pin in pars.get_pin("digit_pins"):
            GPIO.output(pin, True)
        GPIO.output(pars.get_pin("display_dot_pin"), False)
        # default values, shouldn't be needed
        digit_list = [2, 0, 7, 0]

        while True:
            # make sure there is something in the pipe
            # otherwise, continue showing the same
            if pipe.poll():
                # retrieve the two values from the pipe
                val1, val2 = pipe.recv()

                # turn the two values into a list
                list1 = [int(x) for x in str(val1)]
                # if there's only one digit add a zero before
                if len(list1) < 2:
                    list1.insert(0, 0)

                list2 = [int(x) for x in str(val2)]
                # if there's only one digit add a zero before
                if len(list2) < 2:
                    list2.insert(0, 0)
                digit_list = list1 + list2

            # stay on for 100 * 0.005 = 0.5 seconds
            for n in range(101):
                for pos in range(4):
                    GPIO.output(pars.get_pin("digit_pins")[pos], False)
                    val = digit_list[pos]

                    for led in range(0, 7):
                        GPIO.output(
                            pars.get_pin("display_pins")[led],
                            self.digit_array[val][led],
                        )
                    time.sleep(0.005)
                    GPIO.output(pars.get_pin("digit_pins")[pos], True)
