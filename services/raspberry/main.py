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
    def __init__(self, pingTime, sensorSamplingTime, serviceList, deviceName, publishTopic, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, deviceName, "DEVICE", self)
        self._sensorSamplingTime = sensorSamplingTime
        self._publishTopic = publishTopic
        self._isMQTTconnected = False
        self._catalogAddress = catalogAddress
        self._deviceId = ""
        self._mqtt = None

    def run(self):
        print("[RASPBERRY][INFO] Started")
        self._ping.start()

        while True:
            if self._isMQTTconnected:
                #read sensors
                self._mqtt.publish(self._publishTopic + self._deviceId, self._getRandomValues())
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
            'bn': self._deviceId,
            'e': simulatedValues
            }

    # Catalog new id callback
    def onNewCatalogId(self, newId):
        print("[RASPBERRY][INFO] New id from catalog: " + newId)
        self._deviceId = newId
        self._isMQTTconnected = False
        if self._mqtt is not None:
            self._mqtt.stop()

        self._mqtt = MQTTRetry(self._deviceId, self, self._catalogAddress)
        self._mqtt.start()

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
            settings['deviceName'],
            settings['MQTTTopic'],
            settings['catalogAddress']
            )
    rpi.start()
    rpi.join()
