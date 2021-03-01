import sys, os
sys.path.insert(0, os.path.abspath('..'))
import json
import threading
import time
import requests
import copy

json = {
    "serviceServiceList": []
}

# Module for services
class Ping(threading.Thread):
    def __init__(self, pingTime, serviceServiceList, onNewCatalogIdCallback = None):
        threading.Thread.__init__(self)
        self.__pingTime = pingTime
        self.__serviceID = ""
        self.__onNewCatalogIdCallback = onNewCatalogIdCallback
        json["serviceServiceList"] = serviceServiceList

    def run(self):
        print("[PING][INFO] Started ping every " + str(self.__pingTime) + " s")
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
            r = requests.post("http://catalog:8080/catalog/ping", json = postBody)        # TODO: change to relative
            print("[PING][INFO] Sent ping to the catalog http://catalog:8080/catalog/ping")
            if r.status_code == 200:
                if r.json()['serviceId'] != self.__serviceID and self.__onNewCatalogIdCallback != None:
                    self.__onNewCatalogIdCallback(r.json()['serviceId'])        #callback for new id
                self.__serviceID = r.json()['serviceId']
            else:
                print("[PING][ERROR] Unable to register service to the catalog: " + r.json()["error"]["message"])
        except Exception as e:
            print("[PING][ERROR] Unable to register service to the catalog: " + str(e))
