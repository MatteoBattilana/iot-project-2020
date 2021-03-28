# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *
from commons.netutils import *
from commons.settingsmanager import *
import cherrypy
import os
import json


class ExternalWeatherApi():
    exposed=True

    def __init__(self, pingTime, serviceList, serviceId, catalogAddress, safeWindSpeed, openweatherapikey):
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceId, "SERVICE", groupId = None, notifier = None)
        print("[INFO] Started")
        self._ping.start()
        self._openweatherapikey = openweatherapikey
        self._safeWindSpeed = safeWindSpeed
        print("[INFO] openweathermap.com api key set to: " + self._openweatherapikey)

    def stop(self):
        self._ping.stop()

    def GET(self, *uri, **parameter):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if len(uri) == 0:
            return json.dumps({"message": "External weather API endpoint"}, indent=4)
        elif uri[0] == "currentWeatherStatus":
            if self._openweatherapikey:
                if "lat" in parameter and "lon" in parameter:
                    return json.dumps(_getCurrentWeatherStatus(parameter['lat'], parameter['lon'], self._safeWindSpeed, self._openweatherapikey), indent=4)
                else:
                    cherrypy.response.status = 503
                    return json.dumps({"error":{"status": 503, "message": "Unable to contact external weather API"}}, indent=4)
            else:
                cherrypy.response.status = 503
                return json.dumps({"error":{"status": 503, "message": "OPENWETHERMAPAPIKEY not set"}}, indent=4)
        else:
            cherrypy.response.status = 404
            return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)

def _getCurrentWeatherStatus(lat, lon, safeWindSpeed, openweatherapikey):
    # http://api.openweathermap.org/data/2.5/air_pollution?lat=45.672383&lon=11.5411214&units=metric&appid=9ee2ff4386066f12e552d13a4bd53e8e
    # http://api.openweathermap.org/data/2.5/weather?lat=45.672383&lon=11.5411214&appid=9ee2ff4386066f12e552d13a4bd53e8e
    retInformation = {}
    r1 = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=" + lat + "&lon=" + lon + "&units=metric&appid=" + openweatherapikey)
    if r1.status_code == 200:
        if "main" in r1.json():
            retInformation["temperature"] = r1.json()["main"]["temp"]
            retInformation["humidity"] = r1.json()["main"]["humidity"]
        else:
            print("[ERROR] Unable to get temperature from openweatermap: " + json.dumps(r.json()))

        # Refer to https://openweathermap.org/weather-conditions
        if "weather" in r1.json() and (int(r1.json()["weather"][0]["id"]) < 800 or float(r1.json()["wind"]["speed"]) > safeWindSpeed) :
            retInformation["safeOpenWindow"] = False
        else:
            retInformation["safeOpenWindow"] = True


    else:
        print("[ERROR] Unable to contact openweatermap")

    r2 = requests.get("http://api.openweathermap.org/data/2.5/air_pollution?lat=" + lat + "&lon=" + lon + "&units=metric&appid=" + openweatherapikey)
    print(json.dumps(r2.json(), indent=4))
    if r2.status_code == 200:
        print("\nASD: " + str(r2.json()["list"][0]))
        if "list" in r2.json() and "components" in r2.json()["list"][0]:
            retInformation = {**retInformation, **r2.json()["list"][0]["components"]}
        else:
            print("[ERROR] Unable to get temperature from openweatermap: " + json.dumps(r.json()))
    else:
        print("[ERROR] Unable to contact openweatermap")

    return retInformation

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    availableServices = [
        {
            "serviceType": "REST",
            "serviceIP": NetworkUtils.getIp(),
            "servicePort": 8080,
            "endPoint": [
                {
                    "type": "web",
                    "uri": "/currentWeatherStatus",
                    "version": 1,
                    "parameter": [{"name": "lat", "unit": "float"}, {"name": "lon", "unit": "float"}]
                }
                ,{
                        "type": "web",
                        "uri": "/",
                        "version": 1,
                        "parameter": []
                    }
            ]
        }
    ]
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    try:
        openweatermapkey = os.environ['OPENWETHERMAPAPIKEY']
    except:
        print("[ERROR] OPENWETHERMAPAPIKEY variabile not set")
        openweatermapkey = ""

    restManager = ExternalWeatherApi(
        int(settings.getField('pingTime')),
        availableServices,
        settings.getField('serviceName'),
        settings.getField('catalogAddress'),
        float(settings.getField('windSpeedSafe')),
        openweatermapkey
    )
    cherrypy.tree.mount(restManager ,'/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', restManager.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
