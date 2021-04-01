import time
import json
import threading
import logging

class ThingSpeakBulkUpdater():
    def __init__(self, bulkLimit):
        self.cacheList = []
        self.bulkLimit = bulkLimit
        self.lock = threading.Lock()

    def createChannelCache(self, channelName):
        new_channel_cache={
            "channel": channelName,
            "data": []
        }
        self.lock.acquire()
        self.cacheList.append(new_channel_cache)
        self.lock.release()

    def updateChannelCache(self, channelName, newdatas, timestamp, fieldMapping):
        #at the moment the field are fixed a priori

        self.lock.acquire()
        new_channel_update = {}
        new_channel_update["created_at"]=timestamp
        for new_data in newdatas:
            new_channel_update[fieldMapping[new_data["n"]]]=new_data["v"]

        for channelCache in self.cacheList:
            if channelCache["channel"] == channelName:
                if len(channelCache["data"]) < self.bulkLimit:
                    channelCache["data"].append(new_channel_update)
                    logging.info("Added to cache " + str(new_channel_update) + " for " + channelName)
                else:
                    logging.error(f"Exceed maximum messages per bulk {self.bulkLimit}")
        self.lock.release()

    def clearCache(self):
        self.lock.acquire()
        for channelCache in self.cacheList:
            channelCache["data"].clear()
        self.lock.release()

    def findChannel(self, channelName):
        flag = False
        for channelCache in self.cacheList:
            if channelCache["channel"] == channelName:
                flag = True
        return flag
