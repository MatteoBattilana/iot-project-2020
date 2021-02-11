import requests
import time
import json
import copy

json = {
    "serviceName": "",
    "serviceServiceList": [],
    "serviceType": ""
}

class CatalogAdapter:
    def __init__(self, serviceName, serviceServiceList, serviceType, onNewServiceId):
        self.__serviceName = serviceName
        self.__serviceServiceList = serviceServiceList
        self.__serviceType = serviceType
        self.__serviceID = ""
        self.__onNewServiceId = onNewServiceId
        json["serviceName"] = serviceName
        json["serviceServiceList"] = serviceServiceList
        json["serviceType"] = serviceType

    def getBroker(self):
        try:
            r = requests.get("http://127.0.0.1:8080/catalog/getBroker", json = json)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print("[PING][ERROR] Unable to get the broker address: " + str(e))

        return {}


    def sendPing(self):
        postBody = copy.copy(json)
        if self.__serviceID:
            postBody["serviceId"] = self.__serviceID

        try:
            r = requests.post("http://127.0.0.1:8080/catalog/", json = postBody)
            print("[PING][INFO] Sent ping to the catalog http://127.0.0.1:8080/catalog/")
            if r.status_code == 200:
                if r.json()['serviceId'] != self.__serviceID:
                    self.__onNewServiceId(r.json()['serviceId'])        #callback for new id
                self.__serviceID = r.json()['serviceId']
            else:
                print("[PING][ERROR] Unable to register " + self.__serviceName + " to the catalog\nError message + " + r.json()["error"]["message"])
        except Exception as e:
            print("[PING][ERROR] Unable to register " + self.__serviceName + " to the catalog\nError message + " + str(e))
