#!/usr/bin/env python
# -*- coding: utf8 -*-

# sudo apt-get install python3-pyaudio
# sudo pip3 install baidu-aip
# sudo pip3 install ffmpy
# sudo apt-get install ffmpeg
# sudo pip3 install pydub

import wave
from pyaudio import PyAudio, paInt16
from aip import AipSpeech
from pydub import AudioSegment
from ffmpy import FFmpeg
import requests
import json
import os
import sys
import time
from datetime import datetime

class Speech:

    record_format       = paInt16
    record_rate         = 16000
    record_channels     = 1
    record_width        = 2 # get_sample_size(paInt16)
    record_framePerBuf  = 1024
    record_filepath     = "/home/pi/smartHome/capture"

    # https://console.bce.baidu.com/ai/?_=1577239936502&fromai=1#/ai/speech/app/detail~appId=1406406
    AIP_APP_ID = '18101860'
    AIP_API_KEY = 'DKCHMqFyvqMQYHADBRRX45rc'
    AIP_SECRET_KEY = 'BGuCTGlYqUBA7t0fdADAV5RVah9ewc4l'

    # https://www.kancloud.cn/turing/www-tuling123-com/718227
    TULING_API_KEY = "875a2acbc70049d481a63f288b67adee"
    TULING_API_URL = "http://openapi.tuling123.com/openapi/api/v2"
    TULING_HEADERS = {'Content-Type': 'application/json;charset=UTF-8'}

    def __init__(self):
        # os.close(sys.stderr.fileno())
        self.pa = PyAudio()
        self.client = AipSpeech(self.AIP_APP_ID, self.AIP_API_KEY, self.AIP_SECRET_KEY)

    def __del__(self):
        self.pa.terminate()

    # output-wav
    def Speech_recordAudio(self, recordSeconds):
        print("please say something")
        stream = self.pa.open(format=self.record_format, channels=self.record_channels, rate=self.record_rate,
                              input=True, frames_per_buffer=self.record_framePerBuf)
        frames = []
        for i in range(int(self.record_rate/self.record_framePerBuf * recordSeconds)):
            data = stream.read(self.record_framePerBuf)
            frames.append(data)
        stream.stop_stream()
        stream.close()

        t = datetime.now()
        filename = self.record_filepath + "/" + "WAV-%04d%02d%02d-%02d%02d%02d.wav" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.record_channels)
        wf.setsampwidth(self.record_width)
        wf.setframerate(self.record_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print("record success %s" %filename)
        return filename

    # input-wav
    def Speech_playAudio(self, filename):
        stream = self.pa.open(format=self.record_format, channels=self.record_channels, rate=self.record_rate,
                              output=True, frames_per_buffer=self.record_framePerBuf)
        wf = wave.open(filename, 'rb')
        data = wf.readframes(self.record_framePerBuf)
        while data != '':
            stream.write(data)
            data = wf.readframes(self.record_framePerBuf)
        stream.stop_stream()
        stream.close()
        wf.close()

    # input-wav/pcm, format-"wav/pcm"
    def Speech_getAsr(self, filename, format):
        try:
            with open(filename, 'rb') as fp:
                data = fp.read()
            ret = self.client.asr(data, format, 16000, {'dev_pid': 1536, })
            text = ret["result"][0]
            return text
        except:
            print("Speech_getAsr error")
            return None

    # output-wav
    def Speech_getTts(self, text):
        result  = self.client.synthesis(text, 'zh', 1, {'vol': 5, 'per':0,})
        if not isinstance(result, dict):
            t = datetime.now()
            filename = self.record_filepath + "/" + "WAV-%04d%02d%02d-%02d%02d%02d.wav" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
            with open(filename, 'wb') as fp:
                fp.write(result)
            print("getTts success %s" %filename)
            return filename
        else:
            print("Speech_getTts error")
            return None

    def Speech_getRespFromTuling(self, reqText):
        req = {
            "reqType": 0, # 0-text 1-picture 2-audio
            "perception": {
                "inputText": {
                    "text": reqText
                },
                "selfInfo": {
                    "location": {
                        "city": "hangzhou",
                        "province": "zhejiang",
                        "street": "dongxin street"
                    }
                }
            },
            "userInfo": {
                "apiKey": self.TULING_API_KEY,
                "userId": "xiaoming"
            }
        }

        try:
            response = requests.request("post", self.TULING_API_URL, json=req, headers=self.TULING_HEADERS)
            response_dict = json.loads(response.text)
            respText = response_dict["results"][0]["values"]["text"]
            return respText
        except:
            print("Speech_getRespFromTuling error")
            return None

    # input-wav output-mp3
    def Speech_convertWavToMp3(self, sourceFile):
        sound = AudioSegment.from_file(sourceFile, format="wav")
        t = datetime.now()
        desFile = self.record_filepath + "/" + "MP3-%04d%02d%02d-%02d%02d%02d.mp3" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        sound.export(desFile, format="mp3")
        return desFile

    # input-mp3 output-wav
    def Speech_convertMp3ToWav(self, sourceFile):
        t = datetime.now()
        desFile = self.record_filepath + "/" + "WAV-%04d%02d%02d-%02d%02d%02d.wav" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        sound = AudioSegment.from_file(sourceFile, format="mp3")
        sound.export(desFile, format="wav")
        return desFile

    # input-mp3 output-pcm, for itChat RECORDING process
    def Speech_convertMp3ToPcm(self, sourceFile):
        t = datetime.now()
        desFile = self.record_filepath + "/" + "PCM-%04d%02d%02d-%02d%02d%02d.pcm" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        ff = FFmpeg(
            inputs = {sourceFile: None},
            outputs = {desFile: '-acodec pcm_s16le -f s16le -ac 1 -ar 16000'}
        )
        ff.run()
        return desFile
