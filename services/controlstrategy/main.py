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
        self._cache = ControlCache()

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
    
    def polyFitting(self, dataset, degree, time_horizon = 1):
        floatlist=[]
        for data in dataset:
            floatlist.append(float(data))

        #timeset should be modified in case the sampling time varied
        timeset = [i for i in range(0, len(dataset))]
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
        
        #uri = "http://localhost:8090/channel/"+payload["bn"]+"/feeds/getResultsData?results="+str(2)
        #try:
        #    r = requests.get(uri)
        #    for i in range(1,8):
        #        if "field"+str(i) in r["channel"]:
        #            fields.append(r["channel"]["field"+str(i)])
        #    for feed in r["feeds"]:
        #        feeds.append(feed)
        #    logging.debug(f"{feeds}")
        #except Exception as e:
        #    logging.error(f"Request Error {e} for uri={uri}")

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
            
            #get the corresponding field number
            #for i,field in fields:
            #    if field == measure_type:
            #        field_number = i

            #get the last measuretype values       
            #for feed in feeds:
            #    if float(feed["field"+str(field_number)]) > threshold:
            #        cnt = cnt + 1

            if self._cache.getLastNResults(groupId, measure_type) != []:
                #list with last two values
                past_values = self._cache.getLastNResults(groupId, measure_type)
                
                #list with last 5 values
                if self._cache.getLastNResults(groupId, measure_type, n=5) != []:
                    last_five = self._cache.getLastNResults(groupId, measure_type, n=5)
                    #in case the actual value is under threshold but the polynomial interpolation tells us it is going to pass the threshold -> notification
                    predicted = self.polyFitting(last_five, 2)
                    #logging.debug(f"{predicted}")
                    if (float(predicted) > threshold):
                        logging.debug(f"Attention: {measure_type} is going to pass critical value. Actual value = {actual_value}, last two values = {past_values} and predicted value = {predicted}")

                #logging.debug(f"{past_values}")

                #in case the actual value is > threshold and even the last two values had passed it -> notification
                if actual_value > threshold and  all(float(val) > threshold for val in past_values):
                    logging.debug(f"Attention: {measure_type} passed critical value. Actual value = {actual_value}, last two values = {past_values}")
            self._cache.addToCache(groupId, measure_type, field["v"])
            self._cache.popCache(groupId, 5)




if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))

    availableServices=[]

    controlManager = ControlStrategy(settings, availableServices)
    controlManager.start()
