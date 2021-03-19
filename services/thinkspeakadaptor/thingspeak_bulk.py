import time
import json

class ThingSpeakBulkUpdater():
    def __init__(self, bulkLimit):
        self.cacheList = []
        self.bulkLimit = bulkLimit
    def createChannelCache(self, channelName):
        new_channel_cache={
            "channel": channelName,
            "data": []
        }
        self.cacheList.append(new_channel_cache)
    def updateChannelCache(self, channelName, newdatas, timestamp):
        #at the moment the field are fixed a priori
        new_channel_update={
            "field1":"",
            "field2":"",
            "field3":"",
            "field4":"",
            "created_at":""
        }
        new_channel_update["created_at"]=timestamp
        for i,new_data in enumerate(newdatas):
            new_channel_update["field"+str(i+1)]=new_data
        for channelCache in self.cacheList:
            if channelCache["channel"] == channelName:
                if len(channelCache["data"]) < self.bulkLimit:
                    channelCache["data"].append(new_channel_update)
                    print("SIZE: " + str(len(channelCache["data"])))
                else:
                    print(f"[THINGSPEAKBULKUPDATER][ERROR] Exceed maximum messages per bulk {self.bulkLimit}")
        print(f"[THINGSPEAKBULKUPDATER][INFO] {self.cacheList}")
    def clearCache(self):
        for channelCache in self.cacheList:
            channelCache["data"].clear()
    def findChannel(self, channelName):
        flag = False
        for channelCache in self.cacheList:
            if channelCache["channel"] == channelName:
                flag = True
        return flag
