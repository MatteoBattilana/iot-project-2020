import sys, os
sys.path.insert(0, os.path.abspath('..'))
from services.commons.catalogadapter import *
from services.commons.mqtt.MyMQTT import *
from services.commons.mqtt.MyMQTTNotifier import *
import json
import threading
import schedule
import time

class Service(CatalogAdapter, MyMQTTNotifier, threading.Thread):
    def __init__(self, pingTime, serviceId, MQTTtopic, serviceServiceList, notifier = None, subscribeList = {}):
        super().__init__(serviceId, serviceServiceList, "SERVICE", None)
        threading.Thread.__init__(self)
        self.__pingTime = pingTime
        self.__serviceId = serviceId
        self.__MQTTtopic = MQTTtopic
        self.__notifier = notifier
        self.__subscribeList = subscribeList

        self.__scheduleSampling = None
        self.__scheduleMQTTRetry = None

    def run(self):
        self.__setupMQTT()                                                        #setup MQTT
        schedule.every(self.__pingTime).seconds.do(self.sendPing)               #schedule ping in every case
        print("[SERVICE][INFO] Scheduled ping every " + str(self.__pingTime) + " s")
        while True:
            schedule.run_pending()                                              #run scheduled methods
            time.sleep(1)


    #return True if the MQTT is connected
    def __setupMQTT(self):
        broker = self.getBroker()
        if 'uri' in broker and 'port' in broker:
           print("[SERVICE][INFO] Trying to connect to the MQTT broker")
           self.__client = MyMQTT(self.__serviceId, broker['uri'], broker['port'], self)
           self.__client.start()
        else:
           print("[SERVICE][ERROR] No MQTT broker available")

    #MQTT callbacks
    def onMQTTConnected(self):
        print("[SERVICE][INFO] Connected to the MQTT broker")
        for elem in self.__subscribeList:
            self.__client.subscribe(elem)
            print("[SERVICE][INFO] Subscribed to " + elem)

    def onMQTTConnectionError(self, error):
        print("[SERVICE][ERROR] Disconnected from MQTT broker: " + error)
        self.__scheduleMQTTRetry = schedule.every(60).seconds.do(self.__setupMQTT)

    def onMessageReceived(self, topic, message):
        if self.__notifier != None:
            self.__notifier.onMessageReceived(topic, message)

    def onUnexpectedDisconnect(self):
        print("[SERVICE][ERROR] Disconnected from MQTT broker")
        self.__scheduleMQTTRetry = schedule.every(60).seconds.do(self.__setupMQTT)
