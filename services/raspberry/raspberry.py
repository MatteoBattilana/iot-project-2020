# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('../..'))
from services.commons.device import Device
from services.commons.sensorreader.realsensorreader import *
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
                }
            ]
        }
    ]
    rpi = Device(
            settings['pingTime'],
            settings['sensorSamplingTime'],
            settings['deviceId'],
            settings['topic'],
            availableServices,
            RealSensorReader())
    rpi.start()
    rpi.join()
