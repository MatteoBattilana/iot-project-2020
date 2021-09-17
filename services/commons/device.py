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
import logging

# This is a common class to both the simulated and the RASPBERRY device
# used to perform the ping and read the sensors
class Device(threading.Thread):
    exposed=True

    def __init__(self, sensorReader, settingsManager, isExternal = False):
        threading.Thread.__init__(self)
        self._sensorReader = sensorReader
        self._settingsManager = settingsManager
        # setting the list of service that the device is able to give
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
                "serviceIP": NetworkUtils.getIp(isExternal),
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
                        "parameter": [{"name": "groupId", "unit": "string"}, {"name": "pin", "unit": "string"}]
                    },
                    {
                        "type": "configuration",
                        "uri": "/deleteGroupId",
                        "version": 1,
                        "parameter": []
                    },
                    {
                        "type": "configuration",
                        "uri": "/setPosition",
                        "version": 1,
                        "parameter": [{"name": "position", "unit": "string"}]
                    },
                    {
                        "type": "action",
                        "uri": "/forceSensorSampling",
                        "version": 1,
                        "parameter": []
                    },
                    {
                        "type": "action",
                        "uri": "/getSensorValues",
                        "version": 1,
                        "parameter": []
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
                self._settingsManager.getField('serviceId'),
                "RASPBERRY",
                self._settingsManager.getFieldOrDefault('groupId', ''),
                self._settingsManager.getField('devicePosition')
            )
        self._sensorSamplingTime = int(self._settingsManager.getField('sensorSamplingTime'))
        self._catalogAddress = self._settingsManager.getField('catalogAddress')
        self._deviceId = self._settingsManager.getField('serviceId')
        self._deviceName = self._settingsManager.getField('deviceName')
        self._mqtt = None
        self._devicePosition = self._settingsManager.getField('devicePosition')
        self._run = True

    # method use to stop the ping, the mqtt service
    # it is basically used from the cherrypy engine that allows to restart the
    # service after a code change without lunching again the docker service
    def stop(self):
        if self._mqtt is not None:
            self._mqtt.stop()
        self._ping.stop()
        self._run = False
        self.join()

    # method used to read and publish the sensor values following this
    # structure: {"bn": "MatteoHome_119923952/RASPBERRY-A1", "e": [{"n": "co2", "u": "ppm",
    # "t": 1631890231.7521343, "v": 406.7}, {"n": "temperature", "u": "celsius", "t": 1631890231.7521546,
    # "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1631890231.7521625, "v": 51}], "sensor_position": "internal"}
    def _publishSampledSensor(self):
        simulatedValues = self._sensorReader.readSensors()
        groupId = self._settingsManager.getFieldOrDefault('groupId', '')
        if simulatedValues != [] and groupId:
            readValues = {
                'bn': groupId + "/" + self._deviceId,
                'e': simulatedValues,
                'sensor_position': self._devicePosition
                }

            logging.info("Publishing sensor values")
            publishTopic = self._settingsManager.getField('MQTTTopic') + groupId + "/"
            # publish the json to the MQTT broker
            self._mqtt.publish(publishTopic + self._deviceId, readValues)
            return readValues
        else:
            logging.info("Sensors not available")
            return {}

    # method use to start the thread
    def run(self):
        logging.debug("Started")
        self._ping.start()

        self._mqtt = MQTTRetry(self._deviceId, self, self._catalogAddress)
        self._mqtt.start()

        lastTime = time.time()
        while self._run:
            if time.time() - lastTime > self._sensorSamplingTime:
                #read sensors
                self._publishSampledSensor()
                lastTime = time.time()

            time.sleep(1)
        logging.debug("Stopped sensor read")


    #MQTT callbacks
    def onMQTTConnected(self):
        self._isMQTTconnected = True
    def onMQTTConnectionError(self, error):
        self._isMQTTconnected = False
    def onMQTTMessageReceived(self, topic, message):
        pass

    # REST API
    def GET(self, *uri, **parameter):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if len(uri) == 0:
            # Base GET rest endpoint
            return json.dumps({"message": self._deviceName + " API endpoint"}, indent=4)
        if uri[0] == "setPingTime":
            # configure the ping time
            pingTime = int(parameter['pingTime'])
            self._ping.setPingTime(pingTime)
            self._settingsManager.updateField("pingTime", pingTime)
            return json.dumps({"pingTime": pingTime}, indent=4)
            return json.dumps({"groupId": parameter['groupId']}, indent=4)
        if uri[0] == "forceSensorSampling":
            # force a sensor read
            sent = self._publishSampledSensor()
            return json.dumps({"status": 'ok', 'mqtt-payload': sent}, indent=4)
        if uri[0] == "setGroupId":
            # set and change the groupId of the device
            # in this case it must be restarted the ping and updated the settings file
            if self._settingsManager.getFieldOrDefault('pin', '') == parameter['pin']:
                groupId = parameter['groupId']
                self._ping.setGroupId(groupId)
                self._settingsManager.updateField("groupId", groupId)
                return json.dumps({"groupId": groupId}, indent=4)
            else:
                cherrypy.response.status = 401
                return json.dumps({"status": 'error'}, indent=4)
        if uri[0] == "deleteGroupId":
            # set to empty the groupId
            groupId = ''
            self._ping.setGroupId(groupId)
            self._settingsManager.updateField("groupId", groupId)
            return json.dumps({"groupId": groupId}, indent=4)
        if uri[0] == "setPosition":
            # configure the device position, such as internal or external
            position = parameter['position']
            if "internal" in position or "external" in position:
                self._ping.setPosition(position)
                self._devicePosition = position
                self._settingsManager.updateField("devicePosition", position)
                return json.dumps({"devicePosition": position}, indent=4)
            else:
                cherrypy.response.status = 401
                return json.dumps({"status": 'error', 'message': 'Wrong position'}, indent=4)
        if uri[0] == "getSensorValues":
            # used to only read the sensor and not trigger a MQTT publish
            return json.dumps(self._sensorReader.readSensors(), indent=4)

        cherrypy.response.status = 404
        return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
