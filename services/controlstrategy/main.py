from commons.MQTTRetry import *
from commons.ping import *
from commons.settingsmanager import *
from commons.logger import *
from commons.netutils import *
import requests
import json
import time
import logging
import threading
import datetime

class ControlStrategy(threading.Thread):
    def __init(self, settings, serviceList):
        threading.Thread.__init__(self)
        self._settings = settings
        self._subscribeList = self._settings.getField('subscribeTopics')
        self._ping = Ping(int(self._settings.getField('pingTime')),
            serviceList,
            self._settings.getField('catalogAddress'),
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getFieldOrDefault('serviceId', ''),
            "CONTROLSTRATEGY",
            groupId = None,
            notifier = self)
        self._ping.start()
        self._run=True
        self._mqtt = None

        if self._settings.getFieldOrDefault('serviceId', ''):
            self.onNewCatalogId(self._settings.getField('serviceId'))
    
    def run(self):
        logging.debug("Started")
        pass
    def stop(self):
        self._ping.stop()
        if self._isMQTTconnected and self._mqtt is not None:
            self._mqtt.stop()
        self._run=False
        self.join()
    
    def onNewCatalogId(self, newId):
        self._settings.updateField('serviceId', newId)
        if self._mqtt is not None:
            self._mqtt.stop()

        self._mqtt = MQTTRetry(newId, self, self._catalogAddress)
        self._mqtt.subscribe(self._subscribeList)
        self._mqtt.start()

    #MQTT callbacks
    def onMQTTConnected(self):
        self._isMQTTconnected = True
    def onMQTTConnectionError(self, error):
        self._isMQTTconnected = False
    def onMQTTMessageReceived(self, topic, message):
        payload = message
        logging.debug(f"payload = {payload}")
    
    

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    availableServices=[]

    ControlManager = ControlStrategy(
        settings,
        availableServices
    )

    
