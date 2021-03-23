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
from thingspeak_bulk import *
import datetime
from datetime import timedelta
import cherrypy

def changeDatetimeFormat(_datetime):
    year=str(_datetime.year)
    month=str(_datetime.month)
    day=str(_datetime.day)
    hour=str(_datetime.hour)
    minute=str(_datetime.minute)
    second=str(_datetime.second)
    _changed=year+"-"+month+"-"+day+"%20"+hour+":"+minute+":"+second
    return _changed

class ThreadHttpRequest(threading.Thread):
    def __init__(self, url, jsonBody):
        threading.Thread.__init__(self)
        self.url = url
        self.jsonBody = jsonBody

    def run(self):
        try:
            requests.post(self.url, json=self.jsonBody)
            print(f"[THINGSPEAKADAPTOR][INFO] Sent data {self.jsonBody} in bulk to {self.url} in a POST request")
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] POST request went wrong")

#baseUri="https://api.thingspeak.com/"
class ThinkSpeakAdaptor(threading.Thread):
    exposed=True
    def __init__(self, pingTime, serviceList, serviceName, subscribeList, thingspeak_api_key, bulkRate, bulkLimit, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceName, "SERVICE", groupId = None, notifier = self)
        self._ping.start()
        self._subscribeList = subscribeList
        self._isMQTTconnected = False
        self._catalogAddress = catalogAddress
        self._mqtt = None
        self._baseUri = "https://api.thingspeak.com/"
        self._thingspeak_api_key = thingspeak_api_key
        self._channels = []                                 # it don't have to wait to fetch 
        self._channels = self.getChannelList()
        self.cache=ThingSpeakBulkUpdater(bulkLimit)
        self.updateBulkTime=bulkRate
        self._run=True


    def run(self):
        print("[INFO] Started")
        lastTime = 0
        while self._run:
            if time.time() - lastTime > self.updateBulkTime:
                self.sendToThingSpeak()
                lastTime = time.time()
            time.sleep(1)
        print ("[INFO] Stopped ThingSpeak")
    def stop(self):
        self._ping.stop()
        if self._isMQTTconnected and self._mqtt is not None:
            self._mqtt.stop()
        self._run=False
        self.join()

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
        self._isMQTTconnected=True

    def onMQTTConnectionError(self, error):
        self._isMQTTconnected=False
    def onMQTTMessageReceived(self, topic, message):
        payload=message
        #{
        # "bn":
        # "e":[
        #       { "n":
        #         "u":
        #         "t":
        #         "v":
        #       }, ..., {... }
        # ]
        # }

        _channel_name=topic.split("/")[2]       #home1
        #if the _channel_name is not present inside the channelList (the channel has to be created) -1 is returned
        _channel_id=self.getChannelID(_channel_name)

        #fields will contain the fields name
        fields=[]
        #new_datas will contain the values relative to those fields
        #to_join will contain a list of string in the format accepted by MQTT Ex. "field1=100","field2=29"
        _timestamp=""


        for i,field in enumerate(payload["e"]):
            fields.append(field["n"])
            _timestamp=field["t"]

        #if the channel is not set up on thingspeak yet
        if _channel_id == -1:
            print ("Create channel with name: "+ _channel_name + " and fields: " + str(fields))
            self.createNewChannel(_channel_name, fields)

        # check if all fields are present
        missingFields = self.getMissingFields(_channel_name, fields)
        if missingFields:
            self.addFieldsToChannel(_channel_name, missingFields)

        #if the channel is on thingspeak but not in the cache
        if self.cache.findChannel(_channel_name) == False:
            self.cache.createChannelCache(_channel_name)
            #print(f"[THINGSPEAKBULKUPDATER][INFO] Created new channel in the cacheList")

        #update THINGSPEAK with MQTT
        #multiple field TOPIC -> channels/<channelID>/publish/<apikey>
        #single field TOPIC -> channels/<channelID>/publish/fields/field<fieldnumber>/<apikey>
        #Set the PUBLISH messages to a QoS value of 0.
        #Set the connection RETAIN flag to 0.
        #Set the connection CleanSession flag to 1.
        #The payload parameters must be send in this way: field1=100&field2=9&ecc.. as a string

        #payload="&".join(to_join)
        #ThingSpeakPublisher.publish(str(_channel_id), str(self.getChannelApiKey(_channel_name)), payload)
        #print("Sent: " + payload)
        #update THINGSPEAK with REST
        #self.writeSingleEntry(_channel_name, new_datas)

        #update THINGSPEAK CACHE
        date=datetime.datetime.fromtimestamp(_timestamp)
        self.cache.updateChannelCache(_channel_name, payload["e"], str(date), self.getFieldMapping(_channel_name))
        print(f"[THINGSPEAKADAPTOR][INFO] Data sent to the cache")

    # Return the mapping of value type to its field: temperature - fieldX
    def getFieldMapping(self, channelName):
        mapped = {}
        for channel in self._channels:
            if channel["name"]==channelName:
                for i in range(1, 8):
                    if "field" + str(i) in channel:
                        mapped[channel["field" + str(i)]] = "field" + str(i)
        return mapped

    # add the fileds in missingFields to the channel on thingspeak
    def addFieldsToChannel(self, channelName, missingFields):
        channelID=self.getChannelID(channelName)
        url = self._baseUri+"channels/"+str(channelID)+".json?api_key=" + self._thingspeak_api_key + "&" + "&".join(missingFields)


        try:
            r = requests.put(url)
            if r.status_code == 200:
                # add new field to the local list of channels
                for channel in self._channels:
                    if channel["name"]==channelName:
                        for field in missingFields:
                            splitted = field.split("=")
                            channel[splitted[0]] = splitted[1]

                print("[THINGSPEAKADAPTOR][INFO] Added " + str(missingFields) + " to channel " + str(channelID))
        except Exception as e:
            print ("[THINGSPEAKADAPTOR][ERROR] Unable to add " + str(missingFields) + " to channel " + str(channelID))

    # return the missing fields of a channel in form fieldX=type: field1=temperature
    def getMissingFields(self, channelName, fields):
        missingFields = []
        for channel in self._channels:
            if channel["name"]==channelName:
                for value in fields:
                    found = False
                    last = 1
                    for i in range(1, 8):
                        if "field" + str(i) in channel:
                            last = i
                            if channel["field" + str(i)] == value:
                                found = True
                    if found == False:
                        # missing field in channel
                        print(value)
                        missingFields.append("field" + str(last+len(missingFields)+1) + "=" + value)

        return missingFields

    def sendToThingSpeak(self):
        #send all the POST request for every channel opened
        tlist = []
        for channelCache in self.cache.cacheList:
            channelName = channelCache["channel"]
            jsonBody={
                "write_api_key": self.getChannelApiKey(channelName),
                "updates":[]
            }
            for update in channelCache["data"]:
                jsonBody["updates"].append(update)

            thread = ThreadHttpRequest(self._baseUri+"channels/"+str(self.getChannelID(channelName))+"/bulk_update.json", jsonBody)
            thread.start()
            tlist.append(thread)

        for i in tlist:
            i.join()

        self.cache.clearCache()

    def getChannelList(self):
        #https://thingspeak.com/channels/1333290/field/2.json
        #GET request
        #https://api.thingspeak.com/channels.json?api_key=self._thingspeak_api_key
        try:
            r = requests.get(self._baseUri+"channels.json?api_key="+self._thingspeak_api_key)
            if r.status_code == 200:
                channels = r.json()
                # fetch all field list
                for i,channel in enumerate(channels):
                    r2 = requests.get(self._baseUri+"channels/"+str(channel["id"])+"/field/1.json?results=1&api_key="+channel["api_keys"][0]["api_key"])
                    for fieldId in range(0, 10):
                        if "field"+str(fieldId) in r2.json()["channel"]:
                            channels[i]["field"+str(fieldId)] = r2.json()["channel"]["field"+str(fieldId)]
                return channels
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
            print("i: " + str(i) + " name: " + field_name)
            jsonBody["field"+str(i+1)]=field_name

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
                newChannel = r.json()
                for i,field_name in enumerate(fields_name):
                    print("i: " + str(i) + " name: " + field_name)
                    newChannel["field"+str(i+1)]=field_name

                self._channels.append(newChannel)
                print(json.dumps(r.json(), indent=4))
                print("[THINGSPEAKADAPTOR][INFO] Thingspeak Channel " + channelName + " opened with success")
            else:
                print("[THINGSPEAKADAPTOR][ERROR] Unable to create a new channel " + channelName)
        except Exception as e:
            print("[THINGSPEAKADAPTOR][ERROR] Unable to create a new channel" + str(e))

    def getChannelApiKey(self, channelName, write=True):
        #function to return write/read channel API keys
        for channel in self._channels:
            if channel["name"]==channelName:
                for api_key in channel["api_keys"]:
                    if api_key["write_flag"]==write:
                        return api_key["api_key"]
        return "channelName not found"

    def readDataSingleField(self, channelName, field_id, results = 8000, days = 1, minutes = 1440, start = datetime.datetime.now() , end = datetime.datetime.now() + timedelta(days=1), sum = 0, average = 0, median = 0, start_end = False):
        #GET request
        #request parameters
        #results= numbers of entries to retrieve
        #days= numbers of days before now to include data
        #minutes=numbers of minute before now to include data
        #start= start_date
        #end= end_date (the end day measures are not included)
        #sum = X -> get the sum every X minutes
        #average = X -> get the avg every X minutes
        #median = X -> get the median every X minutes ("daily")
        #https://api.thingspeak.com/channels/channel_id/fields/field_id.json?api_key=self._thingspeak_api_key&results=1&
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        final_params=""
        if median != 0:
            final_params="&median="+str(median)
        if average != 0:
            final_params="&average="+str(average)
        if sum != 0:
            final_params="&sum="+str(sum)
        if start_end == True:
            start=changeDatetimeFormat(start)
            end=changeDatetimeFormat(end)
            parameters="api_key="+read_api_key+"&results="+str(results)+"&days="+str(days)+"&minutes="+str(minutes)+"&start="+start+"&end="+end+final_params
        else:
            parameters="api_key="+read_api_key+"&results="+str(results)+"&days="+str(days)+"&minutes="+str(minutes)+final_params
        
        uri=self._baseUri+"channels/"+str(channelID)+"/fields/"+str(field_id)+".json?"+parameters
        try:
            r = requests.get(uri)
            print(f"[THINGSPEAKADAPTOR][INFO] GET request with the following uri: {uri}")
            response = r.json()
            return json.dumps(response, indent=4)
            #print(f"[THINGSPEAKADAPTOR][INFO] Response = {r.json()}")
             
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] GET request to read data from ThingSpeak went wrong")
    def readDataMultipleFields(self, channelName, results = 8000, days = 1, minutes = 1440, start = datetime.datetime.now() - timedelta(days=1), end = datetime.datetime.now(), sum = 0, average = 0, median = 0, start_end = False):
        #https://api.thingspeak.com/channels/<channel_id>/feeds.json
        final_params=""
        if median != 0:
            final_params="&median="+str(median)
        if average != 0:
            final_params="&average="+str(average)
        if sum != 0:
            final_params="&sum="+str(sum)
        if start_end == True:
            start=changeDatetimeFormat(start)
            end=changeDatetimeFormat(end)
            parameters="api_key="+read_api_key+"&results="+str(results)+"&days="+str(days)+"&minutes="+str(minutes)+"&start="+start+"&end="+end+"&sum="+str(sum)+"&average="+str(average)+"&median="+str(median)
        else:
            parameters="api_key="+read_api_key+"&results="+str(results)+"&days="+str(days)+"&minutes="+str(minutes)+"&sum="+str(sum)+"&average="+str(average)+"&median="+str(median)
        
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        uri=self._baseUri+"channels/"+str(channelID)+"/feeds.json?"+parameters
        try:
            r =requests.get(uri)
            print(f"[THINGSPEAKADAPTOR][INFO] GET request with the following uri: {uri}")
            return r.json()
            #print(f"[THINGSPEAKADAPTOR][INFO] Response = {r.json()}")
        except Exception:
            print(f"[THINGSPEAKADAPTOR][ERROR] GET request from ThingSpeak went wrong")
    def GET(self, *uri, **params):
        #uri format 
        #https:localhost:port/channel/channelName/feeds?...
        #https:localhost:port/channel/channelName/field/fieldNumber/functionality?
        if len(uri) != 0:
            if uri[0] == "channel":
                channelName = uri[1]
                if uri[2] == "feeds":
                    #function to test
                    # 1 results
                    # 2 days
                    # 3 minutes
                    # 4 start/end
                    # 5 sum
                    # 6 average
                    # 7 median
                    if uri[3] == "getResultsData":
                        return json.dumps(self.readDataMultipleFields(channelName, results=params['results']), indent=3)
                    elif uri[3] == "getLastDaysData":
                        return json.dumps(self.readDataMultipleFields(channelName, days=params['days']), indent=3)
                    elif uri[3] == "getLastMinutesData":
                        return json.dumps(self.readDataMultipleFields(channelName, minutes=params['minutes']), indent=3)
                    elif uri[3] == "getStartEndData":
                        return json.dumps(self.readDataMultipleFields(channelName, start=params['start'], end=params['end'], start_end=True), indent=3)
                    elif uri[3] == "getSumData":
                        return json.dumps(self.readDataMultipleFields(channelName, sum=params['sum']), indent=3)
                    elif uri[3] == "getAvgData":
                        return json.dumps(self.readDataMultipleFields(channelName, average=params['average']), indent=3)
                    elif uri[3] == "getMedian":
                        return json.dumps(self.readDataMultipleFields(channelName, median=params['median']), indent=3)
                    else:
                        cherrypy.response.status = 404
                        return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)

                elif uri[2] == "field":

                    fieldNumber = uri[3]
                    if uri[4] == "getResultsData":
                        return self.readDataSingleField(channelName, fieldNumber, results=params['results'])
                    elif uri[4] == "getLastDaysData":
                        return self.readDataSingleField(channelName, fieldNumber, days=params['days'])
                    elif uri[4] == "getLastMinutesData":
                        return self.readDataSingleField(channelName, fieldNumber, minutes=params['minutes'])
                    elif uri[4] == "getStartEndData":
                        return self.readDataSingleField(channelName, fieldNumber, start=params['start'], end=params['end'], start_end=True)
                    elif uri[4] == "getSumData":
                        return self.readDataSingleField(channelName, fieldNumber, sum=params['sum'])
                    elif uri[4] == "getAvgData":
                        return self.readDataSingleField(channelName, fieldNumber, average=params['average'])
                    elif uri[4] == "getMedian":
                        return self.readDataSingleField(channelName, fieldNUmber, median=params['median'])
                    else:
                        cherrypy.response.status = 404
                        return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
                else:
                    cherrypy.response.status = 404
                    return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
            else:
                cherrypy.response.status = 404
                return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
        else:
            return json.dumps({"message": "ThingSpeak Adaptor API endpoint"}, indent=4)



if __name__=="__main__":
    conf={
            '/':{
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            }
    }
    settings = SettingsManager("settings.json")
    availableServices = [
        {
            "serviceType": "REST",
            "serviceIP": NetworkUtils.getIp(),
            "servicePort": 8080,
            "endPoint": [
                {
                    "type": "web",
                    "uri": "/",
                    "parameter": []
                }
            ]
        }
    ]
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
            int(settings.getField('bulkRate')),
            int(settings.getField('bulkLimit')),
            settings.getField('catalogAddress')
        )
    
    rpi.start()
    cherrypy.tree.mount(rpi ,'/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', rpi.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()


