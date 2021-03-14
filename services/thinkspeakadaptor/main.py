# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
import json
import socket
import time
from commons.netutils import *
import requests

#baseUri="https://api.thingspeak.com/"

json={
            "api_key":"",
            "name":""
    }

class ThinkSpeakAdaptor(threading.Thread):
    def __init__(self, pingTime, serviceList, serviceName, subscribeList, baseUri, thingspeak_api_key, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceName)
        self._mqtt = MQTTRetry(serviceId, self, catalogAddress)
        self._mqtt.subscribe(subscribeList)
        self._subscribeList = subscribeList
        self._isMQTTconnected = False
        self._catalogAddress=catalogAddress
        self._mqtt=None
        self._baseUri=baseUri
        self._thingspeak_api_key=thingspeak_api_key
        self._channels=[]


    def run(self):
        print("[THINGSPEAKADAPTOR][INFO] Started")
        self._ping.start()
        

        while True:
            time.sleep(10)

    # Catalog new id callback
    def onNewCatalogId(self, newId):
        print("[THINGSPEAKADAPTOR][INFO] New id from catalog: " + newId)
        if self._mqtt is not None:
            self._mqtt.stop()

        self._mqtt = MQTTRetry(newId, self, self._catalogAddress)
        self._mqtt.start()
    #MQTT callbacks
    def onMQTTConnected(self):
        self._isMQTTconnected = True
    def onMQTTConnectionError(self, error):
        self._isMQTTconnected = False
    def onMQTTMessageReceived(self, topic, message):
        payload=json.loads(message)
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
        
        _channel_name=payload["bn"]
        fields=[]
        new_datas=[]
        
        for field in payload["e"]:
            fields.append(field["n"])
            new_datas.append(field["v"])
        if _channel_name is not in channel_list:
            self.createNewChannel(_channel_name, fields)
        
        self.writeSingleEntry(_channel_name, new_datas)




        # TODO: must send to ThingSpeak
        print("Received new message with topic: " + topic)

    def getChannelList(self):
        #GET request
        #https://api.thingspeak.com/channels.json?api_key=self._thingspeak_api_key
        try:
            r = requests.get(self._baseUri+"channels.json?api_key="+self._thingspeak_api_key)
            return json.dumps(r.json(), indent=4)
        except Exception as e:
            print "[THINGSPEAKADAPTOR][ERROR] GET request went wrong"

    def clearChannelFeed(self, channelName):
        #DELETE request
        #https://api.thingspeak.com/channels/CHANNEL_ID/feeds.json
        channelID=self.getChannelID(channelName)
        jsonBody={
            "api_key"=self._thingspeak_api_key
        }
        try:
            requests.delete(self._baseUri+"channels/"+channelID+"/feeds.json", json=jsonBody)
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] Channel {channelName} feed DELETE went wrong")
    
    def removeChannel(self), channelName):
        #DELETE request
        #https://api.thingspeak.com/channels/CHANNEL_ID
        channelID=self.getChannelID(channelName)
        try:
            requests.delete(self._baseUri+"channels/"+channelID)
        except Exception:
            #exception
            print(f"[THINGSPEAKADAPTOR][ERROR] Channel {channelName} deletion was not possible")
    def getChannelID(self, channelName):
        for channel in self.:_channels:
            if channel["name"]==channelName:
                return channel["id"]
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


    def createNewChannel(self, channelName, fields_name):
        #POST request
        jsonBody=copy.copy(json)
        jsonBody["api_key"]=self._thingspeak_api_key
        jsonBody["name"]=channelName
        #TODO modify the jsonBody in order to set the channel parameters at first
        #public_flag=True if we want a public channel
        #specify also the fields used with their names Ex: jsonBody["field1"]=Temperature

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
            r = requests.post(self._baseUri, json = postBody)
            print("[THINGSPEAKADAPTOR][INFO] Thingspeak Channel " + channelName + "opened with success")
            #verify if it works like this
            self._channels.append(r.json())
            
        except Exception as e:
            print("[THINGSPEAKADAPTOR][ERROR] Unable to create a new channel" )

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
        for i,new_data in new_datas:
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
                else:
                    return f"Wrong channel name"

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
    try: 
        thingspeak_api_key = os.environ['THINGSPEAKAPIKEY']
    except:
        print("[THINGSPEAKADAPTOR][ERROR] THINGSPEAKAPIKEY variabile not set")
        thingspeak_api_key = ""
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = []

    rpi = ThinkSpeakAdaptor(
            settings['pingTime'],
            availableServices,
            settings['serviceName'],
            settings['subscribeTopics'],
            settings['baseUri'],
            thingspeak_api_key,
            settings['catalogAddress']
        )
    rpi.start()
    rpi.join()
