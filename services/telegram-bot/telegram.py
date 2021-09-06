# Path hack.
import sys, os

import requests
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *
from io import BytesIO
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from Telegram_Manager import Telegram_Manager

from enum import Enum
from pprint import pprint
import time
import cherrypy
import datetime
import json
import os
import logging
from commons.logger import *
from commons.netutils import *
from commons.settingsmanager import *

commands=['- /login: for authentication',
        '- /register: register to the service',
        '- /logout: logout from the current session',
        '- /check: to get values from the devices',
        '- /addgroupid: add a new groupId to your account',
        '- /delgroupid: remove groupId from your account',
        '- /adddevice: add device to a specific groupId',
        '- /cancel: cancel the current operation']

class TelegramBot():
    exposed=True

    def __init__(self, settings, serviceList, telegram_token):
        self.t_m = Telegram_Manager('users.json')
        self._settings = settings
        self.user_groupId_map = {}
        self._catalogAddress = self._settings.getField('catalogAddress')
        self.bot = telepot.Bot(telegram_token)
        MessageLoop(self.bot, {'chat':self.on_chat_message, 'callback_query':self.on_callback_query}).run_as_thread()
        self._ping = Ping(
            int(self._settings.getField('pingTime')),
            serviceList,
            self._settings.getField('catalogAddress'),
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getField('serviceId'),
            "TELEGRAM-BOT",
            groupId = None)
        logging.debug("Started")
        self._ping.start()

        # Telegram keepAlive to avoid issue https://github.com/nickoala/telepot/issues/225
        self._runKeepAlive = True
        self._keepAliveThread = threading.Thread(target=self.__keepAliveThread)
        self._keepAliveThread.daemon = True
        self._keepAliveThread.start()

    def __keepAliveThread(self):
        lastTime = 0
        while self._runKeepAlive:
            if time.time() - lastTime >= 60:
                logging.debug("Sending keep alive to Telegram")
                try:
                    self.bot.getMe()
                except:
                    logging.error("Unable to send keep alive to Telegram")
                lastTime = time.time()
            time.sleep(1)

        # Catalog new id callback
    def onNewCatalogId(self, newId):
        self._settings.updateField('serviceId', newId)

    def stop(self):
        self._ping.stop()
        self._runKeepAlive = False
        self._keepAliveThread.join()

    def GET(self, *uri, **params):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if len(uri) == 0:
            return json.dumps({"message": "Telegram bot API endpoint"}, indent=4)
        else:
            cherrypy.response.status = 404
            return json.dumps({"error":{"status": 404, "message": "API not available"}}, indent=4)

    def POST(self, *uri):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        body = json.loads(cherrypy.request.body.read())

        if len(uri) == 0:
            return json.dumps({"message": "Telegram bot API endpoint"}, indent=4)
        elif len(uri) == 1:
            logging.info("Requested POST with uri " + str(uri))
            if uri[0] == 'sendAlert':
                # send message via telegram
                chatId = self.t_m.getChatId(body["groupId"])
                if chatId:
                    alertMessage = "ALERT\nMessage: "+ body["alert"] + "\nSuggested action: " + body["action"]
                    if "furtherInfo" in body and body["furtherInfo"]:
                         alertMessage = alertMessage + " due to " + body["furtherInfo"]
                    if "hourSuggestion" in body and body["hourSuggestion"]:
                        alertMessage = alertMessage + "\n" + body["hourSuggestion"]
                    self.bot.sendMessage(chatId, text=alertMessage)
                    ret = body
                else:
                    cherrypy.response.status = 503
                    logging.error("Missing groupId and chat_id Telegram reference")
                    ret = {"error":{"status": 404, "message": "Missing groupId and chat_id Telegram reference"}}

            else:
                cherrypy.response.status = 404
                ret = {"error":{"status": 404, "message": "Missing uri"}}
        else:
            ret = {"error":{"status": 404, "message": "Missing uri"}}
        return json.dumps(ret, indent=4)

    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'location':
            chat_id=msg['chat']['id']
            if self.t_m.getState(chat_id) == 'addGroupId_location':
                pos = msg['location']
                try:
                    r = requests.get(self._catalogAddress + "/updateGroupId?groupId=" + self.t_m.getCurrentGroupId(chat_id) + "&latitude=" + str(pos["latitude"]) + "&longitude="+ str(pos["longitude"]))
                    if r.status_code == 200:
                        self.t_m.coordinate(chat_id,msg['location'])
                        self.bot.sendMessage(chat_id, "Location correctly set!\nYou can now add devices by using the correct command")
                    else:
                        logging.error("Unable to set the location for groupId: " + str(r.json()))
                        self.bot.sendMessage(chat_id, "Unable to set the groupId location due to some server problems. Retry later")
                except:
                    logging.error("Unable to set the location for groupId: " + str(r.json()))
                    self.bot.sendMessage(chat_id, "Unable to set the groupId location due to some server problems. Retry later")
            #variabile globale location che viene modificata, se None l /IdAdd dira inserisci prima posto con location, senno inserisco coordinate con add_id


        elif content_type=='text':
            chat_id=msg['chat']['id'] #chat_id identification
            name=msg["from"]["username"] #account name
            txt=msg['text'] #message sent
            params = txt.split()
            status = self.t_m.status(chat_id)
            print(params)
            par_len = len(params)

            if not txt.startswith('/'):
                if self.t_m.getState(chat_id) == 'login':
                    auth, message = self.t_m.login(chat_id,txt)
                    self.bot.sendMessage(chat_id,message)
                    if auth == True:
                        self.t_m.setState(chat_id,'start')
                        self.bot.deleteMessage(telepot.message_identifier(msg))
                    else:
                        self.t_m.setState(chat_id,'login')

                elif self.t_m.getState(chat_id) == 'register':
                    if txt:
                        self.bot.sendMessage(chat_id,self.t_m.register(chat_id,txt))
                        # self.bot.deleteMessage(telepot.message_identifier(msg))
                        self.t_m.setState(chat_id,'start')

                elif self.t_m.getState(chat_id) == 'addGroupId_name':
                    if " " in txt:
                        self.bot.sendMessage(chat_id,"Please insert a name without spaces")
                    elif not txt in self.t_m.get_ids_name():
                        grId = txt + "_" + str(chat_id)
                        r = requests.get(self._catalogAddress + "/createGroupId?groupId=" + grId)
                        if r.status_code == 200:
                            self.bot.sendMessage(chat_id,self.t_m.add_id(chat_id,txt))
                            self.t_m.setState(chat_id,'addGroupId_location')
                            self.bot.sendMessage(chat_id, "Please send now the location of the groupId. The location will be used to give more precisely suggestion in order to increase the air quality")
                        elif r.status_code == 409:
                            self.bot.sendMessage(chat_id, "Unable to create the groupId because the name is already in use. Please use a different one.")
                        else:
                            logging.error("Unable to create the groupId: " + str(r.json()))
                            self.bot.sendMessage(chat_id, "Unable to create the groupId due to some server problems. Retry later")

                    else:
                        self.bot.sendMessage(chat_id,'The inserted groupId is already registered. Insert a new one')

                elif self.t_m.getState(chat_id) == 'addDevice':
                    ## make request to device to check if pin is correct
                    if par_len == 2:
                        if not self.t_m.isDeviceAlreadyPresent(params[0]):
                            res = self.setDeviceGroupId(params[0], params[1], self.t_m.getCurrentGroupId(chat_id))
                            if res == None:
                                self.bot.sendMessage(chat_id, "Unable to find " + params[0] + " device, please check if it is correct")
                            elif res:
                                self.bot.sendMessage(chat_id,self.t_m.add_sen(chat_id,params))
                                self.t_m.setCurrentDeviceId(chat_id, params[0])
                                self.t_m.setState(chat_id,'device_position')
                                keyboard = ReplyKeyboardMarkup(keyboard=[['Internal', 'External']])
                                self.bot.sendMessage(chat_id, 'Is the device positioned internally or externally with the respect to your room?', reply_markup=keyboard)
                            else:
                                self.bot.sendMessage(chat_id, "Unable to add sensor " + params[0] + " to the " + self.t_m.getCurrentGroupIdName(chat_id) + " groupId, check the pin and retry")
                        else:
                            self.bot.sendMessage(chat_id, "Device already added, please select a different one or remove it from the other account")
                    else:
                        self.bot.sendMessage(chat_id, "Please use the following format: <deviceId> <PIN>")

                elif self.t_m.getState(chat_id) == 'device_position':
                    if txt == 'Internal' or txt == 'External':
                        deviceId = self.t_m.getCurrentDeviceId(chat_id)
                        if self.setDevicePosition(deviceId, txt.lower()):
                            self.t_m.setDevicePosition(chat_id, deviceId, txt.lower())
                            self.t_m.setCurrentDeviceId(chat_id, "")
                            self.t_m.setState(chat_id,'start')
                            self.bot.sendMessage(chat_id, deviceId + " correctly configured!", reply_markup=ReplyKeyboardRemove())
                        else:
                            self.bot.sendMessage(chat_id, "Unable to configure device position. Please retry later")
                    else:
                        self.bot.sendMessage(chat_id, "Wrong position, use only Internal or External")
                else:
                    self.bot.sendMessage(chat_id,"Command not supported")
                    self.sendAllCommands(chat_id)



            elif txt.startswith('/cancel'):
                self.t_m.setState(chat_id,'start')
                self.bot.sendMessage(chat_id,"Operation cancelled \u26A0")

           #ok
            elif txt.startswith('/start'):
                message="Welcome to iot service for monitoring air quality in you environments. Firstly you have to register to the service through the command /register and a password.\nTo see how to use this command please type /info to check all commands and their syntax.\n"
                alert="\u26A0 Remind to SAVE YOUR PASSWORD in order to avoid losing it and don't be able to log to you profile"
                self.bot.sendMessage(chat_id,message)
                self.bot.sendMessage(chat_id,alert)
            #ok
            elif txt.startswith('/info'):
                if len(params)==1:
                    self.sendAllCommands(chat_id)
                else:
                    self.bot.sendMessage(chat_id,self.t_m.commands(params[0]))
            #ok
            elif txt.startswith('/login'):
                if(self.t_m.just_register(chat_id)):
                    self.t_m.setState(chat_id,'login')
                    self.bot.sendMessage(chat_id,"Please insert the password of your account or cancel the login by typing /cancel")
                else:
                    self.bot.sendMessage(chat_id,"Password not set, please use the /register command")

        #ok
            elif txt.startswith('/register'):
                if(not self.t_m.just_register(chat_id)):
                    self.t_m.setState(chat_id,'register')
                    self.bot.sendMessage(chat_id, "Insert the password for your account.")
                else:
                    self.bot.sendMessage(chat_id,'Your password is already set, please use the login command')
            #ok
            elif txt.startswith('/logout'):
                self.bot.sendMessage(chat_id,self.t_m.logout(chat_id))
                self.t_m.setState(chat_id,'start')

            elif not status:
                self.bot.sendMessage(chat_id,'Attention you are offline, please login')

            elif txt.startswith('/check'):
                if not self.isDevicePositionNotSet(chat_id):
                    groupIds=self.t_m.get_ids_name(chat_id)
                    if len(groupIds) > 0:
                        kbs=self.t_m.build_keyboard(groupIds,'groupId')
                        keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                        self.bot.sendMessage(chat_id,"Which groupId do you want to check?",reply_markup=keyboard)
                    else:
                        self.bot.sendMessage(chat_id,"No groupId in your account, please insert one.")

            elif txt.startswith('/addgroupid'):
                self.t_m.setState(chat_id,'addGroupId_name')
                self.bot.sendMessage(chat_id,"Please insert the name of the new groupId")

            elif txt.startswith('/adddevice'):
                if not self.isDevicePositionNotSet(chat_id):
                    groupIds=self.t_m.get_ids_name(chat_id)
                    if len(groupIds) > 0:
                        kbs=self.t_m.build_keyboard(groupIds,'addDevice')
                        keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                        self.bot.sendMessage(chat_id,"Which groupId do you want to add a sensor?",reply_markup=keyboard)
                    else:
                        self.bot.sendMessage(chat_id,"No groupId in your account, please insert one.")

            elif txt.startswith('/delete'):
                groupIds=self.t_m.get_ids_name(chat_id)
                if len(groupIds) > 0:
                    kbs=self.t_m.build_keyboard(groupIds,'delete')
                    keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                    self.bot.sendMessage(chat_id,"Which groupId do you want to delete?",reply_markup=keyboard)
                else:
                    self.bot.sendMessage(chat_id,'No groupId in your account')

                self.t_m.setState(chat_id,'start')

            else:
                self.bot.sendMessage(chat_id,"Command not supported")
                self.sendAllCommands(chat_id)

    def isDevicePositionNotSet(self, chat_id):
        missingPositionDevice = self.t_m.getCurrentDeviceId(chat_id)
        if missingPositionDevice:
            self.bot.sendMessage(chat_id, missingPositionDevice + ' is missing the position.')
            self.t_m.setState(chat_id,'device_position')
            keyboard = ReplyKeyboardMarkup(keyboard=[['Internal', 'External']])
            self.bot.sendMessage(chat_id, 'Is the device positioned internally or externally with the respect to your room?', reply_markup=keyboard)
            return True
        return False

    def sendAllCommands(self,chat_id):
        self.bot.sendMessage(chat_id,"List of all available commands:\n\n" + "\n".join(self.t_m.commands()))

    def deleteGroupId(self, chat_id, groupId):
        result = True
        # loop over all the sensors and remove the groupId
        for device in self.t_m.get_sensors(chat_id,groupId):
            result = result and self.deleteGroupIdDevice(device)

        if result:
            r = requests.get(self._catalogAddress + "/deleteGroupId?groupId=" + groupId + "_" + str(chat_id))
            return True

        return False

    def setDevicePosition(self, deviceId, position):
        r = requests.get(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        if r.status_code != 200:
            logging.error("Unable to get information about service " + deviceId)
            return False

        # now perform set of the groupId to the device
        for service in r.json()['serviceServiceList']:
            if 'serviceType' in service and service['serviceType'] == 'REST':
                ip = service['serviceIP']
                port = service['servicePort']
                # perform set groupId
                r = requests.get('http://' + ip + ":" + str(port) + "/setPosition?position="+position)
                if r.status_code == 200:
                    return True

        logging.error("Unable to set device position " + deviceId)
        return False

    def deleteGroupIdDevice(self, deviceId):
        r = requests.get(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        if r.status_code != 200:
            logging.error("Unable to get information about service " + deviceId)
            return False

        # now perform set of the groupId to the device
        for service in r.json()['serviceServiceList']:
            if 'serviceType' in service and service['serviceType'] == 'REST':
                ip = service['serviceIP']
                port = service['servicePort']
                # perform set groupId
                r = requests.get('http://' + ip + ":" + str(port) + "/deleteGroupId")
                if r.status_code == 200:
                    return True

        logging.error("Unable to remove device " + deviceId)
        return False

    def getData(self, deviceId, measureType):
        r = requests.get(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        logging.error(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        if r.status_code != 200:
            logging.error("Unable to get information about service " + deviceId)
            return {}

        # now perform set of the groupId to the device
        for service in r.json()['serviceServiceList']:
            if 'serviceType' in service and service['serviceType'] == 'REST':
                ip = service['serviceIP']
                port = service['servicePort']
                # perform set groupId
                try:
                    r = requests.get('http://' + ip + ":" + str(port) + "/getSensorValues")
                    if r.status_code != 200:
                        logging.error("Unable to request data from device " + deviceId + ". Retry later.")
                        return {}
                    else:
                        for i in r.json():
                            if i["n"] == measureType:
                                return {"value": i["v"], "unit" : i["u"]}
                except:
                    logging.error("Unable to request data from device " + deviceId + ". Retry later!")


        return {}



    def setDeviceGroupId(self, deviceId, pin, groupId):
        r = requests.get(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        if r.status_code != 200:
            logging.error("Unable to get information about service " + deviceId)
            return None

        # now perform set of the groupId to the device
        for service in r.json()['serviceServiceList']:
            if 'serviceType' in service and service['serviceType'] == 'REST':
                ip = service['serviceIP']
                port = service['servicePort']
                # perform set groupId
                try:
                    r = requests.get('http://' + ip + ":" + str(port) + "/setGroupId?groupId=" + str(groupId) + "&pin="+str(pin))
                    if r.status_code != 200:
                        logging.error("Unable to add device " + deviceId)
                        return False
                except:
                    return False

        return True

    def getGraph(self, sensor, measureType):
        r = requests.get(self._catalogAddress + "/searchByServiceSubType?serviceSubType=THINGSPEAK")
        if r.status_code != 200 or len(r.json()) == 0:
            logging.error("Unable to get information about THINGSPEAK service")
            return None

        # now perform set of the groupId to the device
        image = None
        for device in r.json():
            for service in device['serviceServiceList']:
                if 'serviceType' in service and service['serviceType'] == 'REST':
                    ip = service['serviceIP']
                    port = service['servicePort']
                    # perform set groupId
                    url = 'http://' + ip + ":" + str(port) + "/channel/" + sensor + "/measureType/" + measureType + "/getChart?days=1"
                    try:
                        r = requests.get(url)
                        if r.status_code != 200:
                            logging.error("Unable to download image " + url + " " + r.status_code)

                        output = BytesIO(r.content)
                        image = ('image.png', output)
                    except:
                        logging.error("Unable to download image 1 " + url)

        return image

    def getStatistics(self, groupId, measureType, period):
        r = requests.get(self._catalogAddress + "/searchByServiceSubType?serviceSubType=THINGSPEAK")
        if r.status_code != 200 or len(r.json()) == 0:
            logging.error("Unable to get information about THINGSPEAK service")
            return "Unable to get statistics for " + measureType + ". Retry later"

        # now perform set of the groupId to the device
        response = "Unable to get statistics for " + measureType + ". Retry later"
        for device in r.json():
            for service in device['serviceServiceList']:
                if 'serviceType' in service and service['serviceType'] == 'REST':
                    ip = service['serviceIP']
                    port = service['servicePort']
                    # perform set groupId
                    url = 'http://' + ip + ":" + str(port) + "/group/" + groupId + "/getStats?measureType=" + measureType + "&lapse="+period
                    try:
                        r = requests.get(url)
                        if r.status_code == 200:
                            body = r.json()
                            response = "Statistics for: {}\nAverage: {:0.2f}\nStandard deviation: {:0.2f}\nMin: {:0.2f}\nMax: {:0.2f}".format(measureType, body["average"], body["standard_deviation"], body["minimum"], body["maximum"])
                        else:
                            logging.error("Unable to get statistics " + url + " " + r.status_code)
                    except Exception as e:
                        logging.error("Unable to get statistics " + url + " " + str(e))

        return response

    def on_callback_query(self,msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        txt=query_data.split()
        #for a given group id display all sensor associated
        print(txt)
        if txt[0]=="delete":
                if len(txt)==2:
                    id_sensor=self.t_m.get_sensors(chat_id,txt[1])+["deleteGroupId"]
                    if len(id_sensor)>0:
                        kbs=self.t_m.build_keyboard(id_sensor,txt[0]+' '+txt[1]) #la scelta viene aggregata a questi txt e viene passata alla prox query
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                        self.bot.sendMessage(chat_id,"Which device?",reply_markup=keyboard)
                    else:
                        self.bot.sendMessage(chat_id,'No device available')
                elif txt[2]=='deleteGroupId':
                    if self.deleteGroupId(chat_id,txt[1]):
                        print(txt[2])
                        self.t_m.del_id(chat_id,txt[1])
                        self.bot.sendMessage(chat_id,'GroupId {} cancelled'.format(txt[1]))
                    else:
                        self.bot.sendMessage(chat_id,'Unable to delete GroupId {} due to some server error, please retry later'.format(txt[1]))

                else: # elimino sensore
                    if self.deleteGroupIdDevice(txt[2]):
                        self.t_m.del_sen(chat_id,txt[1:])
                        self.bot.sendMessage(chat_id,'Device {} of GoupId {} cancelled'.format(txt[2],txt[1]))
                    else:
                        self.bot.sendMessage(chat_id,'Unable to delete device {} from GroupId {} due to some server error, please retry later'.format(txt[2],txt[1]))

        else:
            if txt[0]=='addDevice':
                self.t_m.setCurrentId(chat_id,txt[1])
                if self.t_m.isLocationInserted(chat_id, txt[1]):
                    self.t_m.setState(chat_id,'addDevice')
                    self.bot.sendMessage(chat_id, 'Please insert the device in the following format: <id> <PIN>')
                else:
                    self.t_m.setState(chat_id,'addGroupId_location')
                    self.bot.sendMessage(chat_id,'Attention: before doing other actions you have to send position of groupId {}'.format(self.t_m.getCurrentGroupIdName(chat_id)))

            elif txt[0]=='groupId':
                id_sensor=self.t_m.get_sensors(chat_id,txt[1])
                if len(id_sensor) > 0:
                    kbs=self.t_m.build_keyboard(id_sensor + ["statistics"],'devices' + ' ' + txt[1])
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])#questo modo di scrivere mi fa fare in colonna, in riga insieme lista
                    self.bot.sendMessage(chat_id,"Which device or statistics?",reply_markup=keyboard)
                else:
                    self.bot.sendMessage(chat_id,'No device available for this groupId')


            elif len(txt)==3 and txt[2]=='statistics':
                kbs=self.t_m.build_keyboard(['temperature','humidity','co2'],txt[0]+' '+txt[1]+' '+txt[2])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                self.bot.sendMessage(chat_id,"What statistic do you want?",reply_markup=keyboard)

            elif len(txt)==4 and txt[2]=='statistics':
                kbs=self.t_m.build_keyboard(['daily','weekly','monthly'],txt[0]+' '+txt[1]+' '+txt[2]+' '+txt[3])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                self.bot.sendMessage(chat_id,"Which interval?",reply_markup=keyboard)

            elif len(txt)==5 and txt[2]=='statistics':
                self.bot.sendMessage(chat_id,self.getStatistics(txt[1] + "_" + str(chat_id), txt[3], txt[4]))

            # for the selected device is ask if u want datas o thingspeak
            elif txt[0]=='devices':
                kbs=self.t_m.build_keyboard(['datas','thingspeak'],txt[2])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                self.bot.sendMessage(chat_id,"What do you want: actual datas or thingspeak?",reply_markup=keyboard)
            #one selected what do u want,choose with characteristic u want
            elif (txt[1]=='datas' or txt[1]=='thingspeak'): #contorta ma funziona,query=(id_sensore cosaVoglio)
                txt.reverse()
                kbs=self.t_m.build_keyboard(['temperature','co2','humidity'],txt[0]+' '+txt[1])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                self.bot.sendMessage(chat_id,"What do you want?",reply_markup=keyboard)

            #one decided al the path, returns what user wants

            elif txt[2]=='temperature':
                if txt[0]=='datas':
                    reading = self.bot.sendMessage(chat_id, text="Reading temperature from sensor. Please wait")
                    value = self.getData(txt[1], txt[2])
                    self.bot.deleteMessage(telepot.message_identifier(reading))
                    if value:
                        self.bot.sendMessage(chat_id,text="The current temperature is: " + str(value["value"]) + "°")
                    else:
                        self.bot.sendMessage(chat_id, text="Unable to get current sensor value. Retry later")
                #qui dovro mettere la richiesta get per accedere ai dati reali
                elif txt[0]=='thingspeak':
                    #qui richiesta get per richiedere il grafico a thigspeak
                    reading = self.bot.sendMessage(chat_id, "Generating chart for temperature from ThingSpeak. Please wait")
                    image = self.getGraph(txt[1],"temperature")
                    self.bot.deleteMessage(telepot.message_identifier(reading))
                    if image:
                        self.bot.sendPhoto(chat_id,image) #mandare foto
                        self.bot.sendMessage(chat_id,text="temperature graph from %s \n" %txt[1])
                    else:
                        self.bot.sendMessage(chat_id, text="Unable to get the chart from thingspeak. Retry later")
            elif txt[2]=='co2':
                if txt[0]=='datas':
                    reading = self.bot.sendMessage(chat_id, text="Reading co2 from sensor. Please wait")
                    value = self.getData(txt[1], txt[2])
                    self.bot.deleteMessage(telepot.message_identifier(reading))
                    if value:
                        self.bot.sendMessage(chat_id,text="The current co2 is: " + str(value["value"]) + " " + value["unit"])
                    else:
                        self.bot.sendMessage(chat_id, text="Unable to get current sensor value. Retry later")
                elif txt[0]=='thingspeak':
                    reading = self.bot.sendMessage(chat_id, "Generating chart for co2 from ThingSpeak. Please wait")
                    image = self.getGraph(txt[1],"co2")
                    self.bot.deleteMessage(telepot.message_identifier(reading))
                    if image:
                        self.bot.sendPhoto(chat_id,image) #mandare foto
                        self.bot.sendMessage(chat_id,text="co2 graph from %s \n" %txt[1])
                    else:
                        self.bot.sendMessage(chat_id, text="Unable to get the chart from thingspeak. Retry later")

            elif txt[2]=='humidity':
                if txt[0]=='datas':
                    reading = self.bot.sendMessage(chat_id, text="Reading humidity from sensor. Please wait")
                    value = self.getData(txt[1], txt[2])
                    self.bot.deleteMessage(telepot.message_identifier(reading))
                    if value:
                        self.bot.sendMessage(chat_id,text="The current humidity is: " + str(value["value"]) + "%")
                    else:
                        self.bot.sendMessage(chat_id, text="Unable to get current sensor value. Retry later")
                #qui dovro mettere la richiesta get per accedere ai dati reali
                elif txt[0]=='thingspeak':
                    reading = self.bot.sendMessage(chat_id, "Generating chart for humidity from ThingSpeak. Please wait")
                    image = self.getGraph(txt[1],"humidity")
                    self.bot.deleteMessage(telepot.message_identifier(reading))
                    if image:
                        self.bot.sendPhoto(chat_id,image) #mandare foto
                        self.bot.sendMessage(chat_id,text="humidity graph from %s \n" %txt[1])
                    else:
                        self.bot.sendMessage(chat_id, text="Unable to get the chart from thingspeak. Retry later")



if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))
    availableServices = [
        {
            "serviceType": "REST",
            "serviceIP": NetworkUtils.getIp(),
            "servicePort": 8080,
            "endPoint": []
        }
    ]
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    try:
        telegramToken = os.environ['TELEGRAMTOKEN']
        logging.debug("TELEGRAMTOKEN found in ENV and set to: " + telegramToken)
    except:
        logging.error("TELEGRAMTOKEN variabile not set")
        telegramToken = ""  # write here the telegram token if you want to bypass the env variable

    restManager = TelegramBot(
        settings,
        availableServices,
        telegramToken
    )

    # Remove reduntant date cherrypy log
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]
    cherrypy.log.error_log.setLevel(Logger.getLoggerLevel(settings.getField('logVerbosity')))

    app = cherrypy.tree.mount(restManager ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', restManager.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
