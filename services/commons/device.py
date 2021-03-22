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

    def __init__(self, sensorReader, settingsManager, isBehindNat = False):
        threading.Thread.__init__(self)
        self._sensorReader = sensorReader
        self._settingsManager = settingsManager
        serviceList = [
            {
                "serviceType": "MQTT",
                "endPoint": [
                    {
                        "topic": self._settingsManager.getField('MQTTTopic'),
                        "type": "temperature"
                    }
                ]
            },
            {
                "serviceType": "REST",
                "serviceIP": NetworkUtils.getIp(isBehindNat),
                "servicePort": 8080,
                "endPoint": [
                    {
                        "type": "web",
                        "uri": "/",
                        "version": 1,
                        "parameter": []
                    },
                    {
                        "type": "configuration",
                        "uri": "/setPingTime",
                        "version": 1,
                        "parameter": [{"name": "pingTime", "unit": "integer"}]
                    },
                    {
                        "type": "configuration",
                        "uri": "/setGroupId",
                        "version": 1,
                        "parameter": [{"name": "groupId", "unit": "string"}]
                    }
                ]
            }
        ]
        self._ping = Ping(

                int(self._settingsManager.getField('pingTime')),
                serviceList,
                self._settingsManager.getField('catalogAddress'),
                self._settingsManager.getField('deviceName'),
                "DEVICE",
                self._settingsManager.getField('groupId'),
                self
            )
        self._sensorSamplingTime = int(self._settingsManager.getField('sensorSamplingTime'))
        self._publishTopic = self._settingsManager.getField('MQTTTopic') + self._settingsManager.getField('groupId') + "/"
        self._catalogAddress = self._settingsManager.getField('catalogAddress')
        self._isMQTTconnected = False
        self._deviceId = ""
        self._deviceName = self._settingsManager.getField('deviceName')
        self._mqtt = None
        self._run = True


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
        if uri[0] == "setPingTime":
            pingTime = int(parameter['pingTime'])
            self._ping.setPingTime(pingTime)
            self._settingsManager.updateField("pingTime", pingTime)
            return json.dumps({"pingTime": pingTime}, indent=4)
        if uri[0] == "setGroupId":
            self._ping.setGroupId(parameter['groupId'])
            self._settingsManager.updateField("groupId", parameter['groupId'])
            return json.dumps({"groupId": parameter['groupId']}, indent=4)


        cherrypy.response.status = 404
        return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
