import sys, os
sys.path.insert(0, os.path.abspath('..'))
from services.commons.catalogadapter import *
from services.commons.mqtt.MyMQTT import *
from services.commons.mqtt.MyMQTTNotifier import *
import json
import threading
import schedule
import time

class Resource(CatalogAdapter, MyMQTTNotifier, threading.Thread):
    def __init__(self, pingTime, sensorSamplingTime, deviceId, MQTTtopic, serviceServiceList, serviceType, sensorReader, notifier = None, subscribeList = {}):
        super().__init__(deviceId, serviceServiceList, serviceType, None)
        threading.Thread.__init__(self)
        self.__pingTime = pingTime
        self.__sensorSamplingTime = sensorSamplingTime
        self.__sensorReader = sensorReader
        self.__deviceId = deviceId
        self.__MQTTtopic = MQTTtopic
        self.__notifier = notifier
        self.__subscribeList = subscribeList

        self.__scheduleSampling = None
        self.__scheduleMQTTRetry = None

    def run(self):
        self.__setupMQTT()                                                        #setup MQTT
        schedule.every(self.__pingTime).seconds.do(self.sendPing)               #schedule ping in every case
        print("[RESOURCE][INFO] Scheduled ping every " + str(self.__pingTime) + " s")
        while True:
            schedule.run_pending()                                              #run scheduled methods
            time.sleep(1)

    def __sendValue(self):
        val = self.__sensorReader.readSensors()
        ret = {
            "bn": self.__MQTTtopic,
            "e": val
        }
        self.__client.publish(self.__MQTTtopic, ret)
        print ("[RESOURCE][INFO] publishing '" + json.dumps(ret) + "' with topic " + self.__MQTTtopic)


    #return True if the MQTT is connected
    def __setupMQTT(self):
        broker = self.getBroker()
        if 'uri' in broker and 'port' in broker:
           print("[RESOURCE][INFO] Trying to connect to the MQTT broker")
           self.__client = MyMQTT(self.__deviceId, broker['uri'], broker['port'], self)
           self.__client.start()
        else:
           print("[RESOURCE][ERROR] No MQTT broker available")

    #MQTT callbacks
    def onMQTTConnected(self):
        print("[RESOURCE][INFO] Connected to the MQTT broker")
        self.__scheduleMQTTRetry = schedule.every(self.__sensorSamplingTime).seconds.do(self.__sendValue)
        print("[RESOURCE][INFO] Scheduled sampling values every " + str(self.__sensorSamplingTime) + " s")
        for elem in self.__subscribeList:
            self.__client.subscribe(elem)
            print("[RESOURCE][INFO] Subscribed to " + elem)

    def onMQTTConnectionError(self, error):
        print("[RESOURCE][ERROR] Disconnected from MQTT broker: " + error)
        self.__scheduleMQTTRetry = schedule.every(60).seconds.do(self.__setupMQTT)
        if self.__scheduleSampling != None:
            schedule.cancel(self.__scheduleSampling)

    def onMessageReceived(self, topic, message):
        if self.__notifier != None:
            self.__notifier.onMessageReceived(topic, message)

    def onDisconnect(self):
        print("[RESOURCE][ERROR] Disconnected from MQTT broker")
        self.__scheduleMQTTRetry = schedule.every(60).seconds.do(self.__setupMQTT)
        if self.__scheduleSampling != None:
            schedule.cancel(self.__scheduleSampling)
