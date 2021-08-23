# Path hack.
import sys, os

import requests
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
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

        # Catalog new id callback
    def onNewCatalogId(self, newId):
        self._settings.updateField('serviceId', newId)

    def stop(self):
        self._ping.stop()

    def GET(self, *uri, **params):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if len(uri) == 0:
            return json.dumps({"message": "External weather API endpoint"}, indent=4)
        else:
            cherrypy.response.status = 503
            return json.dumps({"error":{"status": 503, "message": "OPENWETHERMAPAPIKEY not set"}}, indent=4)

    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'location':
            chat_id=msg['chat']['id']
            if self.t_m.getState(chat_id) == 'addGroupId_location':
                print(msg['location'])
                res = self.t_m.coordinate(chat_id,msg['location'],self._catalogAddress)
                if res:
                    self.bot.sendMessage(chat_id, "Location correctly set!\nYou can now add devices by using the correct command")
                else:
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
                    self.bot.sendMessage(chat_id,self.t_m.register(chat_id,txt))
                    self.bot.deleteMessage(telepot.message_identifier(msg))
                    self.t_m.setState(chat_id,'start')

                elif self.t_m.getState(chat_id) == 'addGroupId_name':
                    if not txt in self.t_m.get_ids(chat_id):
                        self.bot.sendMessage(chat_id,self.t_m.add_id(chat_id,txt))
                        self.t_m.setState(chat_id,'addGroupId_location')
                        self.bot.sendMessage(chat_id, "Please send now the location of the groupId")
                    else:
                        self.bot.sendMessage(chat_id,'The inserted groupId is already registered. Insert a new one')

                elif self.t_m.getState(chat_id) == 'addSensor':
                    ## make request to device to check if pin is correct
                    if True:
                        self.bot.sendMessage(chat_id,self.t_m.add_sen(chat_id,params))
                        self.t_m.setState(chat_id,'start')

                else:
                    self.bot.sendMessage(chat_id,"Command not supported")
                    self.sendAllCommands(chat_id)





            elif txt.startswith('/cancel'):
                self.t_m.setState(chat_id,'start')
                self.bot.sendMessage(chat_id,"Operation cancelled")

           #ok
            elif txt.startswith('/start'):
                message="Welcome to iot service for monitoring air quality in you environments. Firstly you have to register to the service through the command /register and a password.\nTo see how to use this command please type /info to check all commands and their syntax.\n"
                alert="Remind to SAVE YOUR PASSWORD in order to avoid losing it and don't be able to log to you profile"
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
                self.t_m.setState(chat_id,'login')
                self.bot.sendMessage(chat_id,"Please insert the password of your account or cancel the login by typing /cancel")
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
                groupIds=self.t_m.get_ids(chat_id)
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
                groupIds=self.t_m.get_ids(chat_id)
                if len(groupIds) > 0:
                    kbs=self.t_m.build_keyboard(groupIds,'addDevice')
                    keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                    self.bot.sendMessage(chat_id,"Which groupId do you want to add a sensor?",reply_markup=keyboard)
                else:
                    self.bot.sendMessage(chat_id,"No groupId in your account, please insert one.")

            elif txt.startswith('/delgroupid'):
                groupIds=self.t_m.get_ids(chat_id)
                if len(groupIds) > 0:
                    kbs=self.t_m.build_keyboard(groupIds,'delete')
                    keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                    self.bot.sendMessage(chat_id,"Which groupId do you want to delete?",reply_markup=keyboard)
                else:
                    self.bot.sendMessage(chat_id,'No groupId in your account')

            else:
                self.bot.sendMessage(chat_id,"Command not supported")

    def sendAllCommands(self,chat_id):
        self.bot.sendMessage(chat_id,"List of all available commands:\n\n" + "\n".join(self.t_m.commands()))

    def deleteGroupId(self, chat_id, groupId):
        result = True
        # loop over all the sensors and remove the groupId
        for device in self.t_m.get_sensors(chat_id,groupId):
            result = result and deleteGroupIdDevice(device[1])

        if result:
            r = requests.get(self._catalogAddress + "/deleteGroupId?groupId=" + groupId)
            if r.status_code == 200:
                return True

        return False

    def deleteGroupIdDevice(self, deviceId):
        r = requests.get(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        logging.error(self._catalogAddress + "/searchById?serviceId=" + deviceId)
        if r.status_code != 200:
            logging.error("Unable to get information about service " + deviceId)

        # now perform set of the groupId to the device
        for service in r.json()['serviceServiceList']:
            if 'serviceType' in service and service['serviceType'] == 'REST':
                ip = service['serviceIP']
                port = service['servicePort']
                # perform set groupId
                r = requests.get('http://' + ip + ":" + str(port) + "/deleteGroupId")
                if r.status_code != 200:
                    logging.error("Unable to remove device " + deviceId)
                    return False

        return True

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
                    self.t_m.setState(chat_id,'addSensor')
                    self.bot.sendMessage(chat_id, 'Please insert the device in the following format: <id> <PIN>')
                else:
                    self.t_m.setState(chat_id,'addGroupId_location')
                    self.bot.sendMessage(chat_id,'Attention: before doing other actions you have to send position of groupId {}'.format(self.t_m.currentId(chat_id)))

            elif txt[0]=='groupId':
                id_sensor=self.t_m.get_sensors(chat_id,txt[1])
                if len(id_sensor) > 0:
                    kbs=self.t_m.build_keyboard(id_sensor,'devices')
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])#questo modo di scrivere mi fa fare in colonna, in riga insieme lista
                    self.bot.sendMessage(chat_id,"Which device?",reply_markup=keyboard)
                else:
                    self.bot.sendMessage(chat_id,'No device available for this groupId')

            # for the selected device is ask if u want datas o thingspeak
            elif txt[0]=='devices':
                kbs=self.t_m.build_keyboard(['datas','thingspeak'],txt[1])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                self.bot.sendMessage(chat_id,"What do you want: actual datas or thingspeak?",reply_markup=keyboard)
            #one selected what do u want,choose with characteristic u want
            elif (txt[1]=='datas' or txt[1]=='thingspeak'): #contorta ma funziona,query=(id_sensore cosaVoglio)
                txt.reverse()
                kbs=self.t_m.build_keyboard(['temperature','CO2','humidity'],txt[0]+' '+txt[1])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                self.bot.sendMessage(chat_id,"What do you want?",reply_markup=keyboard)

            #one decided al the path, returns what user wants
            elif txt[2]=='temperature':
                if txt[0]=='datas':
                    self.bot.sendMessage(chat_id,text="You selected temperature of %s" %txt[1])
                #qui dovro mettere la richiesta get per accedere ai dati reali
                else:
                #qui richiesta get per richiedere il grafico a thigspeak
                    self.bot.sendPhoto(chat_id,'https://cdn.getyourguide.com/img/location/5a0838201565b.jpeg/92.jpg')#mandare foto
                    self.bot.sendMessage(chat_id,text="temperature graph from %s \n" %txt[1])
            elif txt[2]=='CO2':
                if txt[0]=='datas':
                    self.bot.sendMessage(chat_id,text="You selected CO2 of %s\n" %txt[1])
                else:
                    self.bot.sendPhoto(chat_id,'https://www.milanretreats.com/wp-content/uploads/2020/01/milanretreats_img_slide.jpg')
                    self.bot.sendMessage(chat_id,text="CO2 graph from %s \n" %txt[1])
            elif txt[2]=='humidity':
                if txt[0]=='datas':
                    self.bot.sendMessage(chat_id,text="You selected humidity of %s" %txt[1])
                #qui dovro mettere la richiesta get per accedere ai dati reali
                else:
                #qui richiesta get per richiedere il grafico a thigspeak
                    self.bot.sendPhoto(chat_id,'https://images.lacucinaitaliana.it/wp-content/uploads/2018/05/18183720/roma-primavera-1600x800.jpg')#mandare foto
                    self.bot.sendMessage(chat_id,text="humidity graph from %s \n" %txt[1])



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
