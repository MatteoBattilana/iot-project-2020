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

class SensorReader():
    def readSensors(self):
        simulatedValues = []
        simulatedValues.append({
            'n': 'humidity',
            'u': 'celsius',
            't': time.time(),
            'v': randrange(0, 100)
        })
        simulatedValues.append({
            'n': 'temperature',
            'u': 'celsius',
            't': time.time(),
            'v': randrange(-20, 40)
        })
        return simulatedValues

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getField('logFile'))
    conf={
            '/':{
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

    app = cherrypy.tree.mount(rpi ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', rpi.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
