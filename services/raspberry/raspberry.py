# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from services.commons.resource import Resource
from services.commons.sensorreader.realsensorreader import *
import json

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": "smarthome55544/led1/temp",
                    "type": "temperature"
                }
            ]
        }
    ]
    rpi = Resource(
            settings['pingTime'],
            settings['sensorSamplingTime'],
            settings['deviceId'],
            settings['topic'],
            availableServices,
            "SENSOR",
            RealSensorReader())
    rpi.start()
    rpi.join()
