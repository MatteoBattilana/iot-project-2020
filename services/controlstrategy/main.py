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
        self._serviceId = self._settings.getField('serviceId')
        self._ping = Ping(int(self._settings.getField('pingTime')),
            serviceList,
            self._catalogAddress,
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getField('serviceId'),
            "CONTROLSTRATEGY",
            groupId = None)
        self._run=True
        self._mqtt = None
        self._cache = ControlCache(self._settings.getField('cacheRetationTimeInterval'),self._settings.getField('catalogAddress'))
        self._raisedFlag = False
        self._predictFlag = False
        self._lastSentAlert = {}

    def run(self):
        self._ping.start()

        self._mqtt = MQTTRetry(self._serviceId, self, self._catalogAddress)
        self._mqtt.subscribe(self._subscribeList)
        self._mqtt.start()

        logging.debug("Started")
        while self._run:
            time.sleep(1)

    def stop(self):
        self._ping.stop()
        if self._mqtt is not None:
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

    def sendTelegramMessage(self, to_ret):
        # I wait 5 minute before sending a new notificaton
        if to_ret['groupId'] not in self._lastSentAlert or time.time() - self._lastSentAlert[to_ret['groupId']] > 5*60:
            uri = str(self._catalogAddress)+"/searchByServiceSubType?serviceSubType=TELEGRAM-BOT"
            try:
                r = requests.get(uri)
                if r.status_code == 200:
                    for service in r.json()[0]["serviceServiceList"]:
                        if service["serviceType"]  == "REST":
                            ip = service["serviceIP"]
                            port = service["servicePort"]
                            try:
                                r = requests.post("http://" + ip + ":" + str(port) + "/sendAlert", json = to_ret)
                                logging.debug("Sent alert to Telegram bot")
                                if r.status_code != 200:
                                    logging.error("Unable to send alert via Telegram: " + r.json())

                            except Exception as e:
                                logging.error("Unable to send alert via Telegram : " + str(e))

            except Exception as e:
                logging.error(f"GET request exception Error: {e}")

            self._lastSentAlert[to_ret['groupId']] = time.time()
        else:
            logging.warning("Skipped to avoid flooding")



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

        #flag set to False if a certain groupId has only an internal device while it is set to True if has also an external one
        externalFlag, externalServiceId = self._cache.hasExternalDevice(groupId)

        if self._cache.findGroupServiceIdCache(groupId, serviceId) == False:
            self._cache.createCache(groupId, serviceId, _type)

        #logging.debug(f"{self._cache.getServiceCache(groupId, serviceId, _type)}")
        for field in payload["e"]:
            measure_type = field["n"]
            actual_value = float(field["v"])
            key = str(measure_type)+"Threshold"
            threshold = float(self._settings.getField(key))

            past_data = self._cache.getLastResults(groupId, serviceId, _type, measure_type)
            if past_data != []:

                #list with last value/values (in order to state the real behavior of the system)
                past_values = []
                for data in past_data:
                    past_values.append(data['value'])

                if _type == "internal":
                #in case the actual value is > threshold and even the last two values had passed it -> NOTIFICATION
                    if actual_value > threshold and all(float(val) > threshold for val in past_values[-2:]) and len(past_values[-2:]) > 1:
                        logging.info(str(actual_value) + " list previous " + str(past_values[-2:]) + " threshold: " + str(threshold))
                        self._raisedFlag = True

                    else:
                        #list with last 5 values
                        time_values = []
                        to_interp = []
                        for data in past_data:
                            to_interp.append(float(data['value']))
                            time_values.append(data['timestamp'])

                        #in case the last values (included the actual one) are under threshold, but the polynomial interpolation tells us it is going to pass the threshold -> NOTIFICATION
                        if len(time_values) > 1 and all(float(x) < threshold for x in past_values):
                            predicted = self.polyFitting(to_interp, time_values, 2, int(self._settings.getField("polyFittingPredict")) )
                            if (float(predicted) > threshold):
                                self._raisedFlag = True
                                self._predictFlag = True
                                #logging.debug(f"Attention: {measure_type} is going to pass critical value. Actual value = {actual_value}, last two values = {past_values[-2:]} and predicted value = {predicted}")

                    #if some measure is critical and need to be notificated to telegram
                    if self._raisedFlag == True:
                        to_ret = {
                            "alert":str(measure_type)+" is critical (critical value crossed three consecutive times)",
                            "action":"",
                            "furtherInfo":"",
                            "groupId": groupId
                        }
                        if self._predictFlag:
                            to_ret["alert"] = str(measure_type) + " is going to be critical"

                        #to send a notification to telegram we have to know the external conditions (temp,hum,pollution) in every case [TAKEN FROM EXTERNALWEATHERAPI]
                        uri = str(self._catalogAddress)+"/searchByServiceSubType?serviceSubType=EXTERNALWEATHERAPI"
                        #get request in order to take the externalweatherapi address
                        try:
                            r = requests.get(uri)
                            if r.status_code == 200:
                                for service in r.json()[0]["serviceServiceList"]:
                                    if service["serviceType"]  == "REST":
                                        ext_weather_api_ip = service["serviceIP"]
                                        ext_weather_api_port = service["servicePort"]
                        except Exception as e:
                            logging.error(f"GET request exception Error: {e}")
                        # Load the location information at the startup when a new cache is added
                        uri = str(self._catalogAddress)+"/getGroupId?groupId="+groupId
                        try:
                            r = requests.get(uri)
                            if r.status_code == 200 and "latitude" in r.json() and "longitude" in r.json():
                                lat = r.json()["latitude"]
                                lon = r.json()["longitude"]
                        except Exception as e:
                            logging.error(f"GET request exception Error: {e}")

                        if ext_weather_api_ip and lat:
                            api_uri = "http://"+str(ext_weather_api_ip)+":"+str(ext_weather_api_port)+"/currentWeatherStatus?lat="+str(lat)+"&lon="+str(lon)
                            #GET request to obtain infos from externalweatherapi
                            try:
                                r = requests.get(api_uri)
                                if r.status_code == 200:
                                    _ext_temp = r.json()["temperature"]
                                    _ext_hum = r.json()["humidity"]
                                    _safe_to_open = r.json()["safeOpenWindow"]
                            except Exception as e:
                                logging.error(f"GET request exception Error: {e}")
                            api_uri = "http://"+str(ext_weather_api_ip)+":"+str(ext_weather_api_port)+"/forecastWeatherStatus?lat="+str(lat)+"&lon="+str(lon)
                            try:
                                r = requests.get(api_uri)
                                if r.status_code == 200:
                                    #here i get the forecast informations about the weather and pollution
                                    pass
                            except Exception as e:
                                logging.error(f"GET request exception error: {e}")

                        #case in which there is the external device -> rather than contacting externalweatherapi demand temp/hum of the external device
                        if externalFlag == True:
                            #here i want to ask to the cache the last value of temperature and humidity of the corresponding external device
                            last_ext_temps = self._cache.getLastResults(groupId,externalServiceId,"external","temperature")
                            last_ext_hums = self._cache.getLastResults(groupId,externalServiceId,"external","humidity")
                            last_ext_temp = float(last_ext_temps.pop()['value'])
                            last_ext_hum = float(last_ext_hums.pop()['value'])
                            #check if external conditions from external device are good enough to open the window
                            if last_ext_temp < self._settings.getField('externalTemperatureMax') and last_ext_temp > self._settings.getField('externalTemperatureMax') and last_ext_hum > self._settings.getField('externalHumidityMin') and last_ext_hum < self._settings.getField('externalHumidityMax'):
                                #tell the user to open the window ONLY if the parameter _safeOpenWindow is OK
                                if _safe_to_open:
                                    #external conditions are good AND it's safeToOpen the window -> tell the user to open the window
                                    to_ret["action"] = "open the window"
                                else:
                                    #external conditions are good BUT it's not safe to open the windows (pollution/wind)
                                    to_ret["action"] = "open the internal door/turn on the dehumidifier"
                                    to_ret["furtherInfo"] = ""

                            #the external conditions obtained from the external device are NOT GOOD -> contact the externalweatherapi to know if in the near future it will change
                            else:
                                #from the externalweatherapi infos we can discover when it will be possible to open the window
                                to_ret["action"] = "open the internal door/turn on the dehumidifier"
                                #TO IMPLEMENT
                                to_ret["furtherInfo"] = "it will be possible to open the window at {}"

                        #case in which there is NO external device -> USE directly the externalweatherapi infos
                        elif _ext_temp and _ext_hum and _safe_to_open:
                            #here we control if it's safetopen and if the external temperature and humidity are good
                            if _safe_to_open == True and _ext_temp < self._settings.getField('externalTemperatureMax') and _ext_temp > self._settings.getField('externalTemperatureMax') and _ext_hum > self._settings.getField('externalHumidityMin') and _ext_hum < self._settings.getField('externalHumidityMax'):
                                to_ret["action"] = "open the window"
                            else:
                                to_ret["action"] = "open the internal door/turn on the dehumidifier"

                        #Send NOTIFICATION to Telegram service
                        self.sendTelegramMessage(to_ret)

                        self._raisedFlag = False
                        self._predictFlag = False

            self._cache.addToCache(groupId, serviceId, measure_type, _type, field["v"], field["t"])




if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))

    availableServices=[]

    controlManager = ControlStrategy(settings, availableServices)
    controlManager.start()
