import json
import threading
import time
import requests
import copy

# base structure to send during the ping, the serviceId is added only after a
# valid one i received
json = {
    "serviceServiceList": [],
    "serviceName": ""
}

# Module for managing the ping to the catalog
class Ping(threading.Thread):
    def __init__(self, pingTime, serviceServiceList, catalogAddress, serviceName, serviceType, notifier = None):
        threading.Thread.__init__(self)
        self._pingTime = pingTime
        self._serviceID = None
        self._catalogAddress = catalogAddress
        self._notifier = notifier
        json["serviceServiceList"] = serviceServiceList
        json["serviceType"] = serviceType
        json["serviceName"] = serviceName

    # sending ping every self._pingTime s
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
            r = requests.post(self._catalogAddress + "/ping", json = postBody)
            print("[PING][INFO] Sent ping to the catalog " + self._catalogAddress + "/ping")
            if r.status_code == 200:
                if r.json()['serviceId'] != self._serviceID and self._notifier is not None:
                    self._notifier.onNewCatalogId(r.json()['serviceId'])        #callback for new id
                self._serviceID = r.json()['serviceId']
            else:
                print("[PING][ERROR] Unable to register service to the catalog: " + r.json()["error"]["message"])
        except Exception as e:
            print("[PING][ERROR] Unable to register service to the catalog 1: " + str(e))
