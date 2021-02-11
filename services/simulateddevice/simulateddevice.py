# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('../..'))
from services.commons.device import Device
from services.commons.sensorreader.randomsequentialsensorreader import *
import json

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": settings['topic'] + "/temp",
                    "type": "temperature"
                },
                {
                    "type": "humidity",
                    "topic": settings['topic'] + "/hum"
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
        },
        {
            "n": "humidity",
            "u": "%",
            "min": 0,
            "max": 100,
            "startingValue": 32
        }])

    rpi = Device(
            settings['pingTime'],
            settings['sensorSamplingTime'],
            settings['deviceId'],
            settings['topic'],
            availableServices,
            sensorReader)
    rpi.start()
    rpi.join()
