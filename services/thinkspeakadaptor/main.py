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
    def __init__(self, pingTime, serviceList, serviceName, subscribeList, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceName, "SERVICE", groupId = None, notifier = self)
        self._subscribeList = subscribeList
        self._isMQTTconnected = False
        self._catalogAddress = catalogAddress
        self._mqtt = None

    def run(self):
        print("[INFO] Started")
        self._ping.start()

        while True:
            time.sleep(10)

    # Catalog new id callback
    def onNewCatalogId(self, newId):
        print("[INFO] New id from catalog: " + newId)
        if self._mqtt is not None:
            self._mqtt.stop()

        self._mqtt = MQTTRetry(newId, self, self._catalogAddress)
        self._mqtt.start()

    #MQTT callbacks
    def onMQTTConnected(self):
        pass
    def onMQTTConnectionError(self, error):
        pass
    def onMQTTMessageReceived(self, topic, message):
        # TODO: must send to ThinkSpeak
        print("Received new message with topic: " + topic)

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    availableServices = []
    rpi = ThinkSpeakAdaptor(
            settings['pingTime'],
            availableServices,
            settings['serviceName'],
            settings['subscribeTopics'],
            settings['catalogAddress']
        )
    rpi.start()
    rpi.join()
