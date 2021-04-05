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
import logging
from commons.logger import *

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
    def __init__(self, url, jsonBody, channelName):
        threading.Thread.__init__(self)
        self.url = url
        self.jsonBody = jsonBody
        self.channelName = channelName

    def run(self):
        try:
            r = requests.post(self.url, json=self.jsonBody)
            logging.info(f"Sent data {self.jsonBody} in bulk to channel {self.channelName} in a POST request")
        except Exception:
            logging.error(f"POST request went wrong")

#baseUri="https://api.thingspeak.com/"
class ThinkSpeakAdaptor(threading.Thread):
    exposed=True
    def __init__(self, settings, serviceList, thingspeak_api_key):
        threading.Thread.__init__(self)
        self._settings = settings
        self._subscribeList = self._settings.getField('subscribeTopics')
        self._isMQTTconnected = False
        self._catalogAddress = self._settings.getField('catalogAddress')
        self._mqtt = None
        self._baseUri = "https://api.thingspeak.com/"
        self._thingspeak_api_key = thingspeak_api_key
        self._channels = []                                 # it don't have to wait to fetch
        self._channels = self.getChannelList()
        self.cache=ThingSpeakBulkUpdater(int(self._settings.getField('bulkLimit')))
        self.updateBulkTime=int(self._settings.getField('bulkRate'))
        self._ping = Ping(
            int(self._settings.getField('pingTime')),
            serviceList,
            self._settings.getField('catalogAddress'),
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getFieldOrDefault('serviceId', ''),
            "THINGSPEAK",
            groupId = None,
            notifier = self)
        self._ping.start()
        self._run=True

        if self._settings.getFieldOrDefault('serviceId', ''):
            self.onNewCatalogId(self._settings.getField('serviceId'))


    def run(self):
        logging.debug("Started")
        lastTime = 0
        while self._run:
            if time.time() - lastTime > self.updateBulkTime:
                self.sendToThingSpeak()
                lastTime = time.time()
            time.sleep(1)
        logging.debug("Stopped ThingSpeak")
    def stop(self):
        self._ping.stop()
        if self._isMQTTconnected and self._mqtt is not None:
            self._mqtt.stop()
        self._run=False
        self.join()

    # Catalog new id callback
    def onNewCatalogId(self, newId):
        self._settings.updateField('serviceId', newId)
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

        _channel_name=topic.split("/")[3]       #RASPBERRY-3
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
            logging.debug("Create channel with name: "+ _channel_name + " and fields: " + str(fields))
            self.createNewChannel(_channel_name, fields)

        # check if all fields are present
        missingFields = self.getMissingFields(_channel_name, fields)
        if missingFields:
            self.addFieldsToChannel(_channel_name, missingFields)

        #if the channel is on thingspeak but not in the cache
        if self.cache.findChannel(_channel_name) == False:
            self.cache.createChannelCache(_channel_name)
            #logging.debug(f"Created new channel in the cacheList")

        #update THINGSPEAK with MQTT
        #multiple field TOPIC -> channels/<channelID>/publish/<apikey>
        #single field TOPIC -> channels/<channelID>/publish/fields/field<fieldnumber>/<apikey>
        #Set the PUBLISH messages to a QoS value of 0.
        #Set the connection RETAIN flag to 0.
        #Set the connection CleanSession flag to 1.
        #The payload parameters must be send in this way: field1=100&field2=9&ecc.. as a string

        #payload="&".join(to_join)
        #ThingSpeakPublisher.publish(str(_channel_id), str(self.getChannelApiKey(_channel_name)), payload)
        #logging.debug("Sent: " + payload)
        #update THINGSPEAK with REST
        #self.writeSingleEntry(_channel_name, new_datas)

        #update THINGSPEAK CACHE
        date=datetime.datetime.fromtimestamp(_timestamp)
        self.cache.updateChannelCache(_channel_name, payload["e"], str(date), self.getFieldMapping(_channel_name))

    # Return the mapping of value type to its field: temperature - fieldX
    def getFieldMapping(self, channelName):
        mapped = {}
        for channel in self._channels:
            if channel["name"]==channelName:
                for i in range(1, 8):
                    if "field" + str(i) in channel:
                        mapped[channel["field" + str(i)]] = "field" + str(i)
        return mapped

    #return the field number corresponding to a certain measure type (otherwise return -1)
    def getFieldNumber(self, channelName, measure_type):
        mapped = self.getFieldMapping(channelName)
        keys = list(mapped.keys())
        values = list(mapped.values())
        to_return = -1
        for i, key in enumerate(keys):
            if key == measure_type:
                to_return = values[i]
                to_return = ''.join(filter(lambda i: i.isdigit(), to_return))
                return to_return

    # add the fields in missingFields to the channel on thingspeak
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

                logging.debug("Added " + str(missingFields) + " to channel " + str(channelID))
        except Exception as e:
            logging.debug("Unable to add " + str(missingFields) + " to channel " + str(channelID))

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

            thread = ThreadHttpRequest(self._baseUri+"channels/"+str(self.getChannelID(channelName))+"/bulk_update.json", jsonBody, channelName)
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
            logging.debug("GET request went wrong")
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
            logging.error(f"Channel {channelName} feed DELETE went wrong")

    def removeChannel(self, channelName):
        #DELETE request
        #https://api.thingspeak.com/channels/CHANNEL_ID
        channelID=self.getChannelID(channelName)
        try:
            requests.delete(self._baseUri+"channels/"+channelID)
        except Exception:
            #exception
            logging.error(f"Channel {channelName} deletion was not possible")

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
            logging.error(f"PUT request went wrong")


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
            if r.status_code == 200:
                newChannel = r.json()
                for i,field_name in enumerate(fields_name):
                    newChannel["field"+str(i+1)]=field_name

                self._channels.append(newChannel)
                logging.debug("Thingspeak Channel " + channelName + " opened with success")
            else:
                logging.error("Unable to create a new channel " + channelName)
        except Exception as e:
            logging.error("Unable to create a new channel" + str(e))

    def getChannelApiKey(self, channelName, write=True):
        #function to return write/read channel API keys
        for channel in self._channels:
            if channel["name"]==channelName:
                for api_key in channel["api_keys"]:
                    if api_key["write_flag"]==write:
                        return api_key["api_key"]
        return "channelName not found"

    def readResultsData(self, channelName, field_id = -1, results = 8000):
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
        #SINGLE FIELD --> https://api.thingspeak.com/channels/channel_id/fields/field_id.json?api_key=self._thingspeak_api_key&results=1&
        #ALL FIELDS --> https://api.thingspeak.com/channels/<channel_id>/feeds.json
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        parameters="api_key="+read_api_key+"&results="+str(results)
        #read data from a single field
        if field_id != -1:
            uri = self._baseUri+"channels/"+str(channelID)+"/fields/"+str(field_id)+".json?"+parameters
        #read data from all fields
        else:
            uri=self._baseUri+"channels/"+str(channelID)+"/feeds.json?"+parameters
        try:
            r = requests.get(uri)
            logging.debug(f"GET request with the following uri: {uri}")
            return r.json()
            #print(f"[THINGSPEAKADAPTOR][INFO] Response = {r.json()}")
        except Exception:
            logging.debug(f"GET request to read data from ThingSpeak went wrong")
    def readDaysData(self, channelName, field_id = -1, days = 1):
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        parameters="api_key="+read_api_key+"&days="+str(days)
        if field_id != -1:
            uri = self._baseUri+"channels/"+str(channelID)+"/fields/"+str(field_id)+".json?"+parameters
        else:
            uri=self._baseUri+"channels/"+str(channelID)+"/feeds.json?"+parameters
        try:
            r = requests.get(uri)
            logging.debug(f"GET request with the following uri: {uri}")
            return r.json()
        except Exception:
            logging.debug(f"GET request to read data from ThingSpeak went wrong")

    def getFeedsGroupId(self, groupId, type, minutes = 1440):
        channelName = []
        ret = []
        r = requests.get(self._catalogAddress + "/searchByGroupId?groupId=" + groupId)
        if r.status_code == 200:
            for channel in r.json():
                print("ASD")
                if "devicePosition" in channel and channel["devicePosition"] == type:
                    ret.append(self.readMinutesData(channel["serviceId"], minutes=minutes))

        return ret

    def readMinutesData(self, channelName, field_id = -1, minutes = 1440):
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        parameters="api_key="+read_api_key+"&minutes="+str(minutes)
        if field_id != -1:
            uri = self._baseUri+"channels/"+str(channelID)+"/fields/"+str(field_id)+".json?"+parameters
        else:
            uri=self._baseUri+"channels/"+str(channelID)+"/feeds.json?"+parameters
        try:
            r = requests.get(uri)
            logging.debug(f"GET request with the following uri: {uri}")
            return r.json()
        except Exception:
            logging.debug(f"GET request to read data from ThingSpeak went wrong")
    def readStartEndData(self, channelName, start = changeDatetimeFormat(datetime.datetime.now() - timedelta(days=7)), end = changeDatetimeFormat(datetime.datetime.now() + timedelta(days=1)), field_id = -1):
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        #start=changeDatetimeFormat(start)
        #end=changeDatetimeFormat(end)
        if start > end:
            return json.dumps({"error":{"status": 404, "message": "Start parameter must be previous with respect to end one"}}, indent=4)
        parameters="api_key="+read_api_key+"&start="+start+"&end="+end
        if field_id != -1:
            uri = self._baseUri+"channels/"+str(channelID)+"/fields/"+str(field_id)+".json?"+parameters
        #read data from all fields
        else:
            uri=self._baseUri+"channels/"+str(channelID)+"/feeds.json?"+parameters

        try:
            r =requests.get(uri)
            logging.debug(f"GET request with the following uri: {uri}")
            return r.json()
            #print(f"[THINGSPEAKADAPTOR][INFO] Response = {r.json()}")
        except Exception:
            logging.debug(f"GET request from ThingSpeak went wrong")
    def readSumAvgMed(self, channelName, field_id = -1, sum = 0, average = 0, median = 0):
        #https://api.thingspeak.com/channels/<channel_id>/feeds.json
        channelID=self.getChannelID(channelName)
        read_api_key=self.getChannelApiKey(channelName, False)
        parameters="api_key="+read_api_key+"&sum="+str(sum)+"&average="+str(average)+"&median="+str(median)
        if field_id != -1:
            uri = self._baseUri+"channels/"+str(channelID)+"/fields/"+str(field_id)+".json?"+parameters
        #read data from all fields
        else:
            uri=self._baseUri+"channels/"+str(channelID)+"/feeds.json?"+parameters

        try:
            r =requests.get(uri)
            logging.debug(f"GET request with the following uri: {uri}")
            return r.json()
            #logging.debug(f"Response = {r.json()}")
        except Exception:
            logging.error(f"GET request from ThingSpeak went wrong")
    def GET(self, *uri, **params):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        #uri format
        #https:localhost:port/channel/channelName/feeds?...
        #https:localhost:port/channel/channelName/field/fieldNumber/functionality?
        if len(uri) != 0:
            if uri[0] == "group":
                groupId = uri[1]
                #http://172.20.0.6:8080/group/home1/getExternalFeeds?minutes=10
                if uri[2] == "getExternalFeeds" and 'minutes' in params:
                    print(groupId)
                    return json.dumps(self.getFeedsGroupId(groupId, "external", minutes=params['minutes']), indent=3)
                if uri[2] == "getInternalFeeds" and 'minutes' in params:
                    return json.dumps(self.getFeedsGroupId(groupId, "internal", minutes=params['minutes']), indent=3)

            if uri[0] == "channel" and len(uri) > 2:
                channelName = uri[1]
                if uri[2] == "feeds" and len(uri) > 3:
                    #function to test
                    # 1 results
                    # 2 days
                    # 3 minutes
                    # 4 start/end
                    # 5 sum
                    # 6 average
                    # 7 median
                    if uri[3] == "getResultsData" and 'results' in params:
                        return json.dumps(self.readResultsData(channelName, results=params['results']), indent=3)
                    elif uri[3] == "getDaysData" and 'days' in params:
                        return json.dumps(self.readDaysData(channelName, days=params['days']), indent=3)
                    elif uri[3] == "getMinutesData" and 'minutes' in params:
                        return json.dumps(self.readMinutesData(channelName, minutes=params['minutes']), indent=3)
                    elif uri[3] == "getStartEndData" and 'start' in params and 'end' in params:
                        return json.dumps(self.readStartEndData(channelName, start=params['start'], end=params['end']), indent=3)
                    elif uri[3] == "getStartEndData" and 'start' in params:
                        return json.dumps(self.readStartEndData(channelName, start=params['start']), indent=3)
                    elif uri[3] == "getStartEndData" and 'end' in params:
                        return json.dumps(self.readStartEndData(channelName, end=params['end']), indent=3)
                    elif uri[3] == "getSum" and 'sum' in params:
                        return json.dumps(self.readSumAvgMed(channelName, sum=params['sum']), indent=3)
                    elif uri[3] == "getAvg" and 'average' in params:
                        return json.dumps(self.readSumAvgMed(channelName, average=params['average']), indent=3)
                    elif uri[3] == "getMedian" and 'median' in params:
                        return json.dumps(self.readSumAvgMed(channelName, median=params['median']), indent=3)
                    else:
                        cherrypy.response.status = 404
                        return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)

                elif uri[2] == "measureType" and len(uri) > 4:
                    measureType = uri[3]
                    fieldNumber = self.getFieldNumber(channelName, measureType)
                    if fieldNumber != None:
                        if uri[4] == "getResultsData" and 'results' in params:
                            return json.dumps(self.readResultsData(channelName, fieldNumber, results=params['results']), indent=3)
                        elif uri[4] == "getDaysData" and 'days' in params:
                            return json.dumps(self.readDaysData(channelName, fieldNumber, days=params['days']), indent=3)
                        elif uri[4] == "getMinutesData" and 'minutes' in params:
                            return json.dumps(self.readMinutesData(channelName, fieldNumber, minutes=params['minutes']), indent=3)
                        elif uri[4] == "getStartEndData" and 'start' in params and 'end' in params:
                            return json.dumps(self.readStartEndData(channelName, start=params['start'], end=params['end'], field_id=fieldNumber), indent=3)
                        elif uri[4] == "getStartEndData" and 'start' in params:
                            return json.dumps(self.readStartEndData(channelName, start=params['start'], field_id=fieldNumber), indent=3)
                        elif uri[4] == "getStartEndData" and 'end' in params:
                            return json.dumps(self.readStartEndData(channelName, end=params['end'], field_id=fieldNumber), indent=3)
                        elif uri[4] == "getSumData" and 'sum' in params:
                            return json.dumps(self.readSumAvgMed(channelName, fieldNumber, sum=params['sum']), indent=3)
                        elif uri[4] == "getAvgData" and 'average' in params:
                            return json.dumps(self.readSumAvgMed(channelName, fieldNumber, average=params['average']), indent=3)
                        elif uri[4] == "getMedian" and 'median' in params:
                            return json.dumps(self.readSumAvgMed(channelName, fieldNumber, median=params['median']), indent=3)
                        else:
                            cherrypy.response.status = 404
                            return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
                    else:
                        return json.dumps({"error":{"status": 404, "message": "Wrong measure type specified"}}, indent=4)
                else:
                    cherrypy.response.status = 404
                    return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
            else:
                cherrypy.response.status = 404
                return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
        else:
            return json.dumps({"message": "ThingSpeak Adaptor API endpoint"}, indent=4)



