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
import serial
import Motor
import Camera
import AiBaidu
import Execute
from snowboy import snowboydecoder


# **************** commands callback **************************************
def commandImage():
    ai.Speech_play("./resources/camera.wav", "wav")
    fileName = camera.Camera_saveImage()
    itchat.send('@img@%s' %fileName, toUserName=sender)
    ai.Speech_play("./resources/saveImageDone.mp3", "mp3") # u"照片拍摄完成，已发送到微信"

def commandVideo():
    fileName = camera.Camera_saveVideo(3000)
    itchat.send('@vid@%s' %fileName, toUserName=sender)
    ai.Speech_play("./resources/saveVideoDone.mp3", "mp3") # u"视频拍摄完成，已发送到微信"

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
    ai.Speech_play("./resources/cameraLeftDone.mp3", "mp3") # u"摄像头左转完成"

def commandCameraRight(angle):
    def motorBackwardThread(angle):
        motor.Motor_backward(angle)

    threading.Thread(target=motorBackwardThread, args=(angle,)).start()
    fileName = camera.Camera_saveVideo(angle*115) # 0.02*4*(angle/0.7)*1000
    itchat.send('@vid@%s' %fileName, toUserName=sender)
    ai.Speech_play("./resources/cameraRightDone.mp3", "mp3") # u"摄像头右转完成"

def commandCleanCache():
    subprocess.call("rm -f ./capture/*.jpg ./capture/*.mp4 ./capture/*.mp3 ./capture/*.wav ./capture/*.pcm", shell=True)
    subprocess.call("rm -f ./*.wav ./*.mp3", shell=True)
    ai.Speech_play("./resources/cleancacheDone.mp3", "mp3") # u"缓存清理完成"

def parseInfrared(recordText):
    for k, v in tvInfraredCodes.items():
        if any(word in recordText for word in k):
            return v

def comamndTv(*infraredCode): # parse function return tuple
    str = ''
    for item in infraredCode:
        temp = hex(item) # 0x6 or 0x6a
        if len(temp) == 3:
            str = str + "0" + temp[2]
        else:
            str = str + temp[2] + temp[3]
    sendData = bytes.fromhex(str) # sendData <class 'bytes'> b'\x01#\xab\xff\n'
    serialAma0.write(sendData)

def commandNotHitted(recordText):
    respText = ai.Robot_emotibot(recordText)
    respFile = ai.Speech_tts(respText)
    print("respText: %s" %respText)
    ai.Speech_play(respFile, "mp3")


# **************** itchat procedure ***************************************
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
        recordFile = ai.Speech_convertMp3ToPcm(msg['FileName'])
        recordText = ai.Speech_asr(recordFile, "pcm")
        print("recordText: %s" %recordText)
        execute.process(recordText)
    except:
        print("recording_reply error: ", sys.exc_info()[0])
    finally:
        sender = 'filehelper' # switch back to filehelper after friends procedure

def threadItChat():
    itchat.auto_login(enableCmdQR=2, hotReload=True)
    itchat.run()


# **************** record procedure ***************************************
def threadRecord():
    while True:
        try:
            recordFile = ai.Speech_record()
            recordText = ai.Speech_asr(recordFile, "wav")
            print("recordText: %s" %recordText)
            execute.process(recordText)
        except:
            print("threadRecord error: ", sys.exc_info()[0])


# **************** snowboy procedure **************************************
def cbAudioRecorder(recordFile):
    try:
        recordText = ai.Speech_asr(recordFile, "wav")
        print("recordText: %s" %recordText)
        execute.process(recordText)
    except:
        print("cbAudioRecorder error: ", sys.exc_info()[0])

def threadSnowboy():
    detector = snowboydecoder.HotwordDetector("./resources/xiaohong.pmdl", sensitivity=0.5)
    detector.start(audio_recorder_callback=cbAudioRecorder)
    detector.terminate()


# **************** serial procedure ***************************************
def threadSerial():
    while True:
        data = serialAma0.read()
        recvData = data.hex()
        print("recvData", recvData) # recvData <class 'str'> 00~ff


# **************** Ctrl+C signal procedure ********************************
def handler_sigint(signalnum, frame):
    serialAma0.close()
    print("process stop")
    exit(0)


if __name__ == '__main__':
    print("process begin")

    # key: hit words, value: v1-command process callback, v2-parameters parse callback
    commands = {
        (u"拍照", u"拍张照"):(commandImage,),
        (u"拍视频", u"拍个视频"):(commandVideo,),
        (u"左转",):(commandCameraLeft, parseAngle),
        (u"右转",):(commandCameraRight, parseAngle),
        (u"清缓存", u"清除缓存", u"清空缓存", u"清理缓存"):(commandCleanCache,),
        (u"左边", u"向左", u"往左", u"右边", u"向右", u"往右", u"上边", u"向上", u"往上", u"下边", u"向下", u"往下",
         u"声音大点", u"声音小点", u"确定", u"返回", u"主页", u"打开电视", u"关闭电视",
         "←", "→", "↑", "↓", "+", "-"):(comamndTv, parseInfrared)}

    tvInfraredCodes = {
        # data1: a1-default serial address
        # data2: f1-send infrared codes
        #        f2-change serial address
        #        f3-change baud
        # data3/4: user code low/high 8b
        # data5: command code
        (u"左", "←"):(0xa1, 0xf1, 0x4c, 0x65, 0x10),
        (u"右", "→"):(0xa1, 0xf1, 0x4c, 0x65, 0x11),
        (u"上", "↑"):(0xa1, 0xf1, 0x4c, 0x65, 0x0b),
        (u"下", "↓"):(0xa1, 0xf1, 0x4c, 0x65, 0x0e),
        (u"大", "+"):(0xa1, 0xf1, 0x4c, 0x65, 0x15),
        (u"小", "-"):(0xa1, 0xf1, 0x4c, 0x65, 0x1c),
        (u"确定",):(0xa1, 0xf1, 0x4c, 0x65, 0x0d),
        (u"返回",):(0xa1, 0xf1, 0x4c, 0x65, 0x1d),
        (u"主页",):(0xa1, 0xf1, 0x4c, 0x65, 0x16),
        (u"开", u"关"):(0xa1, 0xf1, 0x4c, 0x65, 0x0a)}

    signal.signal(signal.SIGINT, handler_sigint) # Ctrl+C

    sender = 'filehelper' # for wechat
    snowboyEnable = False # select snowboy or speech_recognition
    serialAma0 = serial.Serial("/dev/ttyAMA0", 9600)
    if serialAma0.isOpen():
        print("/dev/ttyAMA0 open success")

    motor = Motor.Motor()
    camera = Camera.Camera()
    ai = AiBaidu.AiBaidu()
    execute = Execute.Execute()

    for k, v in commands.items():
        execute.registerProcedure(k, v)
    execute.registerNotHittedProcedure(commandNotHitted)

    threading.Thread(target=threadSerial).start()
    threading.Thread(target=threadItChat).start()
    if snowboyEnable:
        threading.Thread(target=threadSnowboy).start()
    else:
        threading.Thread(target=threadRecord).start()

