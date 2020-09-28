import RPi.GPIO as GPIO

# turns on LED
def LED_ON(gpio_pin):
    GPIO.output(gpio_pin, True)

# turns off LED
def LED_OFF(gpio_pin):
    GPIO.output(gpio_pin, False)

