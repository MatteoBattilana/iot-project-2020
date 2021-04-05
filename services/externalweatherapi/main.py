# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *
from commons.netutils import *
from commons.settingsmanager import *
import cherrypy
import os
import json
import logging
from commons.logger import *


class ExternalWeatherApi():
    exposed=True

    def __init__(self, settings, serviceList, openweatherapikey):
        self._settings = settings
        self._ping = Ping(
            int(self._settings.getField('pingTime')),
            serviceList,
            self._settings.getField('catalogAddress'),
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getFieldOrDefault('serviceId', ''),
            "EXTERNALWEATHERAPI",
            groupId = None,
            notifier = self)
        logging.debug("Started")
        self._ping.start()
        self._openweatherapikey = openweatherapikey
        self._safeWindSpeed = float(settings.getField('windSpeedSafe'))


    # Catalog new id callback
    def onNewCatalogId(self, newId):
        self._settings.updateField('serviceId', newId)

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
                    return json.dumps({"error":{"status": 503, "message": "Unable to contact external weather API: missing parameters"}}, indent=4)
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
            logging.error("Unable to get temperature from openweatermap: " + json.dumps(r.json()))

        # Refer to https://openweathermap.org/weather-conditions
        if "weather" in r1.json() and (int(r1.json()["weather"][0]["id"]) < 800 or float(r1.json()["wind"]["speed"]) > safeWindSpeed) :
            retInformation["safeOpenWindow"] = False
        else:
            retInformation["safeOpenWindow"] = True


    else:
        logging.error("Unable to contact openweatermap")

    r2 = requests.get("http://api.openweathermap.org/data/2.5/air_pollution?lat=" + lat + "&lon=" + lon + "&units=metric&appid=" + openweatherapikey)
    if r2.status_code == 200:
        if "list" in r2.json() and "components" in r2.json()["list"][0]:
            retInformation = {**retInformation, **r2.json()["list"][0]["components"]}
        else:
            logging.error("Unable to get temperature from openweatermap: " + json.dumps(r.json()))
    else:
        logging.error("Unable to contact openweatermap")

    return retInformation

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))
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
        logging.debug("openweathermap.com api key set to: " + openweatermapkey)
    except:
        logging.error("OPENWETHERMAPAPIKEY variabile not set")
        openweatermapkey = ""

    restManager = ExternalWeatherApi(
        settings,
        availableServices,
        openweatermapkey
    )

    # Remove reduntant date cherrypy log
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]
    cherrypy.log.error_log.setLevel(Logger.getLoggerLevel(settings.getField('logVerbosity')))

    app = cherrypy.tree.mount(restManager ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', restManager.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
