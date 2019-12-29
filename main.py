#!/usr/bin/env python
# -*- coding: gbk -*-
import signal
import time
import threading
import re
import itchat
from itchat.content import TEXT, RECORDING
import Motor
import Camera
import Hcsr04
import Speech
from snowboy import snowboydecoder


cameraPos = 0
CAMERA_MAX_LEFT = -120
CAMERA_MAX_RIGHT = 120

motor = Motor.Motor()
camera = Camera.Camera()
hcsr04 = Hcsr04.Hcsr04()
speech = Speech.Speech()

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
    if msg['ToUserName'] == 'filehelper': # for test
        sender = 'filehelper'
    if (recvMsg == "P") or (recvMsg == "p"):
        saveAndSendImage(sender)
    elif (recvMsg == "V") or (recvMsg == "v"):
        itchat.send('please wait...', toUserName=sender)
        saveAndSendVideo(sender, 5000)
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

@itchat.msg_register([RECORDING])
def recording_reply(msg):
    sender = msg['FromUserName']
    if msg['ToUserName'] == 'filehelper': # for test
        sender = 'filehelper'
    msg['Text'](msg['FileName']) # save mp3 file
    reqFile = speech.Speech_convertMp3ToPcm(msg['FileName'])
    reqText = speech.Speech_asr(reqFile, "pcm")
    print("reqText: %s" %reqText)
    respText = speech.Speech_emotibot(reqText)
    print("respText: %s" %respText)
    itchat.send(respText, toUserName=sender)

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

def recordThread():
    while True:
        recordFile = speech.Speech_record()
        recordText = speech.Speech_asr(recordFile, "wav")
        print("recordText: %s" %recordText)
        ttsFile = None
        if any(word in recordText for word in ["拍照", "拍照片", "拍张照", "拍张照片"]):
            speech.Speech_play("./resources/camera.wav", "wav")
            saveAndSendImage("filehelper")
            respText = "照片拍摄成功，已发送到微信传输助手"
            ttsFile = "./resources/savePicDone.mp3"
        elif any(word in recordText for word in ["拍视频", "拍个视频"]):
            saveAndSendVideo("filehelper", 5000)
            respText = "视频拍摄成功，已发送到微信传输助手"
            ttsFile = "./resources/saveVidDone.mp3"
        elif any(word in recordText for word in ["左转", "向左"]):
            angle = re.sub(r'\D', "", recordText)
            motorForwardThread(int(angle))
            respText = "左转" + angle + "度完成"
            ttsFile = speech.Speech_tts(respText)
        elif any(word in recordText for word in ["右转", "向右"]):
            angle = re.sub(r'\D', "", recordText)
            motorBackwardThread(int(angle))
            respText = "右转" + angle + "度完成"
            ttsFile = speech.Speech_tts(respText)
        else:
            respText = speech.Speech_emotibot(recordText)
            ttsFile = speech.Speech_tts(respText)
        print("respText: %s" %respText)
        speech.Speech_play(ttsFile, "mp3")

def audioRecorderCallback(fname):
    recordText = speech.Speech_asr(fname, "wav")
    print("recordText: %s" %recordText)
    if any(word in recordText for word in ["拍照", "拍照片", "拍张照", "拍张照片"]):
        speech.Speech_play("./resources/camera.wav", "wav")
        saveAndSendImage("filehelper")
        respText = "照片拍摄成功，已发送到微信传输助手"
    elif any(word in recordText for word in ["拍视频", "拍个视频"]):
        saveAndSendVideo("filehelper", 5000)
        respText = "视频拍摄成功，已发送到微信传输助手"
    elif any(word in recordText for word in ["左转", "向左"]):
        angle = re.sub(r'\D', "", recordText)
        motorForwardThread(int(angle))
        respText = "左转" + angle + "度完成"
    elif any(word in recordText for word in ["右转", "向右"]):
        angle = re.sub(r'\D', "", recordText)
        motorBackwardThread(int(angle))
        respText = "右转" + angle + "度完成"
    else:
        respText = speech.Speech_emotibot(recordText)
    print("respText: %s" %respText)
    ttsFile = speech.Speech_tts(respText)
    speech.Speech_play(ttsFile, "mp3")

def detectedCallback(): # hit hotword
    speech.Speech_play("./resources/zaine.mp3", "mp3")

def snowboyThread():
    detector = snowboydecoder.HotwordDetector("./resources/xiaohong.pmdl", sensitivity=0.5)
    detector.start(detected_callback=detectedCallback, audio_recorder_callback=audioRecorderCallback)
    detector.terminate()

if __name__ == '__main__':
    print("procedure begin")
    signal.signal(signal.SIGINT, handler_sigint)

    itChatThreading = threading.Thread(target=itChatThread)
    itChatThreading.start()
    motionDetectThreading = threading.Thread(target=motionDetectThread)
    motionDetectThreading.start()
    distanceThreading = threading.Thread(target=distanceThread)
    distanceThreading.start()
    recordThreading = threading.Thread(target=recordThread)
    recordThreading.start()
    snowboyThreading = threading.Thread(target=snowboyThread)
    snowboyThreading.start()