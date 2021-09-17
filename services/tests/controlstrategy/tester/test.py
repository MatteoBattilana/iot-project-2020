from MyMQTT import *
import time
import threading
import socket
import requests
import json
import os
import cherrypy
import unittest

restCallLogPost = []
restCallLogGet = []
restMapper = {}

# Used to send ping to client
class Ping(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._run = True

    def getIp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = socket.gethostname()
        finally:
            s.close()
        return IP

    def stop(self):
        self._run = False

    def run(self):
        externalweatherapi = {
            "serviceId": "EXTERNAL-API-TEST",
            "serviceName": "EXTERNAL-API",
            "serviceType": "SERVICE",
            "serviceSubType": "EXTERNALWEATHERAPI",
              "serviceServiceList": [
                {
                    "serviceType": "REST",
                    "serviceIP": self.getIp(),
                    "servicePort": 8080,
                    "endPoint": []
                }
              ]
        }
        telegrambot = {
            "serviceId": "TELEGRAM-BOT-TEST",
            "serviceName": "TELEGRAM-BOT",
            "serviceType": "SERVICE",
            "serviceSubType": "TELEGRAM-BOT",
              "serviceServiceList": [
                {
                    "serviceType": "REST",
                    "serviceIP": self.getIp(),
                    "servicePort": 8080,
                    "endPoint": []
                }
              ]
        }

        while self._run:
            r = requests.post("http://catalog:8080/catalog/ping", json = externalweatherapi)
            r = requests.post("http://catalog:8080/catalog/ping", json = telegrambot)
            time.sleep(10)

class RESTSimulator():
    exposed=True

    def GET(self, *uri, **params):
        print("Called GET: " + str(uri))
        cherrypy.response.headers['Content-Type'] = 'application/json'
        restCallLogGet.append({"uri": str(uri)})
        return json.dumps(restMapper[uri[0]], indent=4)

    def POST(self, *uri):
        print("Called POST: " + str(uri))
        body = json.loads(cherrypy.request.body.read())
        cherrypy.response.headers['Content-Type'] = 'application/json'
        restCallLogPost.append({"uri": uri[0], "body": body})
        return json.dumps({"error":{"status": 200, "message": "Ok"}}, indent=4)

def createGroupId(name):
    r = requests.get("http://catalog:8080/catalog/createGroupId?groupId="+name)
    r = requests.get("http://catalog:8080/catalog/updateGroupId?groupId="+name+"&latitude=10.0&longitude=22.1")

def deleteGroupId(name):
    r = requests.get("http://catalog:8080/catalog/deleteGroupId?groupId="+name)

def waitForPost(method, timeout = 20):
    startTime = time.time()
    popped = None
    while True:
        if len(restCallLogPost) > 0:
            popped = restCallLogPost.pop()
            print(popped)
            if popped and "uri" in popped and method == popped["uri"]:
                break
        if time.time() - startTime > timeout:
            break
        time.sleep(1)

    if popped:
        print(popped["body"])
    else:
        assert False, "Unable to receive " + method

def addRestMap(uri, returnedJson):
    restMapper[uri] = returnedJson

## WITH EXTERNAL DEVICE
def ext_test_three_consecutive_value_alert_bad_external_weather():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": False,
        "co": 900.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 45}], "sensor_position": "external"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 44}], "sensor_position": "external"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 33.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 44}], "sensor_position": "external"})
    time.sleep(3)

    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def ext_test_three_consecutive_value_alert_good_external_weather():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 65,
        "safeOpenWindow": True,
        "co": 900.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 33.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 45}], "sensor_position": "external"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 33.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 44}], "sensor_position": "external"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 44}], "sensor_position": "external"})
    time.sleep(3)

    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def ext_test_three_consecutive_value_alert_bad_external_weather_open_at():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 22,
        "safeOpenWindow": True,
        "co": 900.6,
        "no": 13.86,
        "no2": 1117.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {
    "hours": [
        {
            "timestamp": 1630746000,
            "temperature": 23.180000000000007,
            "pressure": 1016,
            "humidity": 55,
            "wind_speed": 0.93
        },
        {
            "timestamp": 1630749600,
            "temperature": 23.28000000000003,
            "pressure": 1016,
            "humidity": 53,
            "wind_speed": 0.87
        },
        {
            "timestamp": 1630753200,
            "temperature": 24.129999999999995,
            "pressure": 1016,
            "humidity": 49,
            "wind_speed": 1.07
        },
        {
            "timestamp": 1630756800,
            "temperature": 25.260000000000048,
            "pressure": 1015,
            "humidity": 44,
            "wind_speed": 1.56
        },
        {
            "timestamp": 1630760400,
            "temperature": 26.480000000000018,
            "pressure": 1014,
            "humidity": 38,
            "wind_speed": 1.66
        }]
    })
    addRestMap("forecastPollution", {"pollution_values": [
            {
                "timestamp": 1630746000,
                "co": 687.6,
                "no": 13.86,
                "no2": 17.99,
                "o3": 13.41,
                "so2": 1.03,
                "pm2_5": 13.59,
                "pm10": 17.31,
                "nh3": 15.07
            },
            {
                "timestamp": 1630749600,
                "co": 333.79,
                "no": 0.49,
                "no2": 4.67,
                "o3": 101.57,
                "so2": 0.61,
                "pm2_5": 6.36,
                "pm10": 8.28,
                "nh3": 4.94
            },
            {
                "timestamp": 1630753200,
                "co": 323.77,
                "no": 0.31,
                "no2": 3.43,
                "o3": 114.44,
                "so2": 0.95,
                "pm2_5": 7.73,
                "pm10": 9.33,
                "nh3": 4.94
            },
            {
                "timestamp": 1630756800,
                "co": 327.11,
                "no": 0.29,
                "no2": 3.3,
                "o3": 125.89,
                "so2": 1.28,
                "pm2_5": 9.07,
                "pm10": 10.59,
                "nh3": 5.07
            },
            {
                "timestamp": 1630760400,
                "co": 327.11,
                "no": 0.21,
                "no2": 2.87,
                "o3": 134.47,
                "so2": 1.43,
                "pm2_5": 9.77,
                "pm10": 11.07,
                "nh3": 4.5
            }
        ]
    })
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 33.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 45}], "sensor_position": "external"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 33.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 44}], "sensor_position": "external"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE-EXT', {"bn": "groupId-Test/RANDOM-DEVICE-EXT", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 44}], "sensor_position": "external"})
    time.sleep(3)

    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")


