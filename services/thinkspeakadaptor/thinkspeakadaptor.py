# Path hack.
import sys, os
print(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.abspath('../..'))
from services.commons.MQTTservice import *
import json
import socket

class ThinkSpeakAdaptor(MQTTservice):
    def __init__(self, pingTime, serviceId, serviceServiceList, subscribeList):
        super().__init__(
            pingTime,
            serviceId,
            serviceServiceList,
            SubscriberInformation(subscribeList, self),
            None
        )

    def onMessageReceived(self, topic, message):
        print (topic + " -> " + json.dumps(json.loads(message)))

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "REST",
            "serviceIP": get_ip(),
            "servicePort": 1234,
            "endPoint": [
                {
                    "type": "temperature",
                    "uri": "temp",
                    "parameter": []
                },
                {
                    "type": "humidity",
                    "uri": "hum",
                    "parameter": []
                },
                {
                    "type": "configuration",
                    "uri": "conf",
                    "parameter": [{"value": "integer", "name": "sampleTime"}]
                }
            ]
        }
    ]
    rpi = ThinkSpeakAdaptor(
            settings['pingTime'],
            settings['serviceId'],
            availableServices,
            settings['subscribeTopics'])
    rpi.start()
    rpi.join()
