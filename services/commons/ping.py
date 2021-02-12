import sys, os
sys.path.insert(0, os.path.abspath('..'))
import json
import threading
import time
import requests
import copy

json = {
    "serviceName": "",
    "serviceServiceList": [],
    "serviceType": ""
}

# Module for services
class Ping(threading.Thread):
    def __init__(self, pingTime, serviceType, serviceServiceList, serviceName, onNewServiceIdCallback = None):
        threading.Thread.__init__(self)
        self.__pingTime = pingTime
        self.__serviceName = serviceName
        self.__serviceID = ""
        self.__onNewServiceIdCallback = onNewServiceIdCallback
        json["serviceName"] = serviceName
        json["serviceServiceList"] = serviceServiceList
        json["serviceType"] = serviceType

    def run(self):
        print("[SERVICE][INFO] Started ping every " + str(self.__pingTime) + " s")
        while True:
            self.sendPing()
            time.sleep(self.__pingTime)

    def sendPing(self):
        postBody = copy.copy(json)
        if self.__serviceID:
            # If the id is available, I send it. In the case my sessions is expired
            # a new one is given
            postBody["serviceId"] = self.__serviceID

        try:
            r = requests.post("http://127.0.0.1:8080/catalog/ping", json = postBody)
            print("[PING][INFO] Sent ping to the catalog http://127.0.0.1:8080/catalog/ping")
            if r.status_code == 200:
                if r.json()['serviceId'] != self.__serviceID and self.__onNewServiceIdCallback != None:
                    self.__onNewServiceIdCallback(r.json()['serviceId'])        #callback for new id
                self.__serviceID = r.json()['serviceId']
            else:
                print("[PING][ERROR] Unable to register " + self.__serviceName + " to the catalog: " + r.json()["error"]["message"])
        except Exception as e:
            print("[PING][ERROR] Unable to register " + self.__serviceName + " to the catalog: " + str(e))
