import json
import os
import time
import uuid
import threading
from datetime import datetime

class ServiceManager():
    def __init__(self):
        self.__lock = threading.Lock()
        self.__list = []

    def cleanOldServices(self):
        self.__lock.acquire()
        for serv in self.__list[:]:
            if time.time() - serv['lastUpdate'] > 10:
                print("[CATALOG][INFO] Removed service: " + str(serv['serviceId']))
                self.__list.remove(serv);
        self.__lock.release()

    def searchById(self, id):
        for serv in self.__list:
            if serv['serviceId'] == id:
                return serv
        return {}

    def getAll(self):
        return self.__list

    def __insertService(self, service):
        self.__lock.acquire()
        service['serviceId'] = str(uuid.uuid4())
        service['lastUpdate'] = time.time()
        self.__list.append(service)
        self.__lock.release()
        print("[CATALOG][INFO] Added service " + service['serviceName'] + ": " + str(service['serviceId']))
        return service

    def addService(self, service):
        if "serviceId" not in service or self.searchById(service["serviceId"]) == {}:
            return self.__insertService(service)

        self.__lock.acquire()
        for idx, serv in enumerate(self.__list):
            if serv['serviceId'] == service["serviceId"]:
                service['lastUpdate'] = time.time()
                service['serviceId'] = service["serviceId"]
                self.__list[idx] = service
        self.__lock.release()

        print("[CATALOG][INFO] Updated service " + service['serviceName'] + ": " + str(service['serviceId']))
        return service