if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            }
    }
    availableServices = [
            {
                "serviceType": "REST",
                "serviceIP": NetworkUtils.getIp(),
                "servicePort": 8080,
                "endPoint": [
                    {
                        "type": "web",
                        "uri": "/",
                        "version": 1,
                        "parameter": []
                    },
                    {
                        "type": "web",
                        "uri": "/group/<groupId>/getExternalFeeds",
                        "uri_parameters":[{"name":"groupId","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "minutes", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/group/<groupId>/getInternalFeeds",
                        "uri_parameters":[{"name":"groupId","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "minutes", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getResultsData",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "results", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getDaysData",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "days", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getMinutesData",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "minutes", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getStartEndData",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "start", "unit": "datetime"},{"name":"end", "unit":"datetime"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getSum",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "sum", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getAvg",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "average", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/measureType/<measureType>/getMedian",
                        "uri_parameters":[{"name":"channelName","unit":"string"},{"name":"measureType", "unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "median", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getResultsData",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "results", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getDaysData",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "days", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getMinutesData",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "minutes", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getStartEndData",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "start", "unit": "datetime"},{"name":"end", "unit":"datetime"}],
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getSum",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "sum", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getAvg",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "average", "unit": "integer"}]
                    },
                    {
                        "type": "web",
                        "uri": "/channel/<channelName>/feeds/getMedian",
                        "uri_parameters":[{"name":"channelName","unit":"string"}],
                        "version": 1,
                        "parameter": [{"name": "median", "unit": "integer"}]
                    }
                ]
            }
    ]
    try:
        thingspeak_api_key = os.environ['THINGSPEAKAPIKEY']
        logging.debug("THINGSPEAKAPIKEY variabile set to: " + thingspeak_api_key)
    except:
        logging.error("THINGSPEAKAPIKEY variabile not set")
        thingspeak_api_key = ""

    rpi = ThinkSpeakAdaptor(
        settings,
        availableServices,
        thingspeak_api_key
        )
    rpi.start()

    # Remove reduntant date cherrypy log
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]
    cherrypy.log.error_log.setLevel(Logger.getLoggerLevel(settings.getField('logVerbosity')))

    app = cherrypy.tree.mount(rpi ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', rpi.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
