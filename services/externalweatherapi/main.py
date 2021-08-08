# Path hack.
import sys, os
import datetime
from datetime import timedelta
import requests
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *
from commons.netutils import *
from commons.settingsmanager import *
import cherrypy
import os
import json
import logging
from commons.logger import *

def getMinPos(_dict_list, param):
    min_val = []
    min_val = list(_dict_list[0].values())
    logging.debug(f"min_initial = {min_val}")
    for k in range(0,param):
        min_val.pop(0)
    pos = 0
    for i,data in enumerate(_dict_list):
        tmp=list(data.values())
        for j in range(0,param):
            tmp.pop(0)
        if tmp < min_val:
            min_val = tmp
            pos = i
            
    logging.debug(f"min_val = {min_val}")
    logging.debug(f"the pos = {pos}")
    return pos

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

    #else:
    #                cherrypy.response.status = 503
    #                return json.dumps({"error":{"status": 503, "message": "Unable to contact external weather API: missing parameters"}}, indent=4)

    def GET(self, *uri, **params):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if self._openweatherapikey:
            if len(uri) == 0:
                return json.dumps({"message": "External weather API endpoint"}, indent=4)
            elif uri[0] == "currentWeatherStatus" and "lat" in params and "lon" in params:
                return json.dumps(_getCurrentWeatherStatus(params['lat'], params['lon'], self._safeWindSpeed, self._openweatherapikey), indent=4)
            elif uri[0] == "forecastWeatherStatus" and "lat" in params and "lon" in params and "minutes" in params and "hours" in params and "days" in params:
                return json.dumps(self._getForecastWeather(params['lat'], params['lon'], self._openweatherapikey, params['minutes'], params['hours'], params['days']), indent=4)
            elif uri[0] == "forecastWeatherStatus" and "lat" in params and "lon" in params:
                return json.dumps(self._getForecastWeather(params['lat'], params['lon'], self._openweatherapikey), indent=4)
            elif uri[0] == "forecastWeatherStatus" and "lat" in params and "lon" in params and "days" in params:
                return json.dumps(self._getForecastWeather(params['lat'], params['lon'], self._openweatherapikey, params['days']), indent=4)
            elif uri[0] == "forecastPollution" and "lat" in params and "lon" in params:
                return json.dumps(self._getForecastAirPollution(params['lat'], params['lon']), indent=4)
            elif uri[0] == "whenToOpenTomorrow" and "lat" in params and "lon" in params:
                return json.dumps(self.whenToOpen(params['lat'], params['lon'],self._settings.getField('temperature_lower_bound'), self._settings.getField('temperature_upper_bound')), indent=4)
            else:
                cherrypy.response.status = 404
                return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)
        else:
            cherrypy.response.status = 503
            return json.dumps({"error":{"status": 503, "message": "OPENWETHERMAPAPIKEY not set"}}, indent=4)


    def _getForecastWeather(self, lat, lon, openweatherapikey, minutes=60, hours=48, days=7):
        #for the next 60 minutes we can discover possible precipitations (volume in mm)
        #for the next 48 hours we can also obtain the temperatures, humidities and pressure
        #for the next 7 days we can obtain useful info to elaborate when it is going to be the best moment to open the windows
        
        retInformation = {
            "minutes":[],
            "hours":[],
            "days":[]
        }
    
        uri = "https://api.openweathermap.org/data/2.5/onecall?lat="+str(lat)+"&lon="+str(lon)+"&appid="+openweatherapikey
        r = requests.get(uri)
        logging.debug(f"my uri is {uri}")
        minutes = int(minutes)
        hours = int(hours)
        days = int(days)
        if r.status_code == 200:
            #logging.debug(r.json())
            if minutes <= 60 and hours <= 48 and days <= 7:
                for i in range(0, minutes):
                    if "minutely" in r.json():
                        retInformation["minutes"].append(
                            {
                            "timestamp":r.json()["minutely"][i]["dt"],
                            "precipitations":r.json()["minutely"][i]["precipitation"]
                        }) 
                for j in range(0, hours):
                    if "hourly" in r.json():
                        retInformation["hours"].append(
                            {
                                "timestamp":r.json()["hourly"][j]["dt"],
                                "temperature":float(r.json()["hourly"][j]["temp"])-273.15,
                                "pressure":r.json()["hourly"][j]["pressure"],
                                "humidity":r.json()["hourly"][j]["humidity"],
                                "wind_speed":r.json()["hourly"][j]["wind_speed"]
                            }
                        )
                for i in range(0, days):
                    if "daily" in r.json():
                        retInformation["days"].append(
                           {
                                "timestamp":r.json()["daily"][i]["dt"],
                                "morningTemp":float(r.json()["daily"][i]["temp"]["morn"])-273.15,
                                "dayTemp":float(r.json()["daily"][i]["temp"]["day"])-273.15,
                                "eveningTemp":float(r.json()["daily"][i]["temp"]["eve"])-273.15,
                                "nightTemp":float(r.json()["daily"][i]["temp"]["night"])-273.15,
                                "minDailyTemp":float(r.json()["daily"][i]["temp"]["min"])-273.15,
                                "maxDailyTemp":float(r.json()["daily"][i]["temp"]["max"])-273.15
                            } 
                        )
            else:
                logging.error(f"Specified parameters cannot accepted by the openweatherapi")
        else:
            logging.error(f"Unable to contact openweathermap")
        return retInformation

    def whenToOpen(self, lat, lon, temp_lb, temp_ub):
        #we know the temperature and pressure for the next 48 hours
        #then we have the measures of the next 7 days of 
        #min and max temperatures
        #and also morning, day, evening and night temperatures
        #--> i want to know tomorrow when it will be the best moment to open the windows
        #based on the forecasted value of temperature and humidity
        #and if possible also on the last week air pollution data
        tomorrow_pollution = []
        today = datetime.datetime(datetime.date.today().year,datetime.date.today().month,datetime.date.today().day)
        tomorrow_start = today + timedelta(days=1)
        tomorrow_end = tomorrow_start + timedelta(hours=23, minutes=59, seconds=59)
        tomorrow_start_timestamp = datetime.datetime.timestamp(tomorrow_start)
        tomorrow_end_timestamp = datetime.datetime.timestamp(tomorrow_end)
        
        #these two structures contain the complete information (we do not need all of them)
        _weather_data = self._getForecastWeather(lat, lon, self._openweatherapikey, minutes=0, hours=24, days=1)
        _pollution_data = self._getForecastAirPollution(lat, lon)
        
        #tomorrow_pollution and tomorrow_weather_data contain only the useful data
        for data in _pollution_data["pollution_values"]:
            if data["timestamp"] >= tomorrow_start_timestamp and data["timestamp"] <= tomorrow_end_timestamp:
                tomorrow_pollution.append(data)
        
        cnt = 0
        pollution = []
        new_values = [1000 for i in range(0,len(tomorrow_pollution[0]))]
        for i,data in enumerate(tomorrow_pollution):
            pollution.append(len(tomorrow_pollution))

        #here i create a list (pollution) in which the value corresponding to a certain 
        #index represents a "quality" measure 
        for i,data in enumerate(tomorrow_pollution):
            min_pos = getMinPos(tomorrow_pollution,1)
            pollution[min_pos] = cnt
            cnt = cnt + 1
            tomorrow_pollution[min_pos] = dict(zip(list(tomorrow_pollution[min_pos].keys()), new_values))

        tomorrow_weather_data = []
        
        #here i do the same thing but with pressure,humidity and wind data (weathers)
        weathers = [0 for i in range(0,len(_weather_data["hours"]))]
        for i,hour in enumerate(_weather_data["hours"]):
            tomorrow_weather_data.append(hour)

        #here i want to obtain a list in which the index representing a 
        #certain tomorrow hour has a corresponding value of 0 if in that
        #hour the temperature values are inside the "good" range while
        #the value is 1 if the temperature is outside that range
        logging.debug(f"{tomorrow_weather_data}")
        temperatures = [0 for i in range(0,len(tomorrow_weather_data))]
        for i,data in enumerate(tomorrow_weather_data):
            if data["temperature"] < temp_ub and data["temperature"] > temp_lb:
                temperatures[i] = 0
            else:
                temperatures[i] = 1

        cnt = 0
        new_values= [100000 for i in range(0,len(tomorrow_weather_data[0]))]
        for i,data in enumerate(tomorrow_weather_data):
            weather_pos = getMinPos(tomorrow_weather_data,2)
            weathers[weather_pos] = cnt
            cnt = cnt + 1
            tomorrow_weather_data[weather_pos] = dict(zip(list(tomorrow_weather_data[weather_pos].keys()), new_values))

        #now pollution and weathers list contain a measure of what hour of the following
        #day has the best value regarding pollution and weather conditions

        #i want to create a list in which the index is the position/hour of tomorrow
        #and the corresponding value is a number expressing the distance from the 
        #minimum values 
        #doing this for the pollution and for the weather the perfect time slot will
        #be found easily choosing the smallest sum between the vectors elements summed
        
        poll_weather = [(pollution[i] + weathers[i]) for i in range(len(weathers))]
        
        for i in range(0,len(poll_weather)):
            optimal_pos = poll_weather.index(min(poll_weather))
            if temperatures[optimal_pos] == 0:
                optimal_hour = optimal_pos
                return optimal_hour
            else:
                poll_weather[optimal_pos] = 1000
        
    def _getForecastAirPollution(self, lat, lon):
        #with this function we can obtain past and future air pollution data
        #the returned data are the pollution values of the last five days and the 
        #future 5 ones with 1-hour steps 
        retInformation = {
            "pollution_values":[]
        }
        uri = "http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat="+lat+"&lon="+lon+"&appid="+self._openweatherapikey
        try:
            r = requests.get(uri)
            if r.status_code == 200:
                if "list" in r.json() and "components" in r.json()["list"][0]:
                    for data in r.json()["list"]:
                        retInformation["pollution_values"].append(
                            {
                                "timestamp":data["dt"],
                                 **data["components"]}
                                 )
            else:
                logging.error("Unable to get temperature from openweathermap: " + json.dumps(r.json()))
        except Exception as e:
            logging.error(f"GET request went wrong ")
        
        return retInformation
        
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
            logging.error("Unable to get temperature from openweathermap: " + json.dumps(r.json()))

        # Refer to https://openweathermap.org/weather-conditions
        if "weather" in r1.json() and (int(r1.json()["weather"][0]["id"]) < 800 or float(r1.json()["wind"]["speed"]) > safeWindSpeed) :
            retInformation["safeOpenWindow"] = False
        else:
            retInformation["safeOpenWindow"] = True


    else:
        logging.error("Unable to contact openweathermap")

    r2 = requests.get("http://api.openweathermap.org/data/2.5/air_pollution?lat=" + lat + "&lon=" + lon + "&units=metric&appid=" + openweatherapikey)
    if r2.status_code == 200:
        if "list" in r2.json() and "components" in r2.json()["list"][0]:
            retInformation = {**retInformation, **r2.json()["list"][0]["components"]}
        else:
            logging.error("Unable to get temperature from openweathermap: " + json.dumps(r.json()))
    else:
        logging.error("Unable to contact openweathermap")

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
                },
                {
                    "type":"web",
                    "uri":"/forecastWeatherStatus",
                    "version": 1,
                    "parameter": [{"name": "lat", "unit":"float"}, {"name": "lon", "unit":"float"}, {"name": "minutes", "unit":"int"}, {"name": "hours", "unit":"int"}, {"name": "days", "unit":"int"}]
                },
                {
                    "type":"web",
                    "uri":"/forecastPollution",
                    "version": 1,
                    "parameter": [{"name":"lat", "unit":"float"}, {"name":"lon ", "unit":"float"}]
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
