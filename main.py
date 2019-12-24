#!/usr/bin/env python
# -*- coding: utf8 -*-
import signal
import time
import threading
import re
import itchat
from itchat.content import TEXT
import Motor
import Camera
import Hcsr04

cameraPos = 0 # camera position
CAMERA_MAX_LEFT = -120
CAMERA_MAX_RIGHT = 120

motor = Motor.Motor()
camera = Camera.Camera()
hcsr04 = Hcsr04.Hcsr04()

def handler_sigint(signalnum, frame):
    if (cameraPos < 0):
        motor.Motor_backward(0 - cameraPos)
    if (cameraPos > 0):
        motor.Motor_forward(cameraPos)
    print("procedure exit")
    exit(0)

def saveAndSendImage(sender):
    fileName = camera.Camera_saveImage()
    itchat.send('@img@%s' %fileName, toUserName=sender)
    print("send success %s" %fileName)

def saveAndSendVideo(sender, mSecond):
    fileName = camera.Camera_saveVideo(mSecond)
    itchat.send('@vid@%s' %fileName, toUserName=sender)
    print("send success %s" %fileName)

def motorForwardThread(angle):
    motor.Motor_forward(angle)

def motorBackwardThread(angle):
    motor.Motor_backward(angle)

@itchat.msg_register([TEXT])
def text_reply(msg):
    global cameraPos
    recvMsg = msg.text
    sender = msg['FromUserName']
    if (recvMsg == "P") or (recvMsg == "p"):
        saveAndSendImage(sender)
    elif (recvMsg == "V") or (recvMsg == "v"):
        itchat.send('please wait...', toUserName=sender)
        saveAndSendVideo(sender, 5000) # default video 5s
    else:
        pattern = re.compile(r"(L|l|R|r)([1-9][0-9]?)\Z")
        matchObjs = pattern.match(recvMsg)
        if matchObjs:
            angle = int(matchObjs.group(2))
            if (matchObjs.group(1) == "l") or (matchObjs.group(1) == "L"):
                if (cameraPos > CAMERA_MAX_LEFT):
                    if (cameraPos - angle < CAMERA_MAX_LEFT):
                        angle = cameraPos - CAMERA_MAX_LEFT
                    t1 = threading.Thread(target=motorForwardThread, args=(angle,))
                    t1.start()
                    cameraPos -= angle
                    itchat.send('please wait...', toUserName=sender)
                    saveAndSendVideo(sender, angle*115) # 0.02*4*(angle/0.7)*1000
            else:
                if (cameraPos < CAMERA_MAX_RIGHT):
                    if (cameraPos + angle > CAMERA_MAX_RIGHT):
                        angle = CAMERA_MAX_RIGHT - cameraPos
                    t2 = threading.Thread(target=motorBackwardThread, args=(angle,))
                    t2.start()
                    cameraPos += angle
                    itchat.send('please wait...', toUserName=sender)
                    saveAndSendVideo(sender, angle*115) # 0.02*4*(angle/0.7)*1000

def itChatThread():
    itchat.auto_login(enableCmdQR=2, hotReload=True)
    itchat.run()

def motionDetectThread():
    while True:
        isMoved = camera.Camera_checkMotion()
        if isMoved:
            camera.Camera_saveImage()
        time.sleep(2)

def distanceThread():
    while True:
        distance = hcsr04.HCSR04_getDistance()
        print("distance(cm): %d" %distance)
        time.sleep(2)

if __name__ == '__main__':
    print("procedure begin")
    signal.signal(signal.SIGINT, handler_sigint)

    itChatThreading = threading.Thread(target=itChatThread)
    itChatThreading.start()
    motionDetectThreading = threading.Thread(target=motionDetectThread)
    motionDetectThreading.start()
    distanceThreading = threading.Thread(target=distanceThread)
    distanceThreading.start()
