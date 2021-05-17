import json
import threading
import requests
import logging
import datetime
from datetime import *
import time

def changeDatetimeFormat(_datetime):
    year=str(_datetime.year)
    month=str(_datetime.month)
    day=str(_datetime.day)
    hour=str(_datetime.hour)
    minute=str(_datetime.minute)
    second=str(_datetime.second)
    _changed=year+"-"+month+"-"+day+"%20"+hour+":"+minute+":"+second
    return _changed



class ControlCache():
    def __init__(self, timeInterval, catalogAddress):
        self._cache = []
        self.lock = threading.Lock()
        self._time_interval = timeInterval
        self._catalogAddress = catalogAddress

    def createCache(self, groupId, serviceId, _type):
        new_groupId = {
            "groupId":groupId,
            "serviceIds":[]
        }
        new_cache = {
            "serviceId":serviceId,
            "temperature":[],
            "humidity":[],
            "co2":[]
        }
        
        fields = []

        self.lock.acquire()
       
        uri = str(self._catalogAddress)+"/searchByServiceSubType?serviceSubType=THINGSPEAK"
        try:
            r = requests.get(uri)
            if r.status_code == 200:
                for service in r.json()[0]["serviceServiceList"]:
                    if service["serviceType"]  == "REST":
                        thingspeak_adaptor_ip = service["serviceIP"]
                        thingspeak_adaptor_port = service["servicePort"]
        except Exception as e:
            logging.debug(f"Exception Error: {e}")

        baseUri = "http://"+str(thingspeak_adaptor_ip)+":"+str(thingspeak_adaptor_port)
        
        uri = baseUri+"/channel/"+serviceId+"/feeds/getResultsData?results=1"

        try:
            r = requests.get(uri)
            if r.status_code == 200:
                last_update = r.json()["feeds"][0]["created_at"]
        except Exception as e:
            logging.error(f"Request Error {e} for uri={uri}")

        #from the last entry timestamp i obtain the start timestamp (self._time_interval minutes before)
        end_timestamp = datetime.timestamp( datetime.strptime(last_update, "%Y-%m-%dT%H:%M:%SZ") )
        start_timestamp = end_timestamp - float(self._time_interval*60)

        #then i obtain them in datetime form
        start = datetime.fromtimestamp(start_timestamp)
        end = datetime.fromtimestamp(end_timestamp)

        #finally i convert them in the format accepted by thingspeak
        start = changeDatetimeFormat(start)
        end = changeDatetimeFormat(end)

        uri = baseUri+"/channel/"+serviceId+"/feeds/getStartEndData?start="+start+"&end="+end

        try:
            r = requests.get(uri)
            if r.status_code == 200:
                for i in range(1,8):
                    if "field"+str(i) in r.json()["channel"]:
                        #in fields: field (position) i -> measuretype
                        fields.append(r.json()["channel"]["field"+str(i)])
                for feed in r.json()["feeds"]:
                    for i,field in enumerate(fields):
                        datetime_obj = datetime.strptime(feed["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                        to_append = {
                            "value":feed["field"+str(i+1)],
                            "timestamp":datetime.timestamp(datetime_obj)
                        }
                        new_cache[str(field)].append(to_append)
                
        except Exception as e:
            logging.error(f"Request Error {e} for uri={uri}")

        new_groupId["serviceIds"].append(new_cache)
        self._cache.append(new_groupId)
        self.lock.release()
    
    def addToCache(self, groupId, serviceId, measuretype, data, timestamp):
        self.lock.acquire()
    
        for group_id in self._cache:
            if group_id["groupId"] == groupId:
                for cache in group_id["serviceIds"]:
                    if cache["serviceId"] == serviceId:
                        to_append = {
                            "value":data,
                            "timestamp":timestamp
                        }
                        cache[measuretype].append(to_append)

        #check if the cache has to be emptied
        for group_id in self._cache:
            for cache in group_id["serviceIds"]:
                if len(cache["temperature"]) > 1:
                    first_temp = cache["temperature"][0]["timestamp"]
                    last_temp = cache["temperature"][-1]["timestamp"]
                    if (last_temp-first_temp)/60 > self._time_interval:
                        self.popCache(group_id["groupId"], cache["serviceId"], "temperature")
                if len(cache["humidity"]) > 1:
                    first_hum = cache["humidity"][0]["timestamp"]
                    last_hum = cache["humidity"][-1]["timestamp"]
                    if (last_hum-first_hum)/60 > self._time_interval:
                        self.popCache(group_id["groupId"], cache["serviceId"], "humidity")
                if len(cache["co2"]) > 1:
                    first_co2 = cache["co2"][0]["timestamp"]
                    last_co2 = cache["co2"][-1]["timestamp"]
                    if (last_co2-first_co2)/60 > self._time_interval:
                        self.popCache(group_id["groupId"], cache["serviceId"], "co2")
        
        self.lock.release()

    def popCache(self, groupId, serviceId, measuretype):       

        for group_id in self._cache:
            for cache in group_id["serviceIds"]:
                if cache["serviceId"] == serviceId:
                    cache[str(measuretype)].pop(0)
            
    def findGroupServiceIdCache(self, groupId, serviceId):
        for group_id in self._cache:
            if group_id["groupId"] == groupId:
                for cache in group_id["serviceIds"]:
                    if cache["serviceId"] == serviceId:
                        return True
        return False
    def getLastResults(self, groupId, serviceId, measuretype, minutes=1):
        to_return = []
        _timestamp = datetime.timestamp(datetime.now())
        for group_id in self._cache:
            for cache in group_id["serviceIds"]:
                if cache["serviceId"] == serviceId and self._time_interval > minutes and len(cache[measuretype]) != 0:
                    for data in cache[measuretype]:
                        if (_timestamp-data["timestamp"])/60 < minutes:
                        #if (cache[measuretype][-1]["timestamp"]-data["timestamp"])/60 < minutes:
                            value = data
                            to_return.append(value)
                
        return to_return
    def getServiceCache(self, groupId, serviceId):
        for group_id in self._cache:
            for cache in group_id["serviceIds"]:
                if cache["serviceId"] == serviceId:
                    return cache
        return -1
    def getCompleteCache(self):
        return self._cache