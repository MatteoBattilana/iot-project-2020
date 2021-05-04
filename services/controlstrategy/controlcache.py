import json
import threading
import requests
import logging
import datetime
from datetime import *
import time

class ControlCache(threading.Thread):
    def __init__(self, time_interval):
        threading.Thread.__init__(self)
        self._cache = []
        self.lock = threading.Lock()
        self._time_interval = time_interval
        self._run = True
    
    def run(self):
        while self._run:
            for cache in self._cache:
                if len(cache["temperature"]) != 0:
                    first_temp = cache["temperature"][0]["timestamp"]
                    last_temp = cache["temperature"][-1]["timestamp"]
                    if (last_temp-first_temp)/60 > self._time_interval:
                        self.popCache(cache["groupId"], "temperature")
                if len(cache["humidity"]):
                    first_hum = cache["humidity"][0]["timestamp"]
                    last_hum = cache["humidity"][-1]["timestamp"]
                    if (last_hum-first_hum)/60 > self._time_interval:
                        self.popCache(cache["groupId"], "humidity")
                if len(cache["co2"]):
                    first_co2 = cache["co2"][0]["timestamp"]
                    last_co2 = cache["co2"][-1]["timestamp"]
                    if (last_co2-first_co2)/60 > self._time_interval:
                        self.popCache(cache["groupId"], "co2")
            time.sleep(1)
            
    def stop(self):
        self._run = False

    def createCache(self, groupId):
        new_cache = {
            "groupId":groupId,
            "temperature":[],
            "humidity":[],
            "co2":[]
        }
        self.lock.acquire()
        
        fields = []

        uri = "http://localhost:8090/channel/"+groupId+"/feeds/getMinutesData?minutes="+str(self._time_interval)
        logging.debug(f"Call request to uri = {uri}")
        try:
            r = requests.get(uri)
            if r.status_code == 200:
                for i in range(1,8):
                    if "field"+str(i) in r["channel"]:
                        #in fields: field (position) i -> measuretype
                        fields.append(r["channel"]["field"+str(i)])
                for feed in r["feeds"]:
                    for i,field in enumerate(fields):
                        new_cache[field].append(feed["field"]+str(i))
        except Exception as e:
            logging.error(f"Request Error {e} for uri={uri}")
        self._cache.append(new_cache)
        self.lock.release()
    
    def addToCache(self, groupId, measuretype, data, timestamp):
        self.lock.acquire()

        for cache in self._cache:
            if cache["groupId"] == groupId:
                to_append = {
                    "value":data,
                    "timestamp":timestamp
                }
                cache[measuretype].append(to_append)
        
        self.lock.release()

    def popCache(self, groupId, measuretype):
        self.lock.acquire()

        for cache in self._cache:
            if cache["groupId"] == groupId:
                cache[measuretype].pop(0)
            
        self.lock.release()
    
    def findGroupIdCache(self, groupId):
        for cache in self._cache:
            if cache["groupId"] == groupId:
                return True
        return False
    def getLastResults(self, groupId, measuretype, minutes=1):
        to_return = []
        _timestamp = datetime.timestamp(datetime.now())
        for cache in self._cache:
            if cache["groupId"] == groupId and self._time_interval > minutes and len(cache[measuretype]) != 0:
                for data in cache[measuretype]:
                    #if (_timestamp-data["timestamp"])/60 < minutes:
                    if (cache[measuretype][-1]["timestamp"]-data["timestamp"])/60 < minutes:
                        value = data
                        to_return.append(value)
                
        return to_return
    def getCache(self, groupId):
        for cache in self._cache:
            if cache["groupId"] == groupId:
                return cache
        return -1
