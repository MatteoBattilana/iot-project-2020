import json
import os
import time
import uuid
import threading
from datetime import datetime
import logging


# Menager for services and devices, using lock
class ServiceManager():
    def __init__(self, retentionTimeout):
        self._lock = threading.Lock()
        self._retentionTimeout = retentionTimeout
        self._list = []
        self._currentIndex = 0

    # Clean the records in the list that have a lastUpdate that is higher than
    # the set retention time; this method is called by the catalog every 10 seconds
    def cleanOldServices(self):
        self._lock.acquire()
        for serv in self._list[:]:
            if time.time() - serv['lastUpdate'] > self._retentionTimeout:
                logging.debug("Removed service: " + str(serv['serviceId']))
                self._list.remove(serv)
        self._lock.release()

    def searchById(self, id):
        for serv in self._list:
            if 'serviceId' in serv and serv['serviceId'] == id:
                return serv
        return {}

    def searchByServiceType(self, type):
        ret = []
        for serv in self._list:
            if serv['serviceType'] == type:
                ret.append(serv)
        return ret

    def searchByServiceSubType(self, subtype):
        ret = []
        for serv in self._list:
            if 'serviceSubType' in serv and serv['serviceSubType'] == subtype:
                ret.append(serv)
        return ret

    def searchByGroupId(self, id):
        ret = []
        for serv in self._list:
            if 'groupId' in serv and serv['groupId'] == id:
                ret.append(serv)
        return ret

    # Returns all the devices available
    def getAll(self):
        return self._list

    def addService(self, service):
        if "serviceId" in service:
            if self.searchById(service["serviceId"]) == {}:
                self._lock.acquire()
                service['lastUpdate'] = time.time()
                self._list.append(service)
                self._lock.release()
                logging.debug("Added service new service: " + str(service['serviceId']))
                return service
            else:
                # Otherwise I update its information by keeping its id
                self._lock.acquire()
                for idx, serv in enumerate(self._list):
                    if serv['serviceId'] == service["serviceId"]:
                        service['lastUpdate'] = time.time()
                        self._list[idx] = service
                self._lock.release()

                logging.debug("Updated service service with id: " + str(service['serviceId']))
                return service
        else:
            return {}
