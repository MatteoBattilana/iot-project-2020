import sys, os
sys.path.insert(0, os.path.abspath('..'))
from services.commons.mqtt.MyMQTT import *
from services.commons.mqtt.MyMQTTNotifier import *
from services.commons.ping import *
import json
import threading
import schedule
import requests
import time

class PublisherInformation:
    def __init__(self, sensorReader, MQTTpublisherTopic, sensorSamplingTime):
        self._sensorReader = sensorReader
        self._MQTTpublisherTopic = MQTTpublisherTopic
        self._sensorSamplingTime = sensorSamplingTime

class SubscriberInformation:
    def __init__(self, subscribeList, newMessageCallback):
        self._subscribeList = subscribeList
        self._newMessageCallback = newMessageCallback


# Module for services
class MQTTservice(MyMQTTNotifier, threading.Thread):
    def __init__(self, pingTime, serviceId, serviceServiceList, subscriberInformation = None, publisherInformation = None):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, "SERVICE", serviceServiceList, serviceId)
        self._serviceId = serviceId
        self._subscriberInformation = subscriberInformation
        self._publisherInformation = publisherInformation
        self._isMQTTconnected = False

        self._scheduleSampling = None
        self._scheduleMQTTRetry = None

    def run(self):
        self._ping.start()
        startingTime = time.time()                                                     #setup MQTT
        self._setupMQTT()
        while True:
            if self._isMQTTconnected == False:
                if time.time() - startingTime > 60:
                    self._setupMQTT()
                    startingTime = time.time()
            elif self._publisherInformation != None and time.time() - startingTime > self._publisherInformation._sensorSamplingTime:
                self._sendSensorValues()
                startingTime = time.time()

            time.sleep(1)

    def _getBroker(self):

        try:
            r = requests.get("http://127.0.0.1:8080/catalog/getBroker")
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print("[PING][ERROR] Unable to get the broker address: " + str(e))

        return {}

    def _sendSensorValues(self):
        val = self._publisherInformation._sensorReader.readSensors()
        ret = {
            "bn": self._serviceId,
            "e": val
        }
        self._client.publish(self._publisherInformation._MQTTpublisherTopic, ret)
        print ("[SERVICE][INFO] publishing '" + json.dumps(ret) + "' with topic " + self._publisherInformation._MQTTpublisherTopic)


    #return True if the MQTT is connected
    def _setupMQTT(self):
        broker = self._getBroker()
        if 'uri' in broker and 'port' in broker:
           print("[SERVICE][INFO] Trying to connect to the MQTT broker")
           self._client = MyMQTT(self._serviceId, broker['uri'], broker['port'], self)
           self._client.start()
        else:
           print("[SERVICE][ERROR] No MQTT broker available")

    #MQTT callbacks
    def onMQTTConnected(self):
        print("[SERVICE][INFO] Connected to the MQTT broker")
        if self._subscriberInformation != None:
            for elem in self._subscriberInformation._subscribeList:
                self._client.subscribe(elem)
                print("[SERVICE][INFO] Subscribed to " + elem)
        self._isMQTTconnected = True

    def onMQTTConnectionError(self, error):
        print("[SERVICE][ERROR] Disconnected from MQTT broker: " + error)
        self._isMQTTconnected = False


    def onMessageReceived(self, topic, message):
        if self._subscriberInformation != None and self._subscriberInformation._notifier != None:
            self._subscriberInformation._notifier.onMessageReceived(topic, message)

    def onUnexpectedDisconnect(self):
        print("[SERVICE][ERROR] Disconnected from MQTT broker")
        self._isMQTTconnected = False
