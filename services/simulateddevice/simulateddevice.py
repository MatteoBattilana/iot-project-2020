# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from services.commons.resource import Resource
from services.commons.sensorreader.randomsequentialsensorreader import *
import json

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": "smarthome55544/RPI1/temp",
                    "type": "temperature"
                }
            ]
        }
    ]
    sensorReader = RandomSequentialSensorReader([{
        "n": "temperature",
        "u": "Cel",
        "min": -10,
        "max": 35,
        "startingValue": 22
        }])

    rpi = Resource(
            settings['pingTime'],
            settings['sensorSamplingTime'],
            settings['deviceId'],
            settings['topic'],
            availableServices,
            "SENSOR",
            sensorReader)
    rpi.start()
    rpi.join()
