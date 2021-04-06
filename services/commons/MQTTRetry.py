import json
import threading
import requests
import time
import paho.mqtt.client as PahoMQTT
import logging

# Class that only lists the callbacks fot the MyMQTT module
class MyMQTTNotifier:
    def onMQTTConnected(self):
        pass
    def onMQTTConnectionError(self, error):
        pass
    def onMQTTMessageReceived(self, topic, message):
        pass

# Class for MQTT service, it automatically manages the retry to the MQTT broker
# in case of disconnection every 30s
class MQTTRetry(threading.Thread):
    def __init__(self, serviceId, notifier, catalogAddress):
        threading.Thread.__init__(self)
        self._serviceId = serviceId
        self._notifier = notifier
        self._catalogAddress = catalogAddress
        self._paho_mqtt = PahoMQTT.Client(serviceId, True)

		# register the callback
        self._paho_mqtt.on_connect = self._onConnect
        self._paho_mqtt.on_message = self._onMessageReceived
        self._paho_mqtt.on_disconnect = self._onDisconnect

        self._subscribeList = []

        self._isMQTTconnected = False
        self._isMQTTTryingConnecting = False
        self._scheduleMQTTRetry = None
        self._run = True

    def stop(self):
        self._run = False
        self.join()

    # Thread body necessary to perform the MQTT reconnection retry
    def run(self):
        lastTime = 0
        while self._run:
            if self._isMQTTconnected == False and self._isMQTTTryingConnecting == False and time.time() - lastTime > 30:
                self._setupMQTT()
                lastTime = time.time()
            time.sleep(1)

    # Return the selected broker from the catalog
    def _getBroker(self):
        try:
            r = requests.get(self._catalogAddress + "/getBroker")
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logging.error("Unable to get the broker address: " + str(e))
        return {}

    # publish a json message under the passed topic
    def publish(self, topic, msg):
        self._paho_mqtt.publish(topic, json.dumps(msg), 2)
        logging.debug("publishing '" + json.dumps(msg) + "' with topic " + topic)


    # connect to the MQTT brokerif a valid MQTT broker is returned from the catalog
    def _setupMQTT(self):
        self._isMQTTTryingConnecting = True
        try:
            broker = self._getBroker()
            if 'uri' in broker and 'port' in broker:
               logging.info("Trying to connect to the MQTT broker: " + broker['uri'] + ":" + str(broker['port']))

               self._paho_mqtt.connect(broker['uri'], broker['port'])
               self._paho_mqtt.loop_start()
            else:
               logging.error("No MQTT broker available")
        except Exception as e:
            self._isMQTTTryingConnecting = False
            logging.error("General error while connecting to the MQTT broker " + str(e))
        return {}

    # subscribe to a list of topic
    def subscribe(self, topicList):
        if self._isMQTTconnected == True:
            for topic in topicList:
                logging.debug("Subscribed to " + topic)
                self._paho_mqtt.subscribe(topic, 2)
        self._subscribeList = topicList


    #MQTT callbacks
    def _onDisconnect(self, client, userdata, rc):
        logging.error("Disconnected from MQTT broker: " + PahoMQTT.connack_string(rc))
        self._isMQTTconnected = False
        if self._notifier != None:
            self._notifier.onMQTTConnectionError(PahoMQTT.connack_string(rc))

    def _onConnect (self, paho_mqtt, userdata, flags, rc):
        if rc == 0:
            if self._notifier != None:
                self._notifier.onMQTTConnected()
            logging.info("Connected to the MQTT broker")
            for topic in self._subscribeList:
                logging.debug("Subscribed to " + topic)
                self._paho_mqtt.subscribe(topic, 2)
            self._isMQTTconnected = True
        else:
            logging.error("Unable to connect to the MQTT broker")
            if self._notifier != None:
                self._notifier.onMQTTConnectionError(PahoMQTT.connack_string(rc))

        self._isMQTTTryingConnecting = False

    def _onMessageReceived (self, paho_mqtt , userdata, msg):
		# A new message is received
        if self._notifier != None:
            self._notifier.onMQTTMessageReceived(msg.topic, json.loads(msg.payload))
