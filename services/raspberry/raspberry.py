from ping import *
import json

class Raspberry(Ping):
    def __init__(self, pingTime, serviceName, serviceServiceList, serviceType):
        super().__init__(pingTime, serviceName, serviceServiceList, serviceType)


if __name__=="__main__":
    settings = json.load(open("settings.json"))
    availableServices = [
        {
            "serviceType": "MQTT",
            "endPoint": [
                {
                    "topic": "smarthome55544/led1/temp",
                    "type": "temperature"
                }
            ]
        }
    ]
    rpi = Raspberry(settings['pingTime'], "RPI1", availableServices, "SENSOR")
    rpi.start()
    rpi.join()
