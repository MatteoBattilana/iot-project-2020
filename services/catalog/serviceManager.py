import json
import os
import time
import uuid
import threading
from datetime import datetime


# Menager for services and devices, using lock
class ServiceManager():
    def __init__(self, retentionTimeout):
        self.__lock = threading.Lock()
        self.__retentionTimeout = retentionTimeout
        self.__list = []

    # Clean the records in the list that have a lastUpdate that is higher than
    # the set retention time; this method is called by the catalog every 10 seconds
    def cleanOldServices(self):
        self.__lock.acquire()
        for serv in self.__list[:]:
            if time.time() - serv['lastUpdate'] > self.__retentionTimeout:
                print("[CATALOG][INFO] Removed service: " + str(serv['serviceId']))
                self.__list.remove(serv);
        self.__lock.release()

    def searchById(self, id):
        for serv in self.__list:
            if serv['serviceId'] == id:
                return serv
        return {}

    # Returns all the devices available
    def getAll(self):
        return self.__list

    # Internal function to insert a service
    def __insertService(self, service):
        self.__lock.acquire()
        service['serviceId'] = str(uuid.uuid4())
        service['lastUpdate'] = time.time()
        self.__list.append(service)
        self.__lock.release()
        print("[CATALOG][INFO] Added service new service: " + str(service['serviceId']))
        return service

    def addService(self, service):
        # If the service is not in the list, it is simply added
        if "serviceId" not in service or self.searchById(service["serviceId"]) == {}:
            return self.__insertService(service)

        # Otherwaise I update its information by keeping its id
        self.__lock.acquire()
        for idx, serv in enumerate(self.__list):
            if serv['serviceId'] == service["serviceId"]:
                service['lastUpdate'] = time.time()
                service['serviceId'] = service["serviceId"]
                self.__list[idx] = service
        self.__lock.release()

        print("[CATALOG][INFO] Updated service service with id: " + str(service['serviceId']))
        return service
