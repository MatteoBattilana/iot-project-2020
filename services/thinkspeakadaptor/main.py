# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.MQTTRetry import *
from commons.ping import *
import json
import socket
import time
from commons.netutils import *

class ThinkSpeakAdaptor(threading.Thread):
    def __init__(self, pingTime, serviceList, serviceId, subscribeList, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceId)
        self._mqtt = MQTTRetry(serviceId, self, catalogAddress)
        self._mqtt.subscribe(subscribeList)
        self._subscribeList = subscribeList
        self._isMQTTconnected = False


    def run(self):
        print("[THINGSPEAKADAPTOR][INFO] Started")
        self._ping.start()
        self._mqtt.start()

        while True:
            time.sleep(10)

    #MQTT callbacks
    def onMQTTConnected(self):
        self._isMQTTconnected = True
    def onMQTTConnectionError(self, error):
        self._isMQTTconnected = False
    def onMQTTMessageReceived(self, topic, message):
        print("Received: " + json.dumps(message, indent=4))

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = [
        {
            "serviceType": "REST",
            "serviceIP": NetworkUtils.getIp(),
            "servicePort": 1234,
            "endPoint": [                   #TODO: change to the correct one
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
            availableServices,
            settings['serviceId'],
            settings['subscribeTopics'],
            settings['catalogAddress']
        )
    rpi.start()
    rpi.join()