## NO EXTERNAL DEVICE, BASED ONLY ON EXTERNALWEATHERAPI RESULTS
def test_three_consecutive_value_alert_bad_external_weather():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 89,
        "safeOpenWindow": True,
        "co": 900.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def test_three_consecutive_value_alert_safeOpenWindow_false():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 56,
        "safeOpenWindow": False,
        "co": 687.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def test_three_consecutive_value_alert_good_external_weather():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def test_three_consecutive_value_alert_bad_external_weather_open_window_at():
    addRestMap("currentWeatherStatus", {
        "temperature": 33.91,
        "humidity": 56,
        "safeOpenWindow": True,
        "co": 687.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {
        "hours": [
            {
                "timestamp": 1630746000,
                "temperature": 23.180000000000007,
                "pressure": 1016,
                "humidity": 55,
                "wind_speed": 0.93
            },
            {
                "timestamp": 1630749600,
                "temperature": 23.28000000000003,
                "pressure": 1016,
                "humidity": 53,
                "wind_speed": 0.87
            },
            {
                "timestamp": 1630753200,
                "temperature": 24.129999999999995,
                "pressure": 1016,
                "humidity": 49,
                "wind_speed": 1.07
            },
            {
                "timestamp": 1630756800,
                "temperature": 25.260000000000048,
                "pressure": 1015,
                "humidity": 44,
                "wind_speed": 1.56
            },
            {
                "timestamp": 1630760400,
                "temperature": 26.480000000000018,
                "pressure": 1014,
                "humidity": 38,
                "wind_speed": 1.66
            }]
    })
    addRestMap("forecastPollution", {"pollution_values": [
                {
                    "timestamp": 1630746000,
                    "co": 687.6,
                    "no": 13.86,
                    "no2": 17.99,
                    "o3": 13.41,
                    "so2": 1.03,
                    "pm2_5": 13.59,
                    "pm10": 17.31,
                    "nh3": 15.07
                },
                {
                    "timestamp": 1630749600,
                    "co": 333.79,
                    "no": 0.49,
                    "no2": 4.67,
                    "o3": 101.57,
                    "so2": 0.61,
                    "pm2_5": 6.36,
                    "pm10": 8.28,
                    "nh3": 4.94
                },
                {
                    "timestamp": 1630753200,
                    "co": 323.77,
                    "no": 0.31,
                    "no2": 3.43,
                    "o3": 114.44,
                    "so2": 0.95,
                    "pm2_5": 7.73,
                    "pm10": 9.33,
                    "nh3": 4.94
                },
                {
                    "timestamp": 1630756800,
                    "co": 327.11,
                    "no": 0.29,
                    "no2": 3.3,
                    "o3": 125.89,
                    "so2": 1.28,
                    "pm2_5": 9.07,
                    "pm10": 10.59,
                    "nh3": 5.07
                },
                {
                    "timestamp": 1630760400,
                    "co": 327.11,
                    "no": 0.21,
                    "no2": 2.87,
                    "o3": 134.47,
                    "so2": 1.43,
                    "pm2_5": 9.77,
                    "pm10": 11.07,
                    "nh3": 4.5
                }
            ]
        })
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 75.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")


## PREDICT
def predict_temperature():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 22.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506600.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506600.7055953, "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1630506600.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506700.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506700.7055953, "v": 30.5}, {"n": "humidity", "u": "celsius", "t": 1630506700.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506800.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506800.7055953, "v": 31.5}, {"n": "humidity", "u": "celsius", "t": 1630506800.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506900.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506900.7055953, "v": 31.7}, {"n": "humidity", "u": "celsius", "t": 1630506900.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def predict_no_temperature():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 22.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506600.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506600.7055953, "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1630506600.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506700.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506700.7055953, "v": 28.6}, {"n": "humidity", "u": "celsius", "t": 1630506700.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506800.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506800.7055953, "v": 27.5}, {"n": "humidity", "u": "celsius", "t": 1630506800.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506900.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506900.7055953, "v": 27.2}, {"n": "humidity", "u": "celsius", "t": 1630506900.7056038, "v": 53}], "sensor_position": "internal"})

    # now /sendAlert should be called
    deleteGroupId("groupId-Test")


