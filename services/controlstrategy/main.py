# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
from commons.settingsmanager import *
from commons.logger import *
from commons.netutils import *
from controlcache import *
import requests
import json
import time
import threading
import logging
import numpy as np

class ControlStrategy(threading.Thread):
    def __init__(self, settings, serviceList):
        threading.Thread.__init__(self)
        self._settings = settings
        self._subscribeList = self._settings.getField('subscribeTopics')
        self._catalogAddress = self._settings.getField('catalogAddress')
        self._ping = Ping(int(self._settings.getField('pingTime')),
            serviceList,
            self._catalogAddress,
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getFieldOrDefault('serviceId', ''),
            "CONTROLSTRATEGY",
            groupId = None,
            notifier = self)
        self._ping.start()
        self._run=True
        self._mqtt = None
        self._cache = ControlCache(self._settings.getField('cacheTimeInterval'))
        self._cache.start()

        if self._settings.getFieldOrDefault('serviceId', ''):
            self.onNewCatalogId(self._settings.getField('serviceId'))

    def run(self):
        logging.debug("Started")
        while self._run:
            #do something
            time.sleep(1)

    def stop(self):
        self._ping.stop()
        if self._isMQTTconnected and self._mqtt is not None:
            self._mqtt.stop()
        self._run=False
        self.join()
    
    def polyFitting(self, dataset, timeset, degree, time_horizon = 1):
        floatlist=[]
        for data in dataset:
            floatlist.append(float(data))
        time_horizon = timeset[len(timeset) - 1] - timeset[len(timeset) - 2]

        coefs = np.polyfit(timeset, floatlist, degree)
        poly = np.poly1d(coefs)
        next_value = poly(timeset.pop() + time_horizon)
        return next_value

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
    
        feeds = []
        fields = []

        groupId = payload["bn"]
        
        if self._cache.findGroupIdCache(groupId) == False:
            logging.debug(f"entered here")
            self._cache.createCache(groupId)

        logging.debug(f"{self._cache.getCache(groupId)}")

        for field in payload["e"]:
            #logging.debug(f"{field}")
            measure_type = field["n"]
            actual_value = float(field["v"])
            key = str(measure_type)+"Threshold"
            threshold = float(self._settings.getField(key))

            if self._cache.getLastResults(groupId, measure_type) != []:
                #list with last two values
                past_data = self._cache.getLastResults(groupId, measure_type)
                past_values = []
                for data in past_data:
                    #logging.debug(f"data = {data}")
                    past_values.append(data['value'])
                #list with last 5 values
                if self._cache.getLastResults(groupId, measure_type, minutes=2) != []:
                    time_values = []
                    to_interp = []
                    for data in self._cache.getLastResults(groupId, measure_type, minutes=2):
                        to_interp.append(data['value'])
                        time_values.append(data['timestamp'])
                    #logging.debug(f"last_four={to_interp}")
                    #logging.debug(f"time={time_values}")
                    #in case the actual value is under threshold but the polynomial interpolation tells us it is going to pass the threshold -> notification
                    predicted = self.polyFitting(to_interp, time_values, 2)
                    logging.debug(f"{predicted}")
                    if (float(predicted) > threshold):
                        logging.debug(f"Attention: {measure_type} is going to pass critical value. Actual value = {actual_value}, last two values = {past_values} and predicted value = {predicted}")

                #in case the actual value is > threshold and even the last two values had passed it -> notification
                if actual_value > threshold and  all(float(val) > threshold for val in past_values):
                    logging.debug(f"Attention: {measure_type} passed critical value. Actual value = {actual_value}, last two values = {past_values}")
            self._cache.addToCache(groupId, measure_type, field["v"], field["t"])




if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))

    availableServices=[]

    controlManager = ControlStrategy(settings, availableServices)
    controlManager.start()
