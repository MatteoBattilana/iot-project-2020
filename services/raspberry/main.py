# Path hack.
import re
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
import serial

# Class used to interface with the DHT11 module in order to read the humidity
# and interfaces also with the arduino in order to read the temperature and the co2
class SensorReader():
    def __init__(self):
        self.sensor=Adafruit_DHT.DHT11
        self.gpio=17

    def getArduinoThermistorTemperature(self):
            # read thermistor from arduino
            logging.debug("Asked arduino")
            try:
                i = 0
                ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
                ser.flush()
                while True:
                    if ser.in_waiting > 0:
                        try:
                            string_read = ser.readline().decode('utf-8').rstrip()
                            x = re.search("^T(.*)C(.*)E$", string_read)
                            if x:
                                logging.debug("From arduino: " + str(float(x[1])) + " " + str(float(x[2])))
                                return (float(x[1]), float(x[2]))
                        except:
                            pass
                    if i > 10:
                        return (None, None)
                    i+=1
                    time.sleep(0.5)
                return (None, None)
            except:
                return (None, None)

    # this method is a wrapped that is used to get the correct values from the
    # sensor by reading them multiple times and the performing an average
    def readSensors(self):
        humidity, temperature, co2 = (None, None, None)
        arduinoTemp, arduinoCo2 = self.getArduinoThermistorTemperature()
        co2 = arduinoCo2
        temperature = arduinoTemp

        # Use read_retry method. This will retry up to 15 times to
        # get a sensor reading (waiting 2 seconds between each retry).
        hr = []
        tr = []
        for i in range(5):
            h, t = Adafruit_DHT.read_retry(self.sensor, self.gpio)
            if h is not None:
                hr.append(h)
            if t is not None:
                tr.append(t)

        if len(hr) > 0 and humidity is None:
            humidity = sum(hr) / len(hr)
        if len(tr) > 0 and temperature is None:
            temperature = sum(tr) / len(tr)


        # Reading the DHT11 is very sensitive to timings and occasionally
        # the Pi might fail to get a valid reading. So check if readings are valid.
        simulatedValues = []
        if co2 is not None:
            simulatedValues.append({
                'n': 'co2',
                'u': 'ppm',
                't': time.time(),
                'v': co2
            })
        else:
            logging.warning("Invalid co2 from arduino")
        if temperature is not None:
            simulatedValues.append({
                'n': 'temperature',
                'u': 'celsius',
                't': time.time(),
                'v': temperature
            })
        else:
            logging.warning("Invalid temperature from sensor")
        if humidity is not None:
            simulatedValues.append({
                'n': 'humidity',
                'u': 'celsius',
                't': time.time(),
                'v': round(humidity)
            })
        else:
            logging.warning("Invalid humidity from sensor")
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
    rpi = Device(SensorReader(), settings, isExternal=True)
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
