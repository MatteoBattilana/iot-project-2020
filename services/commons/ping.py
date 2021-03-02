import sys, os
sys.path.insert(0, os.path.abspath('..'))
import json
import threading
import time
import requests
import copy

json = {
    "serviceServiceList": [],
    "serviceName": ""
}

# Module for services
class Ping(threading.Thread):
    def __init__(self, pingTime, serviceServiceList, catalogAddress, serviceName, onNewCatalogIdCallback = None):
        threading.Thread.__init__(self)
        self._pingTime = pingTime
        self._serviceID = ""
        self._catalogAddress = catalogAddress
        self._onNewCatalogIdCallback = onNewCatalogIdCallback
        json["serviceServiceList"] = serviceServiceList
        json["serviceName"] = serviceName

    def run(self):
        print("[PING][INFO] Started ping every " + str(self._pingTime) + " s")
        while True:
            self.sendPing()
            time.sleep(self._pingTime)

    def sendPing(self):
        postBody = copy.copy(json)
        if self._serviceID:
            # If the id is available, I send it. In the case my sessions is expired
            # a new one is given
            postBody["serviceId"] = self._serviceID

        try:
            r = requests.post(self._catalogAddress + "/ping", json = postBody)        # TODO: change to relative
            print("[PING][INFO] Sent ping to the catalog " + self._catalogAddress + "/ping")
            if r.status_code == 200:
                if r.json()['serviceId'] != self._serviceID and self._onNewCatalogIdCallback != None:
                    self._onNewCatalogIdCallback(r.json()['serviceId'])        #callback for new id
                self._serviceID = r.json()['serviceId']
            else:
                print("[PING][ERROR] Unable to register service to the catalog: " + r.json()["error"]["message"])
        except Exception as e:
            print("[PING][ERROR] Unable to register service to the catalog: " + str(e))
