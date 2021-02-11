from services.commons.sensorreader.sensorreader import SensorReader
import numpy as np
import random
import time
import json

# the list is as the following
#[{
#"n": "temperature",
#"u": "Cel",
#"min": 10,
#"max": 50,
#"startingValue": 33
#}, ..]

class RandomSequentialSensorReader(SensorReader):
    def __init__(self, list):
        self.__list = list

    def readSensors(self):
        simulatedValues = []
        for elem in self.__list:
            increment = 0.9 + 0.2 * random.random()
            simulatedValues.append({
                'n': elem['n'],
                'u': elem['u'],
                't': time.time(),
                'v': elem['startingValue'] * increment
            })
        return simulatedValues
