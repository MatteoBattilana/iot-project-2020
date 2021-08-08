import json
import threading
import time
import requests
import copy
import logging

# base structure to send during the ping, the serviceId is added only after a
# valid one i received
json = {}

# Module for managing the ping to the catalog
class Ping(threading.Thread):
    def __init__(self, pingTime, serviceServiceList, catalogAddress, serviceName, serviceType, serviceId, serviceSubType = None, groupId = None, devicePosition = None):
        threading.Thread.__init__(self)
        self._pingTime = pingTime
        self._catalogAddress = catalogAddress
        self._run = True
        json["serviceId"] = serviceId
        json["serviceName"] = serviceName
        json["serviceType"] = serviceType
        if serviceSubType is not None:
            json["serviceSubType"] = serviceSubType
        if groupId is not None:
            json["groupId"] = groupId
        if devicePosition is not None:
            json["devicePosition"] = devicePosition
        json["serviceServiceList"] = serviceServiceList


    # sending ping every self._pingTime s
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

    def setPingTime(self, pingTime):
        logging.debug("Ping time set to " + str(pingTime) + " s")
        self._pingTime = pingTime

    def setGroupId(self, groupId):
        logging.debug("GroupId set to " + groupId + " s")
        json["groupId"] = groupId


    def sendPing(self):
        postBody = copy.copy(json)

        try:
            r = requests.post(self._catalogAddress + "/ping", json = postBody)
            logging.debug("Sent ping to the catalog " + self._catalogAddress + "/ping")
            if r.status_code != 200:
                logging.error("Unable to register service to the catalog: " + r.json())
        except Exception as e:
            logging.error("Unable to register service to the catalog : " + str(e))
