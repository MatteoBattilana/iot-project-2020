import json
import threading
import time
import requests
import copy
import logging

# base structure to send during the ping, the serviceId is added only after a
# valid one i received.
# The structure is the following:
#{
#    "serviceName": "SIMULATED-DEVICE",
#    "serviceType": "DEVICE",
#    "serviceSubType": "RASPBERRY",
#    "groupId": "home1",
#    "devicePosition": "internal",
#    "serviceServiceList": [
#      {
#        "serviceType": "MQTT",
#        "endPoint": [
#          {
#            "topic": "/iot-programming-2343/",
#            "type": "temperature"
#          }
#        ]
#      },
#      {
#        "serviceType": "REST",
#        "serviceIP": "172.20.0.4",
#        "servicePort": 8080,
#        "endPoint": [
#          {
#            "type": "web",
#            "uri": "/",
#            "version": 1,
#            "parameter": [
#
#            ]
#          },
#          {
#            "type": "configuration",
#            "uri": "/setPingTime",
#            "version": 1,
#            "parameter": [
#              {
#                "name": "pingTime",
#                "unit": "integer"
#              }
#            ]
#          },
#          {
#            "type": "configuration",
#            "uri": "/setGroupId",
#            "version": 1,
#            "parameter": [
#              {
#                "name": "groupId",
#                "unit": "string"
#              }
#            ]
#          },
#          {
#            "type": "action",
#            "uri": "/forceSensorSampling",
#            "version": 1,
#            "parameter": [
#
#            ]
#          }
#        ]
#      }
#    ],
#    "serviceId": "SIMULATED-DEVICE-2",
#    "lastUpdate": 1627895704.1240659
#  }

json = {}

# Module for managing the ping to the catalog every pingTime
class Ping(threading.Thread):
    def __init__(self, pingTime, serviceServiceList, catalogAddress, serviceName, serviceType, serviceId, serviceSubType = None, groupId = None, devicePosition = None):
        threading.Thread.__init__(self)
        self._pingTime = pingTime
        self._catalogAddress = catalogAddress
        self._run = True
        json["serviceId"] = serviceId
        json["serviceName"] = serviceName
        json["serviceType"] = serviceType
        # if the service is not a device
        if serviceSubType:
            json["serviceSubType"] = serviceSubType
        # if the service is a device
        if groupId:
            json["groupId"] = groupId

        # if the service is a device
        if devicePosition:
            json["devicePosition"] = devicePosition
        json["serviceServiceList"] = serviceServiceList


    # sending ping every self._pingTime seconds
    def run(self):
        logging.debug("Started ping every " + str(self._pingTime) + " s")
        lastTime = 0
        while self._run:
            if time.time() - lastTime > self._pingTime:
                self.sendPing()
                lastTime = time.time()
            time.sleep(1)
        logging.debug("Stopped ping")

    def stop(self):
        self._run = False
        self.join()

    # used to change the ping time from outside the class
    def setPingTime(self, pingTime):
        logging.debug("Ping time set to " + str(pingTime) + " s")
        self._pingTime = pingTime

    # used to change the groupId from outside the class
    def setGroupId(self, groupId):
        logging.debug("GroupId set to " + groupId)
        json["groupId"] = groupId
        self.sendPing()

    # used to change the position of the device from outside the class
    def setPosition(self, position):
        logging.debug("Position set to " + position)
        json["devicePosition"] = position
        self.sendPing()

    # method that actually sends the ping to the catalog by creating in real time
    # the json body
    def sendPing(self):
        postBody = copy.copy(json)

        try:
            r = requests.post(self._catalogAddress + "/ping", json = postBody)
            logging.debug("Sent ping to the catalog " + self._catalogAddress + "/ping")
            if r.status_code != 200:
                logging.error("Unable to register service to the catalog: " + r.json())
        except Exception as e:
            logging.error("Unable to register service to the catalog : " + str(e))
