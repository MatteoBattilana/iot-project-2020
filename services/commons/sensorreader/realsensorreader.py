from services.commons.sensorreader.sensorreader import SensorReader
import time

class RealSensorReader(SensorReader):
    def readSensors(self):
        return [{
                    "n": "beartbeat",
                    "u": "Bpm",
                    "t": time.time(),
                    "v": 22.5
                }]
