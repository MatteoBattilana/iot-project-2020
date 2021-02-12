# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('../..'))
from services.commons.MQTTservice import *
from services.commons.sensorreader.realsensorreader import *
import json

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": settings['topic'],
                    "type": "temperature"
                }
            ]
        }
    ]
    rpi = MQTTservice(
            settings['pingTime'],
            settings['deviceId'],
            availableServices,
            None,
            PublisherInformation(RealSensorReader(), settings['topic'], settings['sensorSamplingTime'])
            )
    rpi.start()
    rpi.join()