def predict_humidity():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 22.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 54}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 56}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506600.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506600.7055953, "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1630506600.7056038, "v": 64}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506700.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506700.7055953, "v": 26.5}, {"n": "humidity", "u": "celsius", "t": 1630506700.7056038, "v": 70}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506800.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506800.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506800.7056038, "v": 72}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506900.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506900.7055953, "v": 25.7}, {"n": "humidity", "u": "celsius", "t": 1630506900.7056038, "v": 73}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")

def predict_no_humidity():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 22.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 57}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 63}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506600.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506600.7055953, "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1630506600.7056038, "v": 67}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506700.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506700.7055953, "v": 27.5}, {"n": "humidity", "u": "celsius", "t": 1630506700.7056038, "v": 68}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506800.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506800.7055953, "v": 26.5}, {"n": "humidity", "u": "celsius", "t": 1630506800.7056038, "v": 68}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506900.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506900.7055953, "v": 26.7}, {"n": "humidity", "u": "celsius", "t": 1630506900.7056038, "v": 73}], "sensor_position": "internal"})

    deleteGroupId("groupId-Test")

def predict_co2():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 22.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 520.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 57}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 530.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 63}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506600.7055776, "v": 550.83}, {"n": "temperature", "u": "celsius", "t": 1630506600.7055953, "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1630506600.7056038, "v": 67}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506700.7055776, "v": 575.83}, {"n": "temperature", "u": "celsius", "t": 1630506700.7055953, "v": 27.5}, {"n": "humidity", "u": "celsius", "t": 1630506700.7056038, "v": 68}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506800.7055776, "v": 600.83}, {"n": "temperature", "u": "celsius", "t": 1630506800.7055953, "v": 26.5}, {"n": "humidity", "u": "celsius", "t": 1630506800.7056038, "v": 68}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506900.7055776, "v": 650.83}, {"n": "temperature", "u": "celsius", "t": 1630506900.7055953, "v": 26.7}, {"n": "humidity", "u": "celsius", "t": 1630506900.7056038, "v": 73}], "sensor_position": "internal"})

    # now /sendAlert should be called
    waitForPost("sendAlert")
    deleteGroupId("groupId-Test")


def predict_no_co2():
    addRestMap("currentWeatherStatus", {
        "temperature": 22.91,
        "humidity": 44,
        "safeOpenWindow": True,
        "co": 400.6,
        "no": 13.86,
        "no2": 17.99,
        "o3": 13.41,
        "so2": 1.03,
        "pm2_5": 13.59,
        "pm10": 17.31,
        "nh3": 15.07
    })
    addRestMap("forecastWeatherStatus", {"hours": []})
    addRestMap("forecastPollution", {"pollution_values": []})
    # create groupId
    createGroupId("groupId-Test")
    # temperature is outside
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506300.7055776, "v": 510.83}, {"n": "temperature", "u": "celsius", "t": 1630506300.7055953, "v": 22.5}, {"n": "humidity", "u": "celsius", "t": 1630506300.7056038, "v": 53}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506400.7055776, "v": 520.83}, {"n": "temperature", "u": "celsius", "t": 1630506400.7055953, "v": 23.5}, {"n": "humidity", "u": "celsius", "t": 1630506400.7056038, "v": 57}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506500.7055776, "v": 530.83}, {"n": "temperature", "u": "celsius", "t": 1630506500.7055953, "v": 25.5}, {"n": "humidity", "u": "celsius", "t": 1630506500.7056038, "v": 63}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506600.7055776, "v": 550.83}, {"n": "temperature", "u": "celsius", "t": 1630506600.7055953, "v": 28.5}, {"n": "humidity", "u": "celsius", "t": 1630506600.7056038, "v": 67}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506700.7055776, "v": 575.83}, {"n": "temperature", "u": "celsius", "t": 1630506700.7055953, "v": 27.5}, {"n": "humidity", "u": "celsius", "t": 1630506700.7056038, "v": 68}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506800.7055776, "v": 550.83}, {"n": "temperature", "u": "celsius", "t": 1630506800.7055953, "v": 26.5}, {"n": "humidity", "u": "celsius", "t": 1630506800.7056038, "v": 68}], "sensor_position": "internal"})
    c.myPublish('/iot-programming-2343/groupId-Test/RANDOM-DEVICE', {"bn": "groupId-Test/RANDOM-DEVICE", "e": [{"n": "co2", "u": "ppm", "t": 1630506900.7055776, "v": 525.83}, {"n": "temperature", "u": "celsius", "t": 1630506900.7055953, "v": 26.7}, {"n": "humidity", "u": "celsius", "t": 1630506900.7056038, "v": 73}], "sensor_position": "internal"})

    deleteGroupId("groupId-Test")

def exitTest():
    cherrypy.engine.stop()
    c.stop()
    ping.stop()

if __name__ == '__main__':
    # start REST
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            }
    }
    cherrypy.tree.mount(RESTSimulator(), '/', conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.start()

    ping = Ping()
    ping.start()

    c = MyMQTT('myid23213213213', 'test.mosquitto.org', 1883, None)
    c.start()
    time.sleep(3)

    # TEST LIST #
    #test_three_consecutive_value_alert_bad_external_weather()
    #test_three_consecutive_value_alert_safeOpenWindow_false()
    #test_three_consecutive_value_alert_good_external_weather()
    #test_three_consecutive_value_alert_bad_external_weather_open_window_at()

    #ext_test_three_consecutive_value_alert_good_external_weather()
    #ext_test_three_consecutive_value_alert_bad_external_weather()
    ext_test_three_consecutive_value_alert_bad_external_weather_open_at()

    #predict_temperature()
    #predict_no_temperature()
    #predict_humidity()
    #predict_no_humidity()
    #predict_co2()
    #predict_no_co2()

    print("###### All tests successfull! Now the service is stopping. ######")
    exitTest()
