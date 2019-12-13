#!/usr/bin/python

# www.raspberrypi.org/phpBB3/viewtopic.php?f=43&t=45235
# install PIL: "sudo apt-get install python-imaging-tk"

# import io
import StringIO
import subprocess
import os
import time
import threading
from datetime import datetime
from PIL import Image

class Camera:

    # motion detection settings:
    threshold = 64                              # how much a pixel change to be marked as changed
    sensitivity = 2000                          # how many changed pixels to trigger capture an image
    filepath = "/home/pi/smartHome/capture"     # location of folder to save photos and vedios

    # settings of the photos to save
    saveWidth   = 1296
    saveHeight  = 972
    saveQuality = 50 # 0 to 100

    # test-image settings
    testWidth   = 100
    testHeight  = 75
    buffer1 = None
    buffer2 = None

    mutex = threading.Lock()

    def __init__(self):
        self.buffer1 = self.Camera_captureTestImage()

    def Camera_captureTestImage(self):
        command = "raspistill -w %s -h %s -t 700 -e bmp -n -o -" %(self.testWidth, self.testHeight)
        # imageData = io.StringIO()
        imageData = StringIO.StringIO()
        self.mutex.acquire()
        imageData.write(subprocess.check_output(command, shell=True))
        self.mutex.release()
        imageData.seek(0)
        im = Image.open(imageData)
        buf = im.load()
        imageData.close()
        return buf

    def Camera_saveImage(self):
        time = datetime.now()
        filename = self.filepath + "/" + "IMG-%04d%02d%02d-%02d%02d%02d.jpg" %(time.year, time.month, time.day, time.hour, time.minute, time.second)
        self.mutex.acquire()
        subprocess.call("raspistill -w %s -h %s -t 700 -e jpg -q %s -n -o %s" %(self.saveWidth, self.saveHeight, self.saveQuality, filename), shell=True)
        self.mutex.release()
        print("save success %s" %filename)
        return filename

    def Camera_checkMotion(self):
        changedPixels = 0
        self.buffer2 = self.Camera_captureTestImage()
        for x in xrange(0, self.testWidth):
            for y in xrange(0, self.testHeight):
                pixdiff = abs(self.buffer1[x,y][1] - self.buffer2[x,y][1]) # just check green channel as it's the highest quality channel
                if pixdiff > self.threshold:
                    changedPixels += 1
            if (changedPixels > self.sensitivity): # scan one line of image then check sensitivity for movement
                self.buffer1 = self.buffer2
                return True
        self.buffer1 = self.buffer2
        return False

    def Camera_waitProcessDone(self):
        self.mutex.acquire()