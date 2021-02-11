# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from services.commons.service import Service
import json
import socket

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
    rpi = Service(
            settings['pingTime'],
            settings['serviceId'],
            settings['topic'],
            availableServices)
    rpi.start()
    rpi.join()
