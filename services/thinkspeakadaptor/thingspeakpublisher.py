import paho.mqtt.publish as publish

class ThingSpeakPublisher:
    def publish(channelID, apiKey, tPayload):
        mqttHost = "mqtt.thingspeak.com"
        tTransport = "tcp"
        tPort = 1883
        tTLS = None
        topic = "channels/" + channelID + "/publish/" + apiKey

        publish.single(topic, payload=tPayload, hostname=mqttHost, port=tPort, tls=tTLS, transport=tTransport)
