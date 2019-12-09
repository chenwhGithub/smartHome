#!/usr/bin/env python
# -*- coding: utf8 -*-

import signal
import time
import threading
import itchat
from itchat.content import TEXT
import Motor
import Camera

motor = Motor.Motor()
camera = Camera.Camera()

def handler(signalnum, frame):
    print("exit procedure")
    exit(0)

@itchat.msg_register([TEXT])
def text_reply(msg):
    recv = msg.text
    if recv == "P":
        fileName = camera.Camera_saveImage()
        itchat.send('@img@%s' %fileName, toUserName=msg['FromUserName'])
        print("send success %s" %fileName)

def recvItChat():
    itchat.auto_login(enableCmdQR=2)
    itchat.run()

def motionDetect():
    while (True):
        isMoved = camera.Camera_checkMotion()
        if isMoved:
            camera.Camera_saveImage()
        time.sleep(1)

if __name__ == '__main__':
    print("begin procedure")
    signal.signal(signal.SIGINT, handler) # Ctrl + C

    itChatThreading = threading.Thread(target=recvItChat)
    itChatThreading.start()

    motionDetectThreading = threading.Thread(target=motionDetect)
    motionDetectThreading.start()
