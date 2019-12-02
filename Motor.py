# ULN2003-pin   Pi-pin
# 5V            2(5V)
# GND           6(GND)
# IN1           11(GPIO17)
# IN2           12(GPIO18)
# IN3           13(GPIO27)
# IN4           15(GPIO22)

import RPi.GPIO as GPIO
import time

class Motor:

    IN1 = 11
    IN2 = 12
    IN3 = 13
    IN4 = 15
    DELAY = 0.01

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        GPIO.setup(self.IN3, GPIO.OUT)
        GPIO.setup(self.IN4, GPIO.OUT)

    def __SetStep(self, w1, w2, w3, w4):
        GPIO.output(self.IN1, w1)
        GPIO.output(self.IN2, w2)
        GPIO.output(self.IN3, w3)
        GPIO.output(self.IN4, w4)

    # step angle, one pulse(1/8 beats): 5.625=360/64
    # 5.625*2*4=45, 45*8=360, 360*64=one circle
    # one time for loop: 5.625*2*4/64=0.7
    def Motor_forward(self, angles):
        loops = int(angles/0.7)
        for i in range(loops):
            self.__SetStep(1, 0, 0, 0)
            time.sleep(self.DELAY)
            self.__SetStep(0, 1, 0, 0)
            time.sleep(self.DELAY)
            self.__SetStep(0, 0, 1, 0)
            time.sleep(self.DELAY)
            self.__SetStep(0, 0, 0, 1)
            time.sleep(self.DELAY)

    def Motor_backward(self, angles):
        loops = int(angles/0.7)
        for i in range(loops):
            self.__SetStep(0, 0, 0, 1)
            time.sleep(self.DELAY)
            self.__SetStep(0, 0, 1, 0)
            time.sleep(self.DELAY)
            self.__SetStep(0, 1, 0, 0)
            time.sleep(self.DELAY)
            self.__SetStep(1, 0, 0, 0)
            time.sleep(self.DELAY)

    def Motor_stop(self):
        self.__SetStep(0, 0, 0, 0)

