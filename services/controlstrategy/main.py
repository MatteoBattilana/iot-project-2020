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
from datetime import timedelta

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

    #this function check if the value toCheck is inside a certain range of values
    #measureType is passed to get from the settings.json the upper and lower bounds
    #if the parameter noMin is set True
    def checkMeasureType(self,toCheck, measureType, noMin=False):
        isInRange = False
        upBound = self._settings.getField(measureType+'Max')
        lwBound = 0
        if noMin == False:
            lwBound = self._settings.getField(measureType+'Min')
        if toCheck <= upBound and toCheck >= lwBound:
            isInRange = True
        return isInRange

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

        coefs = np.polyfit(timelist, floatlist, degree)
        poly = np.poly1d(coefs)
        next_value = poly(timelist[-1] + time_horizon)
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
                                    logging.error("Unable to send alert via Telegram: " + str(r.content) + " " + str(r.status_code))
                                else:
                                    self._lastSentAlert[to_ret['groupId']] = time.time()

                            except Exception as e:
                                logging.error("Unable to send alert via Telegram : " + str(e))

            except Exception as e:
                logging.error(f"GET request exception Error: {e}")
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
                        if len(time_values) > 5 and all(float(x) < threshold for x in past_values):
                            predicted = self.polyFitting(to_interp, time_values, 2, int(self._settings.getField("polyFittingPredict")) )
                            logging.debug("Predicted " + measure_type + " " + str(float(predicted)))
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

                        ext_weather_api_ip = ""
                        ext_weather_api_port = ""
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

                        lat = ""
                        lon = ""
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
                                    _ext_temp = float(r.json()["temperature"])
                                    _ext_hum = float(r.json()["humidity"])
                                    _safe_to_open = r.json()["safeOpenWindow"]
                                    _co = float(r.json()["co"])
                                    _no = float(r.json()["no"])
                                    _no2 = float(r.json()["no2"])
                                    _o3 = float(r.json()["o3"])
                                    _so2 = float(r.json()["so2"])
                                    _pm2_5 = float(r.json()["pm2_5"])
                                    _pm10 = float(r.json()["pm10"])
                            except Exception as e:
                                logging.error(f"GET request exception Error: {e}")
                            api_uri = "http://"+str(ext_weather_api_ip)+":"+str(ext_weather_api_port)+"/forecastWeatherStatus?lat="+str(lat)+"&lon="+str(lon)
                            start_timestamp = 0
                            try:
                                r = requests.get(api_uri)
                                if r.status_code == 200:
                                    weatherHours = [-1 for i in range(0,len(r.json()["hours"]))]
                                    start_timestamp = r.json()["hours"][0]["timestamp"]
                                    #here i get the forecast informations about the weather
                                    for i,hour in enumerate(r.json()["hours"]):
                                        logging.debug(str(hour))
                                        if i>0 and self.checkMeasureType(float(hour["temperature"]), 'externalTemperature') and self.checkMeasureType(float(hour['humidity']),'externalHumidity') and self.checkMeasureType(float(hour["wind_speed"]), 'windSpeed'):
                                            weatherHours[i] = 1
                                        else:
                                            weatherHours[i] = 0
                            except Exception as e:
                                logging.error(f"GET request exception error: {e}")
                            api_uri = "http://"+str(ext_weather_api_ip)+":"+str(ext_weather_api_port)+"/forecastPollution?lat="+str(lat)+"&lon="+str(lon)
                            try:
                                r = requests.get(api_uri)
                                if r.status_code == 200:
                                    pollHours = [ -1 for i in range(0,len(r.json()["pollution_values"])) ]
                                    #here i get the forecast infos about the pollution
                                    for i, hour in enumerate(r.json()["pollution_values"]):
                                        if i>0 and self.checkMeasureType(float(hour["co"]), "co", noMin=True) and self.checkMeasureType(float(hour["no"]), "no", noMin=True) and self.checkMeasureType(float(hour["no2"]), "no2", noMin=True) \
                                            and self.checkMeasureType(float(hour["o3"]), "o3", noMin=True) and self.checkMeasureType(float(hour["pm10"]),"pm10", noMin=True) \
                                            and self.checkMeasureType(float(hour["so2"]), "so2", noMin=True) and self.checkMeasureType(float(hour["pm2_5"]), "pm2_5", noMin=True):
                                            pollHours[i] = 1
                                        else:
                                            pollHours[i] = 0

                            except Exception as e:
                                logging.error(f"GET request exception Error: {e}")

                            #case in which there is the external device -> rather than contacting externalweatherapi demand temp/hum of the external device
                            isOpenWindow = False
                            if externalFlag == True:
                                #here i want to ask to the cache the last value of temperature and humidity of the corresponding external device
                                last_ext_temps = self._cache.getLastResults(groupId,externalServiceId,"external","temperature")
                                last_ext_hums = self._cache.getLastResults(groupId,externalServiceId,"external","humidity")
                                last_ext_temp = float(last_ext_temps.pop()['value'])
                                last_ext_hum = float(last_ext_hums.pop()['value'])
                                #check if external conditions from external device are good enough to open the window
                                #tell the user to open the window ONLY if the parameter _safeOpenWindow is OK
                                if self.checkMeasureType(last_ext_temp, 'externalTemperature') and self.checkMeasureType(last_ext_hum, 'externalHumidity') \
                                            and _safe_to_open and self.checkMeasureType(_co, "co", noMin=True) and self.checkMeasureType(_no, "no", noMin=True) \
                                            and self.checkMeasureType(_no2, "no2", noMin=True) \
                                            and self.checkMeasureType(_o3, "o3", noMin=True) and self.checkMeasureType(_pm10,"pm10", noMin=True) \
                                            and self.checkMeasureType(_so2, "so2", noMin=True) and self.checkMeasureType(_pm2_5, "pm2_5", noMin=True):
                                    #external conditions are good, it's safeToOpen the window (wind is good) AND pollution is OK-> tell the user to open the window
                                    to_ret["action"] = "open the window"
                                    isOpenWindow = True
                                elif not _safe_to_open:
                                    #external conditions are good BUT it's not safe to open the windows due to pollution
                                    to_ret["action"] = "open the internal door/turn on the dehumidifier"
                                    to_ret["furtherInfo"] = "bad external weather condition"
                                else:
                                    to_ret["action"] = "open the internal door/turn on the dehumidifier"
                                    to_ret["furtherInfo"] = "pollution high level"



                            #case in which there is NO external device -> USE directly the externalweatherapi infos
                            else:
                                #here we control if it's safetopen AND if the external temperature and humidity are good AND if the pollution levels are OK
                                if _safe_to_open and self.checkMeasureType(_ext_temp,"externalTemperature") and self.checkMeasureType(_ext_hum,"externalHumidity") and \
                                    self.checkMeasureType(_co, "co", noMin=True) and self.checkMeasureType(_no, "no", noMin=True) and self.checkMeasureType(_no2, "no2", noMin=True) \
                                    and self.checkMeasureType(_o3, "o3", noMin=True) and self.checkMeasureType(_pm10,"pm10", noMin=True) \
                                    and self.checkMeasureType(_so2, "so2", noMin=True) and self.checkMeasureType(_pm2_5, "pm2_5", noMin=True):
                                    to_ret["action"] = "open the window"
                                    isOpenWindow = True
                                elif not _safe_to_open:
                                    to_ret["action"] = "open the internal door/turn on the dehumidifier"
                                    to_ret["furtherInfo"] = "bad weather conditions"
                                else:
                                    to_ret["action"] = "open the internal door/turn on the dehumidifier"
                                    to_ret["furtherInfo"] = "pollution high levels"

                            if not isOpenWindow:
                                #the external conditions obtained from the external device are NOT GOOD -> contact the externalweatherapi to know if in the near future it will change
                                #from the externalweatherapi infos we can discover when it will be possible to open the window
                                final_len = min(len(pollHours), len(weatherHours))
                                hours = [(pollHours[i]+weatherHours[i]) for i in range(0,final_len)]
                                found = None
                                for i,hour in enumerate(hours):
                                    if hour == 2:
                                        found = i
                                        break
                                if found:
                                    # I need to add the current timezone (Italy)
                                    found = found + 2
                                    hourToOpen = datetime.fromtimestamp(start_timestamp) + timedelta(hours=found)
                                    to_ret["hourSuggestion"] = "It will be possible to open the window at " + hourToOpen.strftime("%H:%M %d/%m")

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
