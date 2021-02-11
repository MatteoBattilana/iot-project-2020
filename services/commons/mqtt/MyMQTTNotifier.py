# Class that only lists the callbacks fot the MyMQTT module 
class MyMQTTNotifier:
    def onMQTTConnected(self):
        pass
    def onMQTTConnectionError(self, error):
        pass
    def onMessageReceived(self, topic, message):
        pass
    def onUnexpectedDisconnect(self):
        pass
