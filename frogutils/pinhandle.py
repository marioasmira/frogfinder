from multiprocessing.queues import Queue
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

# these two functions are not inside the class
# because they need to be used for setup in the parameters

# turns on PIN
def PIN_ON(gpio_pin: int) -> None:
    """Turns the provided GPIO pin to HIGH

    Parameters
    ----------
    gpio_pin : int
        The GPIO pin to be set to HIGH.

    """

    GPIO.output(gpio_pin, True)


# turns off PIN
def PIN_OFF(gpio_pin: int) -> None:
    """Turns the provided GPIO pin to LOW

    Parameters
    ----------
    gpio_pin : int
        The GPIO pin to be set to LOW.

    """
    GPIO.output(gpio_pin, False)


class PinHandle:
    """Class to handle the output to GPIO pins

    Methods
    -------
    run(pars, queue)
        Receives GPIO pin information from a queue and turns them to HIGH or LOW until interrupted.
    """

    def __init__(self) -> None:
        pass

    def run(self, pars, queue: Queue) -> None:
        """Receives GPIO pin information from a queue and turns them to HIGH or LOW until interrupted

        Parameters
        ----------
        pars : Parameters
            The parameter object from which to collect GPIO information.
        queue : Queue
            The queue from which to receive which GPIO pins to interact with.

        """

        while True:
            target, on_off = queue.get()
            if on_off:
                PIN_ON(pars.get_pin(target))
            else:
                PIN_OFF(pars.get_pin(target))
            sleep(0.05)
