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
from aip import AipSpeech, AipOcr, AipFace
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
import base64

class AiBaidu:

    record_format       = paInt16
    record_rate         = 16000
    record_channels     = 1
    record_framePerBuf  = 1024

    # https://console.bce.baidu.com/ai/?_=1577239936502&fromai=1#/ai/speech/app/detail~appId=1406406
    AIP_APP_ID = '18101860' # for speech, ocr
    AIP_API_KEY = 'DKCHMqFyvqMQYHADBRRX45rc'
    AIP_SECRET_KEY = 'BGuCTGlYqUBA7t0fdADAV5RVah9ewc4l'

    AIP_APP_ID_FACE = '18461652' # for face
    AIP_API_KEY_FACE = 'tw82n23q5EfbexbioxEj4htE'
    AIP_SECRET_KEY_FACE = 'FBc3855Vob1zkuddFGK5ZgZQ1qTQvQz0'

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
        self.clientSpeech = AipSpeech(self.AIP_APP_ID, self.AIP_API_KEY, self.AIP_SECRET_KEY)
        self.clientOcr = AipOcr(self.AIP_APP_ID, self.AIP_API_KEY, self.AIP_SECRET_KEY)
        self.clientFace = AipFace(self.AIP_APP_ID_FACE, self.AIP_API_KEY_FACE, self.AIP_SECRET_KEY_FACE)
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
            ret = self.clientSpeech.asr(data, fileFormat, self.record_rate, {'dev_pid': 1537, })
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
            result = self.clientSpeech.synthesis(text, 'zh', 1, {'vol':7, 'per':0, 'spd':5, 'pit':5}) # per:0-women 1-man 3-duxiaoyao 4-duyaya
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


    # get response from text
    def Robot_tuling(self, reqText):
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
            resp = requests.request("post", self.TULING_API_URL, json=req, headers=self.TULING_HEADERS)
            respJson = json.loads(resp.text)
            respText = respJson["results"][0]["values"]["text"]
            return respText
        except:
            print("Robot_tuling error: ", sys.exc_info()[0])
            raise

    # get response from text
    def Robot_emotibot(self, reqText):
        req = {
            "cmd": "chat",
            "appid": self.EMOTIBOT_API_ID,
            "userid": "xiaoming",
            "text": reqText,
            "location": "hangzhou"
        }

        try:
            resp = requests.request("post", self.EMOTIBOT_API_URL, params=req)
            respJson = json.loads(resp.text)
            respText = respJson["data"][0]["value"]
            return respText
        except:
            print("Robot_emotibot error: ", sys.exc_info()[0])
            raise


    # get words from image
    def Ocr_getWords(self, fileName):
        with open(fileName, 'rb') as fp:
            image = fp.read()
        try:
            resp = self.clientOcr.basicGeneral(image);
            words = ""
            for item in resp["words_result"]:
                words += item["words"]
            return words
        except:
            print("Ocr_getWords error: ", sys.exc_info()[0])
            raise

    def Ocr_getIdCard(self, fileNameFront, fileNameBack):
        card = {}
        if fileNameFront:
            with open(fileNameFront, 'rb') as fpFront:
                imageFront = fpFront.read()
            try:
                respFront = self.clientOcr.idcard(imageFront, "front");
                card["name"] = respFront["words_result"][u"姓名"]["words"]
                card["gender"] = respFront["words_result"][u"性别"]["words"]
                card["nation"] = respFront["words_result"][u"民族"]["words"]
                card["birth"] = respFront["words_result"][u"出生"]["words"]
                card["address"] = respFront["words_result"][u"住址"]["words"]
                card["id"] = respFront["words_result"][u"公民身份号码"]["words"]
            except:
                print("Ocr_getIdCard front error: ", sys.exc_info()[0])
                raise
        if fileNameBack:
            with open(fileNameBack, 'rb') as fpBack:
                imageBack = fpBack.read()
            try:
                respBack = self.clientOcr.idcard(imageBack, "back");
                card["issue"] = respBack["words_result"][u"签发机关"]["words"]
                card["beginDate"] = respBack["words_result"][u"签发日期"]["words"]
                card["EndDate"] = respBack["words_result"][u"失效日期"]["words"]
            except:
                print("Ocr_getIdCard back error: ", sys.exc_info()[0])
                raise
        return card

    def Ocr_getPlateLicense(self, fileName):
        with open(fileName, 'rb') as fp:
            image = fp.read()
        try:
            resp = self.clientOcr.licensePlate(image);
            return resp["words_result"]["number"]
        except:
            print("Ocr_getPlateLicense error: ", sys.exc_info()[0])
            raise

    def Ocr_getForm(self, fileName, resultType="excel"):
        with open(fileName, 'rb') as fp:
            image = fp.read()
        try:
            options = {}
            options["result_type"] = resultType # excel/json
            resp = self.clientOcr.tableRecognition(image, options)
            return resp["result"]["result_data"]
        except:
            print("Ocr_getPlateLicense error: ", sys.exc_info()[0])
            raise


    def Face_detect(self, fileName):
        with open(fileName, 'rb') as fp:
            data = fp.read()

        image = base64.b64encode(data).decode()
        imageType = "BASE64"
        options = {}
        options["face_field"] = "age,beauty,gender,emotion"
        face = {}
        try:
            resp = self.clientFace.detect(image, imageType, options)
            if resp["error_code"] == 0:
                face["token"] = resp["result"]["face_list"][0]["face_token"]
                face["gender"] = resp["result"]["face_list"][0]["gender"]["type"]
                face["age"] = resp["result"]["face_list"][0]["age"]
                face["beauty"] = resp["result"]["face_list"][0]["beauty"]
                face["emotion"] = resp["result"]["face_list"][0]["emotion"]["type"]
            return face
        except:
            print("Face_detect error: ", sys.exc_info()[0])
            raise

    def Face_addGroup(self, groupId):
        resp = self.clientFace.groupAdd(groupId)
        return resp["error_code"] # success:0 fail:other

    def Face_deleteGroup(self, groupId):
        resp = self.clientFace.groupDelete(groupId)
        return resp["error_code"] # success:0 fail:other

    def Face_getGroupList(self):
        groupList = []
        resp = self.clientFace.getGroupList()
        if resp["error_code"] == 0:
            groupList = resp["result"]["group_id_list"]
        return groupList

    def Face_getUserList(self, groupId):
        userList = []
        resp = self.clientFace.getGroupUsers(groupId)
        if resp["error_code"] == 0:
            userList = resp["result"]["user_id_list"]
        return userList

    def Face_deleteUser(self, groupId, userId):
        resp = self.clientFace.deleteUser(groupId, userId)
        return resp["error_code"] # success:0 fail:other

    def Face_addFace(self, fileName, groupId, userId):
        with open(fileName, 'rb') as fp:
            data = fp.read()

        image = base64.b64encode(data).decode()
        imageType = "BASE64"
        faceToken = ""
        try:
            resp = self.clientFace.addUser(image, imageType, groupId, userId)
            if resp["error_code"] == 0:
                faceToken = resp["result"]["face_token"]
            return faceToken
        except:
            print("Face_addFace error: ", sys.exc_info()[0])
            raise

    def Face_deleteFace(self, groupId, userId, faceToken):
        resp = self.clientFace.faceDelete(userId, groupId, faceToken)
        return resp["error_code"] # success:0 fail:other

    def Face_getFaceList(self, groupId, userId):
        faceTokens = []
        resp = self.clientFace.faceGetlist(userId, groupId)
        if resp["error_code"] == 0:
            for face in resp["result"]["face_list"]:
                faceTokens.append(face["face_token"])
        return faceTokens

    # groupIdList:"group1,group2", without blank
    def Face_serch(self, fileName, groupIdList, userId=None):
        with open(fileName, 'rb') as fp:
            data = fp.read()

        image = base64.b64encode(data).decode()
        imageType = "BASE64"
        options = {}
        if userId:
            options["user_id"] = userId
        ret = {}
        try:
            resp = self.clientFace.search(image, imageType, groupIdList, options)
            if resp["error_code"] == 0:
                ret["face_token"] = resp["result"]["face_token"]
                ret["group_id"] = resp["result"]["user_list"][0]["group_id"]
                ret["user_id"] = resp["result"]["user_list"][0]["user_id"]
                ret["score"] = resp["result"]["user_list"][0]["score"]
            return ret
        except:
            print("Face_serch error: ", sys.exc_info()[0])
            raise

    def Face_match(self, fileName1, fileName2):
        with open(fileName1, 'rb') as fp1:
            data1 = fp1.read()
        with open(fileName2, 'rb') as fp2:
            data2 = fp2.read()

        image1 = base64.b64encode(data1).decode()
        image2 = base64.b64encode(data2).decode()
        imageType = "BASE64"
        score = 0.0
        resp = self.clientFace.match([
            {'image': image1, 'image_type': imageType},
            {'image': image2, 'image_type': imageType}])
        if resp["error_code"] == 0:
            score = resp["result"]["score"]
        return score


