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

class SensorReader():
    def readSensors(self):
        simulatedValues = []
        simulatedValues.append({
            'n': 'temperature',
            'u': 'celsius',
            't': time.time(),
            'v': randrange(-20, 40)
        })
        simulatedValues.append({
            'n': 'humidity',
            'u': 'celsius',
            't': time.time(),
            'v': randrange(0, 100)
        })
        return simulatedValues

if __name__=="__main__":
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    rpi = Device(SensorReader(), SettingsManager("settings.json"))
    rpi.start()
    cherrypy.tree.mount(rpi ,'/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', rpi.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
