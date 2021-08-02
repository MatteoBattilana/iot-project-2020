# Path hack.
import sys, os

import requests
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from enum import Enum
from pprint import pprint
import time
import cherrypy
import datetime
import json
import os
import logging
import requests
from commons.logger import *
from commons.netutils import *
from commons.settingsmanager import *

class State(Enum):
    ASK_GROUP_ID = 1

chat_state = 0

user_groupId_map = {}



class TelegramBot():
    exposed=True

    def __init__(self, settings, serviceList, telegram_token):
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
            self._settings.getFieldOrDefault('serviceId', ''),
            "TELEGRAM-BOT",
            groupId = None,
            notifier = self)
        logging.debug("Started")
        self._ping.start()
        print('Listening ...')

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

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type=='text':
            chat_id=msg['chat']['id']
            command=msg['text']

            if command=='/start':
                self.bot.sendMessage(chat_id, 'Hello! This is the Telegram Bot for the IoT platform for user-involved air recirculation system. You can use the following commands:\n- /setGroupId to set the group id\n- /getData to get data from the system')        
            
            elif chat_id not in self.user_groupId_map:
                # The chat must ask which is the groupId the user needs to check
                if command[0] == '/':
                    self.bot.sendMessage(chat_id, 'The groupId has not been configured, type the id')
                    self.bot.sendMessage(chat_id, 'Please insert a valid groupId\n') 

                else:
                    # Set the groupId
                    try:
                        r = requests.get(self._catalogAddress + "/getAllGroupId")
                        if r.status_code == 200:
                            logging.debug("OK1")
                            if command in r.json():
                                logging.debug("OK2")
                                self.user_groupId_map[chat_id] = command
                                self.bot.sendMessage(chat_id, 'The groupId set to ' + command + ', now you can perform the normal requests')
                            else:
                                self.bot.sendMessage(chat_id, 'The groupId ' + command + ', is not valid. Insert a valid one')
                        else:
                            logging.error("Unable to get the groups from catalog")
                    except Exception as e:
                        logging.error("Unable to get the groups from catalog " + str(e))

            
            elif command=='/setGroupId':
                self.bot.sendMessage(chat_id, 'Please insert a valid groupId\n') 
                self.user_groupId_map.pop(chat_id, None)
    
            elif command=='/getData':
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Temperature', callback_data='temperature')],
                    [InlineKeyboardButton(text='C02', callback_data='c02')],
                    [InlineKeyboardButton(text='Humidity', callback_data='humidity')]],)
                self.bot.sendMessage(chat_id, 'What do you want to know?', reply_markup=keyboard)
            else :
                self.bot.sendMessage(chat_id, 'Invalid command!\n')

    def on_callback_query(self, msg): # come premo ritornano cose 
        logging.debug(msg)
        query_id, chat_ID, query_data = telepot.glance(msg, flavor='callback_query')
        print('Callback Query:', query_id, chat_ID, query_data)
        if query_data=='temperature':
            self.bot.sendMessage(chat_ID,text="The temperature is 25°\n")
        elif query_data=='c02':
            self.bot.sendMessage(chat_ID,text="The CO2 is 699 ppm \n")
        elif query_data=='humidity':
            self.bot.sendMessage(chat_ID,text="The humidity is 74% \n")

    def getMeasure(self, type, catalogAddress):


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
