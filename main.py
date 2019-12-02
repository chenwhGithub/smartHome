#!/usr/bin/env python
# -*- coding: utf8 -*-

import Motor

motor = Motor.Motor()

if __name__ == '__main__':
    motor.Motor_forward(90)
    motor.Motor_stop()
    motor.Motor_backward(90)
    motor.Motor_stop()
    print("exit procedure")
