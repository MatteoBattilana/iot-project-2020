# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
import json
import socket
import time
import requests
from commons.netutils import *
from commons.settingsmanager import *
from thingspeakpublisher import *
#from datetime import *

#baseUri="https://api.thingspeak.com/"
class ThinkSpeakAdaptor(threading.Thread):
    def __init__(self, pingTime, serviceList, serviceName, subscribeList, thingspeak_api_key, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceName, "SERVICE", groupId = None, notifier = self)
        self._ping.start()
        self._subscribeList = subscribeList
        self._isMQTTconnected = False
        self._catalogAddress = catalogAddress
        self._mqtt = None
        self._baseUri = "https://api.thingspeak.com/"
        self._thingspeak_api_key = thingspeak_api_key
        self._channels = self.getChannelList()


    def run(self):
        print("[INFO] Started")
        while True:
            time.sleep(10)

    # Catalog new id callback
    def onNewCatalogId(self, newId):
        print("[INFO] New id from catalog: " + newId)
        if self._mqtt is not None:
            self._mqtt.stop()

        self._mqtt = MQTTRetry(newId, self, self._catalogAddress)
        self._mqtt.subscribe(self._subscribeList)
        self._mqtt.start()

    #MQTT callbacks
    def onMQTTConnected(self):
        pass
    def onMQTTConnectionError(self, error):
        pass
    def onMQTTMessageReceived(self, topic, message):
        payload=message
        #{
        # "bn":
        # "e":[
        #       { "n":
        #         "u":
        #         "t":
        #         "v":
        #       }
        # ]
        # }

        _channel_name=topic.split("/")[2]       #home1
        #if the _channel_name is not present inside the channelList (the channel has to be created) -1 is returned
        _channel_id=self.getChannelID(_channel_name)

        #fields will contain the fields name
        fields=[]
        #new_datas will contain the values relative to those fields
        new_datas=[]
        #to_join will contain a list of string in the format accepted by MQTT Ex. "field1=100","field2=29"
        to_join=[]
        _timestamp=""


        for i,field in enumerate(payload["e"]):
            fields.append(field["n"])
            new_datas.append(field["v"])
            to_join.append("field"+str(i+1)+"="+str(field["v"]))
            _timestamp=field["t"]

        #created_datetime = datetime.fromtimestamp(_timestamp)
        #to_join.append("created_at="+created_datetime)
        if _channel_id == -1:
            self.createNewChannel(_channel_name, fields)

        #update THINGSPEAK with MQTT
        #multiple field TOPIC -> channels/<channelID>/publish/<apikey>
        #single field TOPIC -> channels/<channelID>/publish/fields/field<fieldnumber>/<apikey>
        #Set the PUBLISH messages to a QoS value of 0.
        #Set the connection RETAIN flag to 0.
        #Set the connection CleanSession flag to 1.
        #The payload parameters must be send in this way: field1=100&field2=9&ecc.. as a string

        payload="&".join(to_join)
        ThingSpeakPublisher.publish(str(_channel_id), str(self.getChannelApiKey(_channel_name)), payload)
        print("Sent: " + payload)
        #update THINGSPEAK with REST
        #self.writeSingleEntry(_channel_name, new_datas)

    def getChannelList(self):
        #GET request
        #https://api.thingspeak.com/channels.json?api_key=self._thingspeak_api_key
        try:
            r = requests.get(self._baseUri+"channels.json?api_key="+self._thingspeak_api_key)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print ("[THINGSPEAKADAPTOR][ERROR] GET request went wrong")
        return []

    def clearChannelFeed(self, channelName):
        #DELETE request
        #https://api.thingspeak.com/channels/CHANNEL_ID/feeds.json
        channelID=self.getChannelID(channelName)
        jsonBody={
            "api_key": self._thingspeak_api_key
        }
        try:
            requests.delete(self._baseUri+"channels/"+channelID+"/feeds.json", json=jsonBody)
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] Channel {channelName} feed DELETE went wrong")

    def removeChannel(self, channelName):
        #DELETE request
        #https://api.thingspeak.com/channels/CHANNEL_ID
        channelID=self.getChannelID(channelName)
        try:
            requests.delete(self._baseUri+"channels/"+channelID)
        except Exception:
            #exception
            print(f"[THINGSPEAKADAPTOR][ERROR] Channel {channelName} deletion was not possible")
    def getChannelID(self, channelName):
        for channel in self._channels:
            if channel["name"]==channelName:
                return channel["id"]
        return -1
    def modifyChannelData(self, newChannelName):
        #PUT request to modify the name of the channel
        #https://api.thingspeak.com/channels.json
        jsonBody=json
        jsonBody["api_key"]=self._thingspeak_api_key
        jsonBody["name"]=newChannelName
        try:
            requests.put(self._baseUri+"channels.json", json=jsonBody)
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] PUT request went wrong")


    def createNewChannel(self, channelName, fields_name, public=False, latitude=0.0, longitude=0.0):
        #POST request
        #https://api.thingspeak.com/channels.json
        jsonBody={
            "api_key": self._thingspeak_api_key,
            "name": channelName,
            "public_flag":public,
            "field1":"",
            "field2":"",
            "field3":"",
            "field4":"",
            "field5":"",
            "field6":"",
            "field7":"",
            "field8":"",
            "latitude":latitude,
            "longitude":longitude
        }

        for i,field_name in enumerate(fields_name):
            jsonBody["field"+str(i)]=field_name

        #these are the returned infos
        info_channel={
            "id": None,
            "name": "",
            "description": None,
            "latitude": "",
            "longitude": "",
            "created_at": "",
            "elevation": None,
            "last_entry_id": None,
            "public_flag": None,
            "url": None,
            "ranking": None,
            "metadata": None,
            "license_id": None,
            "github_url": None,
            "tags": [],
            "api_keys": [
                    {
                    "api_key": "",
                    "write_flag": None
                    },
                    {
                    "api_key": "",
                    "write_flag": None
                    }
                        ]
        }

        try:
            r = requests.post(self._baseUri + "channels.json", json = jsonBody)
            #verify if it works like this
            print(self._baseUri + "channels.json",)
            if r.status_code == 200:
                self._channels.append(r.json())
                print("[THINGSPEAKADAPTOR][INFO] Thingspeak Channel " + channelName + " opened with success")
            else:
                print("[THINGSPEAKADAPTOR][ERROR] Unable to create a new channel " + channelName)
        except Exception as e:
            print("[THINGSPEAKADAPTOR][ERROR] Unable to create a new channel" + str(e))

    def writeSingleEntry(self,channelName, new_datas):
        #the single entry can be updated through GET and POST request
        # GET request
        #https://api.thingspeak.com/update.json?api_key=self._thingspeak_api_key&field1=100
        #in our case i decided to use POST request
        #POST request
        #https://api.thingspeak.com/update.json
        jsonBody={
            "api_key":self.getChannelApiKey(channelName),
            "field1":None,
            "field2":None,
            "field3":None,
            "field4":None,
            "field5":None,
            "field6":None,
            "field7":None,
            "field8":None,
            "lat":"",
            "long":"",
            "created_at":""
        }
        #this has to be modified
        for i,new_data in enumerate(new_datas):
            jsonBody["field"+str(i)]=new_data


        try:
            requests.post(self._baseUri+"update.json", json=jsonBody)
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] POST request went wrong")

    def writeMultipleEntries(self, channelName):
        #with this function it is possible to update multiple instances of update.
        #POST request
        #https://api.thingspeak.com/channels/<channel_id>/bulk_update.json
        channelID=self.getChannelID(channelName)
        jsonBody={
            "write_api_key":self.getChannelApiKey(channelName),
            "updates":[]
        }
        new_update={
            "field1":None,
            "field2":None,
            "field3":None,
            "field4":None,
            "field5":None,
            "field6":None,
            "field7":None,
            "field8":None,
            "lat":"",
            "long":"",
            "created_at":""
        }
        #DIFFERENT FORMAT FOR JSON BODY
        #new_update={
        #   "delta_t":,
        #   "field1":,
        #   "fieldX":
        # }
            #TODO
        #decide how to fill multiple data entries varying with time
        uri=self._baseUri+"channels/"+channelID+"/bulk_update.json"
        try:
            requests.post(uri, json=jsonBody)
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] POST request went wrong")

    def getChannelApiKey(self, channelName, write=True):
        #function to return write/read channel API keys
        for channel in self._channels:
            if channel["name"]==channelName:
                for api_key in channel["api_keys"]:
                    if api_key["write_flag"]==write:
                        return api_key["api_key"]
        return "channelName not found"

    def readDataSingleField(self, channelName, field_id):
        #GET request
        #request parameters
        #results= numbers of entries to retrieve
        #days= numbers of days before now to include data
        #minutes=numbers of minute before now to include data
        #start= start_date
        #end= end_date
        #https://api.thingspeak.com/channels/channel_id/fields/field_id.json?api_key=self._thingspeak_api_key&results=1&
        channelID=self.getChannelID(channelName)
        #TODO the uri must be modified in order to satisfy our needs
        uri=self._baseUri+"channels/"+channelID+"/fields/"+str(field_id)+".json?api_key="+self._thingspeak_api_key
        try:
            requests.get(uri)
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] GET request went wrong")
    def readDataMultipleFields(self, channelName):
        pass

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    availableServices = []
    try:
        thingspeak_api_key = os.environ['THINGSPEAKAPIKEY']
        print("[THINGSPEAKADAPTOR][INFO] THINGSPEAKAPIKEY variabile set to: " + thingspeak_api_key)
    except:
        print("[THINGSPEAKADAPTOR][ERROR] THINGSPEAKAPIKEY variabile not set")
        thingspeak_api_key = ""

    rpi = ThinkSpeakAdaptor(
            int(settings.getField('pingTime')),
            availableServices,
            settings.getField('serviceName'),
            settings.getField('subscribeTopics'),
            thingspeak_api_key,
            settings.getField('catalogAddress')
        )
    rpi.start()
    rpi.join()
