import json
import os
import time
import uuid
import threading
from datetime import datetime


# Menager for services and devices, using lock
class ServiceManager():
    def __init__(self, retentionTimeout):
        self._lock = threading.Lock()
        self._retentionTimeout = retentionTimeout
        self._list = []

    # Clean the records in the list that have a lastUpdate that is higher than
    # the set retention time; this method is called by the catalog every 10 seconds
    def cleanOldServices(self):
        self._lock.acquire()
        for serv in self._list[:]:
            if time.time() - serv['lastUpdate'] > self._retentionTimeout:
                print("[CATALOG][INFO] Removed service: " + str(serv['serviceId']))
                self._list.remove(serv);
        self._lock.release()

    def searchById(self, id):
        for serv in self._list:
            if serv['serviceId'] == id:
                return serv
        return {}

    # Returns all the devices available
    def getAll(self):
        return self._list

    # Internal function to insert a service
    def _insertService(self, service, serviceName):
        self._lock.acquire()
        service['serviceId'] = serviceName + "-" + str(len(self._list))
        service['lastUpdate'] = time.time()
        self._list.append(service)
        self._lock.release()
        print("[CATALOG][INFO] Added service new service: " + str(service['serviceId']))
        return service

    def addService(self, service):
        # If the service is not in the list, it is simply added
        if "serviceId" not in service or self.searchById(service["serviceId"]) == {}:
            return self._insertService(service, service["serviceName"])

        # Otherwaise I update its information by keeping its id
        self._lock.acquire()
        for idx, serv in enumerate(self._list):
            if serv['serviceId'] == service["serviceId"]:
                service['lastUpdate'] = time.time()
                service['serviceId'] = service["serviceId"]
                self._list[idx] = service
        self._lock.release()

        print("[CATALOG][INFO] Updated service service with id: " + str(service['serviceId']))
        return service
