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
        self._cache = ControlCache(self._settings.getField('cacheRetationTimeInterval'),self._settings.getField('catalogAddress'))
        self._raisedFlag = False
        self._predictFlag = False

        if self._settings.getFieldOrDefault('serviceId', ''):
            self.onNewCatalogId(self._settings.getField('serviceId'))

    def run(self):
        logging.debug("Started")
        while self._run:
            time.sleep(1)

    def stop(self):
        self._ping.stop()
        if self._isMQTTconnected and self._mqtt is not None:
            self._mqtt.stop()
        self._run=False
        self.join()
    
    def polyFitting(self, dataset, timeset, degree, time_horizon = 1):
        floatlist = []
        timelist = []
        for data in dataset:
            floatlist.append(float(data))

        #logging.debug(f"{timeset}")
        #remove timestamp (first data) offset from timeset list
        for timedata in timeset:
            _time_data = int(timedata - timeset[0])
            timelist.append(_time_data)
        #logging.debug(f"{timelist}")
        time_horizon = timelist[len(timelist) - 1] - timelist[len(timelist) - 2]

        coefs = np.polyfit(timelist, floatlist, degree)
        poly = np.poly1d(coefs)
        next_value = poly(timelist.pop() + time_horizon)
        return next_value
    
    #in this function all the control algorithm has to be developed so that
    #for every thread the control is made every N (timeInterval to be chosen) 
    def controlAlgorithm(self):
        pass

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
        logging.debug(f"{payload}")
    
        feeds = []
        fields = []
        base_name = []

        base_name = payload["bn"].split("/")
        groupId = base_name[0]
        serviceId = base_name[1]

        # if the cache does not contains the reference groupId / serviceId I create it
        # by loading its content from thingspeak
        _type = payload["sensor_position"]
        if self._cache.findGroupServiceIdCache(groupId, serviceId) == False:
            self._cache.createCache(groupId, serviceId, _type)

        # logging.debug(f"{self._cache.getServiceCache(groupId, serviceId)}")

        for field in payload["e"]:
            measure_type = field["n"]
            actual_value = float(field["v"])
            key = str(measure_type)+"Threshold"
            threshold = float(self._settings.getField(key))

            past_data = self._cache.getLastResults(groupId, serviceId, measure_type)
            if past_data != []:

                #list with last value/values (in order to state the real behavior of the system)
                past_values = []
                for data in past_data:
                    past_values.append(data['value'])
                
                #in case the actual value is > threshold and even the last two values had passed it -> notification
                if actual_value > threshold and all(float(val) > threshold for val in past_values[-2:]):
                    self._raisedFlag = True
                    logging.debug(f"Attention: {measure_type} passed critical value. Actual value = {actual_value}, last two values = {past_values[-2:]}")

                    # TODO: make send notification to TELEGRAM
                else:
                    #list with last 5 values
                    time_values = []
                    to_interp = []
                    for data in past_data:
                        to_interp.append(float(data['value']))
                        time_values.append(data['timestamp'])
                    #logging.debug(f"last_four={to_interp}")
                    #logging.debug(f"time={time_values}")

                    #in case the actual value is under threshold but the polynomial interpolation tells us it is going to pass the threshold -> notification
                    if len(time_values) > 1:
                        predicted = self.polyFitting(to_interp, time_values, 2, int(self._settings.getField("polyFittingPredict")) )
                        if (float(predicted) > threshold):
                            self._raisedFlag = True
                            self._predictFlag = True
                            logging.debug(f"Attention: {measure_type} is going to pass critical value. Actual value = {actual_value}, last two values = {past_values[-2:]} and predicted value = {predicted}")

            if self._raisedFlag == True:
                uri = str(self._catalogAddress)+"/searchByServiceSubType?serviceSubType=EXTERNALWEATHERAPI"
                try:
                    r = requests.get(uri)
                    if r.status_code == 200:
                        for service in r.json()[0]["serviceServiceList"]:
                            if service["serviceType"]  == "REST":
                                ext_weather_api_ip = service["serviceIP"]
                                ext_weather_api_port = service["servicePort"]
                except Exception as e:
                    logging.debug(f"GET request exception Error: {e}")
                lat = 45.06
                lon = 7.66
                # TODO: load the location information at the startup when a new cache is added

                api_uri = "http://"+str(ext_weather_api_ip)+":"+str(ext_weather_api_port)+"/currentWeatherStatus?lat="+str(lat)+"&lon="+str(lon)

                try:
                    r = requests.get(api_uri)
                    if r.status_code == 200:
                        _ext_temp = r.json()["temperature"]
                        _ext_hum = r.json()["humidity"]
                        _safe_to_open = r.json()["safeOpenWindow"]

                        #the external conditions are good -> in case we want to circulate air we can open the windows
                        if _safe_to_open == True and _ext_temp < self._settings.getField('externalTemperatureMax') and _ext_temp > self._settings.getField('externalTemperatureMin') and _ext_hum > self._settings.getField('externalHumidityMin') and _ext_hum < self._settings.getField('externalHumidityMax'):
                            #case in which the measuretype forecast is over threshold
                            if self._predictFlag and self._raisedFlag:
                                to_ret = {
                                    "alert":str(measure_type)+"is going to be critical",
                                    "action":"open the window to prevent it",
                                    "groupId": groupId
                                }
                            #case in which the actual measure value is over threshold
                            else:
                                to_ret = {
                                    "alert":str(measure_type)+"is critical",
                                    "action":"open the window",
                                    "groupId": groupId
                                    }

                            logging.debug(to_ret)
                        
                        #the external conditions won't let us open the windows
                        else:
                            if self._predictFlag and self._raisedFlag:
                                to_ret = {
                                    "alert":str(measure_type)+" is going to be critical but external condition are bad",
                                    "action":"turn on the dehumidifier/open the internal door",
                                    "groupId": groupId  
                                }
                            else:
                                to_ret = {
                                "alert":str(measure_type)+" critical but external condition are bad",
                                "action":"turn on the dehumidifier/open the internal door",
                                "groupId": groupId
                                }
                        #logging.debug(r.json())

                        # TODO: send request to Telegram service for sending the message

                except Exception as e:
                    logging.debug(f"GET request exception: {e}")


            self._raisedFlag = False
            self._predictFlag = False
            self._cache.addToCache(groupId, serviceId, measure_type, field["v"], field["t"])




if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))

    availableServices=[]

    controlManager = ControlStrategy(settings, availableServices)
    controlManager.start()

