# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
from commons.device import *
import cherrypy
from random import randrange
from commons.netutils import *
from commons.settingsmanager import *
import threading
import json
import time
import logging
from commons.logger import *
import requests

# Simulated sensor read by using a specific thingspeak channel that contains real time data
# This is only for testing due to missing hardware availability, but still works great because it
# give real data and not random ones
class SensorReader():
    def readSensors(self):
        simulatedValues = []
        try:
            r = requests.get("https://api.thingspeak.com/channels/297675/feeds.json?results=1")
            if r.status_code == 200:
                jsonBody = r.json()
                sim_temp = jsonBody["feeds"][0]["field1"]
                simulatedValues.append({
            'n': 'temperature',
            'u': 'celsius',
            't': time.time(),
            'v': sim_temp
        })
                sim_hum = jsonBody["feeds"][0]["field2"]
                simulatedValues.append({
            'n': 'humidity',
            'u': 'celsius',
            't': time.time(),
            'v': sim_hum
        })
        except Exception as e:
            logging.error(f"ThingSpeak GET request to read data went wrong")

        try:
            r = requests.get("https://api.thingspeak.com/channels/1207176/field/7.json?results=1")
            if r.status_code == 200:
                jsonBody = r.json()
                sim_co2 = jsonBody["feeds"][0]["field7"]
                simulatedValues.append({
            'n': 'co2',
            'u': 'ppm',
            't': time.time(),
            'v': sim_co2
            }
            )
        except Exception as e:
            logging.error(f"ThingSpeak GET request to read data went wrong")
        return simulatedValues

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    rpi = Device(SensorReader(), settings)
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
