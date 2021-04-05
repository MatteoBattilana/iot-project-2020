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
                self._list.remove(serv);
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

    def getWebInterfaceByGroup(self, groupId):
        url = ''
        for serv in self._list:
            if 'groupId' in serv and serv['groupId'] == groupId and 'serviceType' in serv and serv['serviceType'] == 'SERVICE':
                for service in serv['serviceList']:
                    if service['serviceType'] == "HTML":
                        for endpoint in service['endPoint']:
                            if endpoint['type'] == 'nodered-ui':
                                url = "http://" + service['serviceIP'] + ":" + str(service['servicePort']) + endpoint['uri']
        return url


    def searchByServiceSubType(self, subtype):
        ret = []
        for serv in self._list:
            if 'serviceSubType' in serv and serv['serviceSubType'] == subtype:
                ret.append(serv)
        return ret

    def searchAllGroupId(self):
        ret = []
        for serv in self._list:
            if 'groupId' in serv and serv['groupId'] not in ret:
                ret.append(serv['groupId'])
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

    def _insertServiceByServiceId(self, service, serviceId):
        self._lock.acquire()
        service['serviceId'] = serviceId
        service['lastUpdate'] = time.time()
        if (len(serviceId.split('-')) == 2):
            self._currentIndex = max(int(serviceId.split('-')[1]), self._currentIndex) + 1
        else:
            self._currentIndex = self._currentIndex + 1
        self._list.append(service)
        self._lock.release()
        logging.debug("Added service new service: " + str(service['serviceId']))
        return service

    # Internal function to insert a service
    def _insertService(self, service):
        return self._insertServiceByServiceId(service, service["serviceName"] + "-" + str(self._currentIndex))

    def addService(self, service):
        # If the service is not in the list, it is simply added
        if "serviceId" not in service and "serviceName" in service:
            return self._insertService(service)

        if self.searchById(service["serviceId"]) == {}:
            self._insertServiceByServiceId(service, service["serviceId"])
        else:
            # Otherwaise I update its information by keeping its id
            self._lock.acquire()
            for idx, serv in enumerate(self._list):
                if serv['serviceId'] == service["serviceId"]:
                    service['lastUpdate'] = time.time()
                    service['serviceId'] = service["serviceId"]
                    self._list[idx] = service
            self._lock.release()

        logging.debug("Updated service service with id: " + str(service['serviceId']))
        return service
