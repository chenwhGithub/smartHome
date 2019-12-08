#!/usr/bin/env python
# -*- coding: utf8 -*-

import signal
import time
import Motor
import Camera

motor = Motor.Motor()
camera = Camera.Camera()

def handler(signalnum, frame):
    print("exit procedure")
    exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, handler) # Ctrl + C
    print("begin procedure")
    motor.Motor_forward(90)
    motor.Motor_stop()
    # motor.Motor_backward(90)
    # motor.Motor_stop()
    print("begin motion detect")
    while (True):
        isMoved = camera.Camera_checkMotion()
        if isMoved:
            camera.Camera_saveImage()
        time.sleep(1)
