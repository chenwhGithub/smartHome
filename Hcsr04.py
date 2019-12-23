# HC-SR04-pin   Pi-pin
# 5V            4(5V)
# GND           9(GND)
# Trig          16(GPIO23)
# Echo          18(GPIO24)

import RPi.GPIO as GPIO
import time

class Hcsr04:

    Trig = 16
    Echo = 18

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.Trig, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.Echo, GPIO.IN)

    def HCSR04_getDistance(self):
        GPIO.output(self.Trig, True)
        time.sleep(0.000015) # 15us pulse
        GPIO.output(self.Trig, False)

        while not GPIO.input(self.Echo): # start recording, waiting init high level
            pass
        start = time.time()

        while GPIO.input(self.Echo): # end recording, waiting response low level
            pass
        end=time.time()

        distance = round((end-start)*17000) # cm, (end-start)*340/2*100
        return distance
