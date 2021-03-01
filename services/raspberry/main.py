# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
from random import random
import threading
import json
import time

class Raspberry(threading.Thread):
    def __init__(self, pingTime, sensorSamplingTime, serviceList, deviceId, publishTopic):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList)
        self._mqtt = MQTTRetry(deviceId, self)
        self._sensorSamplingTime = sensorSamplingTime
        self._publishTopic = publishTopic
        self._isMQTTconnected = False

    def run(self):
        print("[RASPBERRY][INFO] Started")
        self._ping.start()
        self._mqtt.start()

        while True:
            if self._isMQTTconnected:
                #read sensors
                self._mqtt.publish(self._publishTopic, self._getRandomValues())
            time.sleep(self._sensorSamplingTime)

    def _getRandomValues(self):
        simulatedValues = []
        simulatedValues.append({
            'n': 'temperature',
            'u': 'celsius',
            't': time.time(),
            'v': random()
        })
        return {
            'bn': self._publishTopic,
            'e': simulatedValues
            }

    #MQTT callbacks
    def onMQTTConnected(self):
        self._isMQTTconnected = True
    def onMQTTConnectionError(self, error):
        self._isMQTTconnected = False
    def onMQTTMessageReceived(self, topic, message):
        pass


if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": settings['MQTTTopic'],
                    "type": "temperature"
                }
            ]
        }
    ]
    rpi = Raspberry(
            settings['pingTime'],
            settings['sensorSamplingTime'],
            availableServices,
            settings['deviceId'],
            settings['MQTTTopic']
            )
    rpi.start()
    rpi.join()
