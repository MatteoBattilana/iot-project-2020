# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
import cherrypy
from random import random
from commons.netutils import *
import threading
import json
import time

class Device(threading.Thread):
    exposed=True

    def __init__(self, pingTime, sensorSamplingTime, serviceList, deviceName, groupId, publishTopic, catalogAddress, sensorReader):
        threading.Thread.__init__(self)
        serviceList.append(
            {
                "serviceType": "REST",
                "serviceIP": NetworkUtils.getIp(),
                "servicePort": 8080,
                "endPoint": [
                    {
                        "type": "web",
                        "uri": "/",
                        "version": 1,
                        "parameter": []
                    }
                ]
            }
        )
        self._ping = Ping(pingTime, serviceList, catalogAddress, deviceName, "DEVICE", groupId, self)
        self._sensorSamplingTime = sensorSamplingTime
        self._publishTopic = publishTopic + groupId + "/"
        self._isMQTTconnected = False
        self._catalogAddress = catalogAddress
        self._deviceId = ""
        self._deviceName = deviceName
        self._mqtt = None
        self._run = True
        self._sensorReader = sensorReader


    def stop(self):
        if self._isMQTTconnected and self._mqtt is not None:
            self._mqtt.stop()
        self._ping.stop()
        self._run = False
        self.join()

    def run(self):
        print("[INFO] Started")
        self._ping.start()

        lastTime = time.time()
        while self._run:
            if self._isMQTTconnected and time.time() - lastTime > self._sensorSamplingTime:
                #read sensors
                self._mqtt.publish(self._publishTopic + self._deviceId, self._getRandomValues())
                lastTime = time.time()
            time.sleep(1)
        print ("[INFO] Stopped sensor read")

    def _getRandomValues(self):
        simulatedValues = self._sensorReader.readSensors()
        return {
            'bn': self._deviceId,
            'e': simulatedValues
            }


    # Catalog new id callback
    def onNewCatalogId(self, newId):
        print("[INFO] New id from catalog: " + newId)
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

    # REST API
    def GET(self, *uri, **parameter):
        if len(uri) == 0:
            return json.dumps({"message": self._deviceName + " API endpoint"}, indent=4)
        return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
