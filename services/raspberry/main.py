# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
from commons.device import *
from commons.settingsmanager import *
import cherrypy
from random import random
from commons.netutils import *
import threading
import json
import time
import Adafruit_DHT
import logging
from commons.logger import *

class SensorReader():
    def __init__(self):
        self.sensor=Adafruit_DHT.DHT11
        self.gpio=17

    def readSensors(self):
        # Use read_retry method. This will retry up to 15 times to
        # get a sensor reading (waiting 2 seconds between each retry).
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.gpio)

        # Reading the DHT11 is very sensitive to timings and occasionally
        # the Pi might fail to get a valid reading. So check if readings are valid.
        simulatedValues = []
        if humidity is not None and temperature is not None:
            simulatedValues.append({
                'n': 'temperature',
                'u': 'celsius',
                't': time.time(),
                'v': temperature
            })
            simulatedValues.append({
                'n': 'humidity',
                'u': 'celsius',
                't': time.time(),
                'v': humidity
            })
        return simulatedValues

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))
    conf={
            '/':{
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    rpi = Device(SensorReader(), settings, isExternal=True)
    rpi.start()

    # Remove reduntant date cherrypy log
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]

    app = cherrypy.tree.mount(rpi ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', rpi.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
