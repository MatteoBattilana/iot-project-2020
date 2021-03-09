# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
from commons.device import *
import cherrypy
from random import random
from commons.netutils import *
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
            'v': random()
        })
        return simulatedValues

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": settings['MQTTTopic'],
                    "type": "temperature"
                }
            ]
        }
    ]
    conf={
            '/':{
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    rpi = Device(
            settings['pingTime'],
            settings['sensorSamplingTime'],
            availableServices,
            settings['deviceName'],
            settings['groupId'],
            settings['MQTTTopic'],
            settings['catalogAddress'],
            SensorReader()
        )
    rpi.start()
    cherrypy.tree.mount(rpi ,'/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.server.socket_port = 8822
    cherrypy.engine.subscribe('stop', rpi.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
