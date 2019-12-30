#!/usr/bin/env python
# -*- coding: utf8 -*-

# sudo apt-get install python3-pyaudio
# sudo pip3 install baidu-aip
# sudo pip3 install ffmpy
# sudo apt-get install ffmpeg
# sudo pip3 install pydub
# sudo pip3 install SpeechRecognition
# sudo apt-get install pulseaudio
# sudo apt-get install swig # for training_service.py xiaohong.pmdl
# sudo apt-get install libatlas-base-dev

import wave
from pyaudio import PyAudio, paInt16
from aip import AipSpeech
from pydub import AudioSegment
from pydub.playback import play
from ffmpy import FFmpeg
import speech_recognition as sr
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
    record_framePerBuf  = 1024

    # https://console.bce.baidu.com/ai/?_=1577239936502&fromai=1#/ai/speech/app/detail~appId=1406406
    AIP_APP_ID = '18101860'
    AIP_API_KEY = 'DKCHMqFyvqMQYHADBRRX45rc'
    AIP_SECRET_KEY = 'BGuCTGlYqUBA7t0fdADAV5RVah9ewc4l'

    # https://www.kancloud.cn/turing/www-tuling123-com/718227
    TULING_API_KEY = "875a2acbc70049d481a63f288b67adee"
    TULING_API_URL = "http://openapi.tuling123.com/openapi/api/v2"
    TULING_HEADERS = {'Content-Type': 'application/json;charset=UTF-8'}

    # http://console.developer.emotibot.com/api/ApiKey/documentation.php
    EMOTIBOT_API_ID = "ad470c115e2cd908d166eeea9c742c5b"
    EMOTIBOT_API_URL = "http://idc.emotibot.com/api/ApiKey/openapi.php"

    def __init__(self):
        # os.close(sys.stderr.fileno())
        self.capturePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture")
        self.client = AipSpeech(self.AIP_APP_ID, self.AIP_API_KEY, self.AIP_SECRET_KEY)
        self.pa = PyAudio()
        self.r = sr.Recognizer()
        self.mic = sr.Microphone(sample_rate=self.record_rate) # format:paInt16(deadcode)
        with self.mic as source:
            self.r.adjust_for_ambient_noise(source)

    def __del__(self):
        self.pa.terminate()

    # record from audio to wav
    def Speech_recordByPyaudio(self, recordSeconds):
        print("please say something")
        stream = self.pa.open(format=self.record_format, channels=self.record_channels, rate=self.record_rate, input=True, frames_per_buffer=self.record_framePerBuf)
        frames = []
        for i in range(int(self.record_rate/self.record_framePerBuf * recordSeconds)):
            data = stream.read(self.record_framePerBuf)
            frames.append(data)
        stream.stop_stream()
        stream.close()

        t = datetime.now()
        filename = self.capturePath + "/" + "WAV-%04d%02d%02d-%02d%02d%02d.wav" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.record_channels)
        wf.setsampwidth(self.pa.get_sample_size(self.record_format))
        wf.setframerate(self.record_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return filename

    # record from audio to wav
    def Speech_record(self):
        print("please say something")
        t = datetime.now()
        filename = self.capturePath + "/" + "WAV-%04d%02d%02d-%02d%02d%02d.wav" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        try:
            with self.mic as source:
                audio = self.r.listen(source)
            with open(filename, "wb") as fp:
                fp.write(audio.get_wav_data()) # channels:1
            return filename
        except:
            print("Speech_record error: ", sys.exc_info()[0])
            raise

    # asr from file to text, fileFormat:"wav"-for record, "pcm"-for itchat RECORDING
    def Speech_asr(self, fileName, fileFormat):
        try:
            with open(fileName, 'rb') as fp:
                data = fp.read()
            ret = self.client.asr(data, fileFormat, self.record_rate, {'dev_pid': 1536, })
            text = ret["result"][0]
            return text
        except:
            print("Speech_asr error: ", sys.exc_info()[0])
            raise

    # tts from text to mp3
    def Speech_tts(self, text):
        t = datetime.now()
        filename = self.capturePath + "/" + "MP3-%04d%02d%02d-%02d%02d%02d.mp3" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        try:
            result = self.client.synthesis(text, 'zh', 1, {'vol':7, 'per':0, 'spd':5, 'pit':5}) # per:0-women 1-man 3-duxiaoyao 4-duyaya
            with open(filename, 'wb') as fp:
                fp.write(result)
            return filename
        except:
            print("Speech_tts error: ", sys.exc_info()[0])
            raise

    # play from file to audio, fileFormat:"wav/mp3.."
    def Speech_play(self, fileName, fileFormat):
        try:
            audio = AudioSegment.from_file(fileName, format=fileFormat)
            play(audio)
        except:
            print("Speech_play error: ", sys.exc_info()[0])
            raise

    # get response from text
    def Speech_tuling(self, reqText):
        req = {
            "reqType": 0, # 0:text 1:picture 2:audio
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
            print("Speech_tuling error: ", sys.exc_info()[0])
            raise

    # get response from text
    def Speech_emotibot(self, reqText):
        req = {
            "cmd": "chat",
            "appid": self.EMOTIBOT_API_ID,
            "userid": "xiaoming",
            "text": reqText,
            "location": "hangzhou"
        }

        try:
            r = requests.post(self.EMOTIBOT_API_URL, params=req)
            jsondata = json.loads(r.text)
            respText = jsondata.get('data')[0].get('value')
            return respText
        except:
            print("Speech_emotibot error: ", sys.exc_info()[0])
            raise

    # convert mp3 to pcm, for itChat RECORDING
    def Speech_convertMp3ToPcm(self, srcFile):
        t = datetime.now()
        desFile = self.capturePath + "/" + "PCM-%04d%02d%02d-%02d%02d%02d.pcm" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        ff = FFmpeg(
            inputs = {srcFile: None},
            outputs = {desFile: '-acodec pcm_s16le -f s16le -ac 1 -ar 16000'}
        )
        ff.run()
        return desFile

    # convert from wav to mp3, reserved
    def Speech_convertWavToMp3(self, srcFile):
        t = datetime.now()
        desFile = self.capturePath + "/" + "MP3-%04d%02d%02d-%02d%02d%02d.mp3" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        audio = AudioSegment.from_file(srcFile, format="wav")
        audio.export(desFile, format="mp3")
        return desFile

    # convert from mp3 to wav, reserved
    def Speech_convertMp3ToWav(self, srcFile):
        t = datetime.now()
        desFile = self.capturePath + "/" + "WAV-%04d%02d%02d-%02d%02d%02d.wav" %(t.year, t.month, t.day, t.hour, t.minute, t.second)
        audio = AudioSegment.from_file(srcFile, format="mp3")
        audio.export(desFile, format="wav")
        return desFile
