import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
# turns on LED
def PIN_ON(gpio_pin):
    GPIO.output(gpio_pin, True)

# turns off LED
def PIN_OFF(gpio_pin):
    GPIO.output(gpio_pin, False)

class PinHandle():
    def __init__(self) -> None:
        pass

    def run(self, pars, queue):
        while True:
            target, on_off = queue.get()
            if on_off :
                PIN_ON(pars.get_pin(target))
            else:
                PIN_OFF(pars.get_pin(target))
            sleep(0.05)
