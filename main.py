#!/usr/bin/env python
# -*- coding: utf8 -*-
import signal
import time
import threading
import re
import subprocess
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
        saveAndSendVideo(sender, 3000)
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

def processCommand(command):
    respText = ""
    respFile = ""
    # if any(word in command for word in [u"主页", u"向左", u"向右", u"向上", u"向下", u"确定", u"返回", u"开机", u"关机"]):
    if any(word in command for word in [u"拍照", u"拍张照"]):
        speech.Speech_play("./resources/camera.wav", "wav")
        saveAndSendImage("filehelper")
        respText = u"照片拍摄成功，已发送到微信传输助手"
        respFile = "./resources/savePicDone.mp3"
    elif any(word in command for word in [u"拍视频", u"拍个视频"]):
        saveAndSendVideo("filehelper", 3000)
        respText = u"视频拍摄成功，已发送到微信传输助手"
        respFile = "./resources/saveVidDone.mp3"
    elif any(word in command for word in ["左转"]):
        angle = re.sub(r'\D', "", command)
        motorForwardThread(int(angle))
        respText = u"左转" + angle + u"度完成"
        respFile = speech.Speech_tts(respText)
    elif any(word in command for word in ["右转"]):
        angle = re.sub(r'\D', "", command)
        motorBackwardThread(int(angle))
        respText = u"右转" + angle + u"度完成"
        respFile = speech.Speech_tts(respText)
    elif any(word in command for word in [u"清缓存", u"清除缓存", u"清空缓存", u"清理缓存"]):
        subprocess.call("rm -f ./capture/*.jpg ./capture/*.mp4 ./capture/*.mp3 ./capture/*.wav ./capture/*.pcm", shell=True)
        subprocess.call("rm -f ./*.wav ./*.mp3", shell=True)
        respText = u"缓存清理完成"
        respFile = "./resources/cleancacheDone.mp3"
    else:
        respText = speech.Speech_emotibot(command)
        respFile = speech.Speech_tts(respText)

    return respText, respFile

def recordThread():
    while True:
        try:
            recordFile = speech.Speech_record()
            recordText = speech.Speech_asr(recordFile, "wav")
            speech.Speech_play(snowboydecoder.DETECT_DONG, "wav")
            print("recordText: %s" %recordText)
            respText, respFile = processCommand(recordText)
            if respText:
                print("respText: %s" %respText)
            if respFile:
                speech.Speech_play(respFile, "mp3")
        except:
            print("recordThread error: ", sys.exc_info()[0])

def audioRecorderCallback(fname):
    recordText = speech.Speech_asr(fname, "wav")
    print("recordText: %s" %recordText)

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