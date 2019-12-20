#!/usr/bin/env python
# -*- coding: utf8 -*-
import signal
import time
import threading
import itchat
from itchat.content import TEXT
import Motor
import Camera
import re

motor = Motor.Motor()
camera = Camera.Camera()

def handler_sigint(signalnum, frame):
    camera.Camera_waitProcessDone()
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
    recvMsg = msg.text
    sender = msg['FromUserName']
    if (recvMsg == "P") or (recvMsg == "p"):
        saveAndSendImage(sender)
    elif (recvMsg == "V") or (recvMsg == "v"):
        itchat.send('please wait...', toUserName=sender)
        saveAndSendVideo(sender, 5000)
    else:
        pattern = re.compile(r"(L|l|R|r)([1-9][0-9]?)\Z") # l50 or r30
        matchObjs = pattern.match(recvMsg)
        if matchObjs:
            angle = int(matchObjs.group(2))
            if (matchObjs.group(1) == "l") or (matchObjs.group(1) == "L"):
                t1 = threading.Thread(target=motorForwardThread, args=(angle,))
                t1.start()
            else:
                t2 = threading.Thread(target=motorBackwardThread, args=(angle,))
                t2.start()
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

if __name__ == '__main__':
    print("procedure begin")
    signal.signal(signal.SIGINT, handler_sigint) # Ctrl + C

    itChatThreading = threading.Thread(target=itChatThread)
    itChatThreading.start()
    motionDetectThreading = threading.Thread(target=motionDetectThread)
    motionDetectThreading.start()
