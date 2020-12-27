import requests
import threading
import time
import json
import copy

json = {
    "serviceName": "",
    "serviceServiceList": [],
    "serviceType": ""
}

class Ping(threading.Thread):
    def __init__(self, pingTime, serviceName, serviceServiceList, serviceType):
        threading.Thread.__init__(self)
        self.__pingTime = pingTime
        self.__serviceName = serviceName
        self.__serviceServiceList = serviceServiceList
        self.__serviceType = serviceType
        self.__serviceID = ""
        json["serviceName"] = serviceName
        json["serviceServiceList"] = serviceServiceList
        json["serviceType"] = serviceType

    def run(self):
        while 1:
            postBody = copy.copy(json)
            if self.__serviceID:
                postBody["serviceId"] = self.__serviceID

            r = requests.post("http://127.0.0.1:8080/catalog/", json = postBody)
            print("[PING][INFO] Sent ping")
            if r.status_code == 200:
                self.__serviceID = r.json()['serviceId']
            else:
                print("[PING][ERROR] Unable to register " + self.__serviceName + " to the catalog\nError message + " + r.json()["error"]["message"])
            time.sleep(self.__pingTime)
