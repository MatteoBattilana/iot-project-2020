import json
import threading
import requests
import logging

class ControlCache():
    def __init__(self):
        self._cache = []
        self.lock = threading.Lock()

    def createCache(self, groupId):
        new_cache = {
            "groupId":groupId,
            "temperature":[],
            "humidity":[],
            "co2":[]
        }
        self.lock.acquire()
        self._cache.append(new_cache)
        self.lock.release()
    
    def addToCache(self, groupId, measuretype, data):
        self.lock.acquire()

        for cache in self._cache:
            if cache["groupId"] == groupId:
                cache[measuretype].append(data)
        
        self.lock.release()

    def popCache(self, groupId, n):
        for cache in self._cache:
            if cache["groupId"] == groupId:
                if len(cache["temperature"]) > n:
                    cache["temperature"].pop(0)
                if len(cache["humidity"]) > n:
                    cache["humidity"].pop(0)
                if len(cache["co2"]) > n:
                    cache["co2"].pop(0)
    
    def findGroupIdCache(self, groupId):
        for cache in self._cache:
            if cache["groupId"] == groupId:
                return True
        return False
    def getLastNResults(self, groupId, measuretype, n=2):
        to_return = []
        for cache in self._cache:
            if cache["groupId"] == groupId and len(cache[measuretype]) > n-1:
                for i in range(1,n+1):
                    value = cache[measuretype][len(cache[measuretype])-i]
                    #logging.debug(f"value to return is {value}")
                    to_return.append(value)
        return to_return
    def getCache(self, groupId):
        for cache in self._cache:
            if cache["groupId"] == groupId:
                return cache
        return -1
