#!/usr/bin/env python
# -*- coding: utf8 -*-

import signal
import time
import threading
import re
import sys
import subprocess
import itchat
from itchat.content import TEXT, RECORDING
# import serial
import Motor
import Camera
import Speech
import Execute
from snowboy import snowboydecoder

sender = 'filehelper' # for wechat
snowboyEnable = False

motor = Motor.Motor()
camera = Camera.Camera()
speech = Speech.Speech()
execute = Execute.Execute()

def handler_sigint(signalnum, frame):
    print("process exit")
    exit(0)


# **************** commands callback **************************************
def commandImage():
    speech.Speech_play("./resources/camera.wav", "wav")
    fileName = camera.Camera_saveImage()
    itchat.send('@img@%s' %fileName, toUserName=sender)
    speech.Speech_play("./resources/saveImageDone.mp3", "mp3") # u"照片拍摄完成，已发送到微信"

def commandVideo():
    fileName = camera.Camera_saveVideo(3000)
    itchat.send('@vid@%s' %fileName, toUserName=sender)
    speech.Speech_play("./resources/saveVideoDone.mp3", "mp3") # u"视频拍摄完成，已发送到微信"

def parseAngle(recordText):
    angleStr = re.sub(r'\D', "", recordText) # parse number
    angle = int(angleStr)
    if angle > 90:
        angle = 90
    return angle

def commandCameraLeft(angle):
    def motorForwardThread(angle):
        motor.Motor_forward(angle)

    threading.Thread(target=motorForwardThread, args=(angle,)).start()
    fileName = camera.Camera_saveVideo(angle*115) # 0.02*4*(angle/0.7)*1000
    itchat.send('@vid@%s' %fileName, toUserName=sender)
    speech.Speech_play("./resources/cameraLeftDone.mp3", "mp3") # u"摄像头左转完成"

def commandCameraRight(angle):
    def motorBackwardThread(angle):
        motor.Motor_backward(angle)

    threading.Thread(target=motorBackwardThread, args=(angle,)).start()
    fileName = camera.Camera_saveVideo(angle*115) # 0.02*4*(angle/0.7)*1000
    itchat.send('@vid@%s' %fileName, toUserName=sender)
    speech.Speech_play("./resources/cameraRightDone.mp3", "mp3") # u"摄像头右转完成"

def commandCleanCache():
    subprocess.call("rm -f ./capture/*.jpg ./capture/*.mp4 ./capture/*.mp3 ./capture/*.wav ./capture/*.pcm", shell=True)
    subprocess.call("rm -f ./*.wav ./*.mp3", shell=True)
    speech.Speech_play("./resources/cleancacheDone.mp3", "mp3") # u"缓存清理完成"
'''
def parseInfrared(recordText):
    for k, v in tvInfraredCodes.items():
        if k in recordText:
            return v

def comamndTv(*infraredCode): # parse function return tuple
    for data in infraredCode:
        serial.send(data)
'''
def commandNotHitted(recordText):
    respText = speech.Speech_emotibot(recordText)
    respFile = speech.Speech_tts(respText)
    print("respText: %s" %respText)
    speech.Speech_play(respFile, "mp3")


# **************** itchat procedure **************************************
@itchat.msg_register([TEXT])
def text_reply(msg):
    global sender
    recordText = msg.text
    sender = msg['FromUserName']
    if msg['ToUserName'] == 'filehelper': # for test
        sender = 'filehelper'

    try:
        print("recordText: %s" %recordText)
        execute.process(recordText)
    except:
        print("text_reply error: ", sys.exc_info()[0])
    finally:
        sender = 'filehelper' # switch back to filehelper after friends procedure

@itchat.msg_register([RECORDING])
def recording_reply(msg):
    global sender
    sender = msg['FromUserName']
    if msg['ToUserName'] == 'filehelper':
        sender = 'filehelper'

    msg['Text'](msg['FileName']) # save mp3 file
    try:
        recordFile = speech.Speech_convertMp3ToPcm(msg['FileName'])
        recordText = speech.Speech_asr(recordFile, "pcm")
        print("recordText: %s" %recordText)
        execute.process(recordText)
    except:
        print("recording_reply error: ", sys.exc_info()[0])
    finally:
        sender = 'filehelper' # switch back to filehelper after friends procedure

def threadItChat():
    itchat.auto_login(enableCmdQR=2, hotReload=True)
    itchat.run()


# **************** record procedure **************************************
def threadRecord():
    while True:
        try:
            recordFile = speech.Speech_record()
            recordText = speech.Speech_asr(recordFile, "wav")
            print("recordText: %s" %recordText)
            execute.process(recordText)
        except:
            print("threadRecord error: ", sys.exc_info()[0])


# **************** snowboy procedure **************************************
def cbAudioRecorder(recordFile):
    try:
        recordText = speech.Speech_asr(recordFile, "wav")
        print("recordText: %s" %recordText)
        execute.process(recordText)
    except:
        print("cbAudioRecorder error: ", sys.exc_info()[0])

def threadSnowboy():
    detector = snowboydecoder.HotwordDetector("./resources/xiaohong.pmdl", sensitivity=0.5)
    detector.start(audio_recorder_callback=cbAudioRecorder)
    detector.terminate()


# key: hit words, value: v1-command process callback, v2-parameters parse callback
commands = {
(u"拍照", u"拍张照"):(commandImage,),
(u"拍视频", u"拍个视频"):(commandVideo,),
(u"左转",):(commandCameraLeft, parseAngle),
(u"右转",):(commandCameraRight, parseAngle),
(u"清缓存", u"清除缓存", u"清空缓存", u"清理缓存"):(commandCleanCache,)}
# (u"左边", u"右边", u"上边", u"下边", u"声音大", u"声音调大", u"声音小", u"声音调小",
# u"确定", u"返回", u"主页", u"开电视", u"关电视", u"关闭电视",):(comamndTv, parseInfrared)}

tvInfraredCodes = {
u"左":(0x01, 0x01, 0x01, 0x01, 0x01),
u"右":(0x01, 0x01, 0x01, 0x01, 0x01),
u"上":(0x01, 0x01, 0x01, 0x01, 0x01),
u"下":(0x01, 0x01, 0x01, 0x01, 0x01),
u"大":(0x01, 0x01, 0x01, 0x01, 0x01),
u"小":(0x01, 0x01, 0x01, 0x01, 0x01),
u"确定":(0x01, 0x01, 0x01, 0x01, 0x01),
u"返回":(0x01, 0x01, 0x01, 0x01, 0x01),
u"主页":(0x01, 0x01, 0x01, 0x01, 0x01),
u"开":(0x01, 0x01, 0x01, 0x01, 0x01),
u"关":(0x01, 0x01, 0x01, 0x01, 0x01)}


if __name__ == '__main__':
    print("process begin")
    signal.signal(signal.SIGINT, handler_sigint)

    for k, v in commands.items():
        execute.registerProcedure(k, v)
    execute.registerNotHittedProcedure(commandNotHitted)

    threading.Thread(target=threadItChat).start()
    if snowboyEnable:
        threading.Thread(target=threadSnowboy).start()
    else:
        threading.Thread(target=threadRecord).start()

