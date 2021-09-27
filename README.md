# Description of the infrastructure
The entire infrastructure is based on a central service that is called Broker. It keeps a list of available services with their corresponding REST and MQTT endopoints in order to allows the other services to know which services are available. Within a time, that is called retationTime, each service must perform a ping operation that is nothing else than a notification to the catalog to say "I'm still alive". In this way, the record for that service will not be removed from the catalog.
This is done by saving an additional information in the json of each service called lastUpdate that contains the time in which the last ping has been performed.

Eache service is indentified by and id (SIMULATED-DEVICE-1) but it is defined also by two attributes:
- TYPE: it can assume only two values: [SERVICE, DEVICE]
- SUBTYPE: ideally it can be every type, depends on the alive services in the infrastructure, at the moment we have [EXTERNALWEATHERAPI, WEBINTERFACE, ...]
- groupId: only the services with TYPE = DEVICE have this attribute. Since the infrastructure must be scalable and maybe in the future, this will be used by more than one user, the groupId attribute define to which room the device belong. For example, if we have two users: Marco and Matteo, the sensor that are inside Marco's house will have a different groupId. At the moment this has been implemented in the code and works correctly but no simulated sensors have been implemented. This is because this is not actually requested.

Update: at the startup the sensor is not associated to any groupId, via Telegram the user must configure a new device by calling the /setGroupId API of the sensor by passing the new groupId and the pin, that works like a password. The id of the service/device is set via a json configuration file.

This is an extract from a http://localhost:8080/catalog/getAll response request:

```json
{
    "serviceName": "SIMULATED-DEVICE",
    "serviceType": "DEVICE",
    "serviceSubType": "RASPBERRY",
    "groupId": "home1",
    "devicePosition": "internal",
    "serviceServiceList": [
      {
        "serviceType": "MQTT",
        "endPoint": [
          {
            "topic": "/iot-programming-2343/",
            "type": "temperature"
          }
        ]
      },
      {
        "serviceType": "REST",
        "serviceIP": "172.20.0.4",
        "servicePort": 8080,
        "endPoint": [
          {
            "type": "web",
            "uri": "/",
            "version": 1,
            "parameter": [
              
            ]
          },
          {
            "type": "configuration",
            "uri": "/setPingTime",
            "version": 1,
            "parameter": [
              {
                "name": "pingTime",
                "unit": "integer"
              }
            ]
          },
          {
            "type": "configuration",
            "uri": "/setGroupId",
            "version": 1,
            "parameter": [
              {
                "name": "groupId",
                "unit": "string"
              }
            ]
          },
          {
            "type": "action",
            "uri": "/forceSensorSampling",
            "version": 1,
            "parameter": [
              
            ]
          }
        ]
      }
    ],
    "serviceId": "SIMULATED-DEVICE-2",
    "lastUpdate": 1627895704.1240659
  }
```

It's important to say that each service cannot directly communication each others since the ip of the service can change, but they must ask the catalog the ip/port and enpoints of a specific one.
For example, if the sensor needs to perform a query about the externa weather condition, it must request to the catolog which is the ip and port for that desired service. So,
1. http://catalog:8080/catalog/searchByServiceSubType?serviceSubType=EXTERNALWEATHERAPI
2. Check if the list is not empty
3. Take the last one and perform the desire request

At this point, one the catalog has been loaded, the new services will perform a ping to it in order to be registered in the catalog list of the active services. This is both for SERVICE and DEVICE. In order to simplify this, a class shared among all the services has been created and named `ping.py`. 

# Services description

More specifically the infrastructure is made up of 7 different services: the most important, on which all the system relies, is the Catalog; then the Device Adaptor, the External Api Adaptor, the Telegram Manager, the ThingSpeak Adaptor, NodeRed and finally the Control Strategy. 

## Catalog

It performs the dual function of Service Catalog and Device Catalog and it is the starting point for every service inside the infrastructure: in fact its purpose is to list all the services and devices endpoints and the resources they expose in order to be able to comunicate with them.
Every service must perform regularly a ping operation to inform the catalog that it is up and running: in fact the catalog checks periodically if time from the last ping operation has expired and, if so, it removes the service from the list.

## Telegram Manager
The Telegram Manager exposes RESTFUL APIs which are going to be used by other services: in particular the Control Strategy used in order to notificate the end-user.

## Nodered
The Telegram Manager exposes RESTFUL APIs which are going to be used by other services: in particular the Control Strategy used in order to notificate the end-user.

## Control strategy

It’s the infrastructure core service:  
* It receives and analyses data coming from the devices
* It does not merely check that the data for the various measured quantities are above the threshold limit, but it performs a multiple control in order to avoid spurious data problems.
* It alerts the user even if the devices measurements have not reached a critical value yet, but are going to do so: implementing a function which predicts the future measurements’ value based on the past ones, this service is able to understand if some kind of measure is going to be critical in the next future.
* Through Telegram Manager REST end-points, it sends to the user the notification in case one of the measured quantities is critical. At this point, analysing whether the user has or not an external device linked to the platform, and especially based on the actual external conditions plus the air pollution levels, it suggests to the user what is the best action to do in order to restore an healthy environment.
* If the external conditions are good and so is the air quality outside the user is told to open its window. Otherwise, in case one of these two conditions is not fulfilled, the control strategy tells the user not to open the window, but to open an internal door instead or eventually to switch on the dehumidifier; furthermore, based on the forecasted value provided by the external weather API, this service is able to inform the end-user if the external weather and the air pollution levels are going to return within normal ranges and when so that the user knows in advance when to open the window.

## ThingSpeak adaptor

ThingSpeak is used in order to store, visualize, and analyze live data streams in the cloud. It provides instant visualizations of data posted by our devices.
The Thingspeak Adaptor is our link between Thingspeak itsself and the infrastructure: it is subscribed to sensors topic in order to be able to receive their live messages and then it upload them to ThingSpeak via REST. It also performs daily, weekly and monthly statistics for all the measured quantities.

## ExternalWeatherApi

The ExternalWeatherApi service contact OpenWeather API in order to get: 
* Current weather data
* Air pollution data
* Forecasted weather data
* Forecasted air pollution values
* These informations are exposed via RESTful APIs to other services and then processed by the Control Strategy.

# Setup

## Windows 10 setup
* Download git: [Git install tutorial](https://phoenixnap.com/kb/how-to-install-git-windows)
* Download and install docker: [Docker installer](https://hub.docker.com/editions/community/docker-ce-desktop-windows/)
* Download and install WSL: [Stack Overflow guide](https://stackoverflow.com/a/65898115)
* Set the environment variable: [Env variable tutorial](https://phoenixnap.com/kb/windows-set-environment-variable). The variable names you have to set are (the key values must asked to @MatteoBattilana):
  - OPENWETHERMAPAPIKEY
  - THINGSPEAKAPIKEY
* Clone the project repository to your computer:
  - Open the git bash just installed
  - Write the following command: `git clone https://github.com/MatteoBattilana/iot-project-2020.git`
* In order to start the architecture you have to:
  - Enter the service directory: `cd iot-project-2020/services`
  - Build the architecture (it has to be done once unless you made some changes to Dockerfiles or requirements.txt files): `docker-compose build`
  - Start the architecture (it will take a while): `docker-compose up`


### Fix node-red problem
You should enter the project directory, open the git bash terminal and execute:
```
git config --global core.eol lf
git config --global core.autocrlf input
```


## GIT commands
### Update the repo to the last update without modification to the same file
```
git fetch
git pull
```


### Create a branch and enter
```
git branch newbranch
git checkout newbranch
```

### Clean/Restore a local branch (discard your local modifications inside a someone else branch)
```
git reset --hard
```

### Local save of your work in a branch (to do before switching to another branch or having done a commit)
```
git stash (push) --> save the modifications
git stash pop --> to have the modifications back
```

### Push your changes to GitHub, to your branch
```
git add .
git commit -m "Added servicetest"
git push origin newbranch
```
Once you have done your work, open a pull request using the GitHub interface

### Material links which can be useful
* ThingSpeak channel with CO2 data: [BME Air Quality](https://thingspeak.com/channels/1207176)
* ThingSpeak channel with Temperature and Humidity from North Italy: [Stazione Meteo Carema - Airale](https://thingspeak.com/channels/297675)
* ThingSpeak University Project: [CO2-measurement and demand-oriented ventilation](https://www.umwelt-campus.de/en/forschung/projekte/iot-werkstatt/translate-to-englisch-ideen-zur-corona-krise)
* Simulation Tool for CO2 distribution behavior: [Educational tool for CO2 concentration simulations](https://github.com/bph-tuwien/bph_co2)
* One example of informations about IAQ (there are several ones): [Indoor Air Quality](http://www.iaquk.org.uk/ESW/Files/IAQ_Rating_Index.pdf) 

### PROJECT REST ENDPOINTS
* CATALOG:
 Catalog services research:
  - search by Id: [http://localhost:8080/catalog/searchById?serviceId=ID](http://localhost:8080/catalog/searchById?serviceId=SIMULATED-DEVICE-1)
  - search by GroupId: [http://localhost:8080/catalog/searchByGroupId?groupId=GROUPID](http://localhost:8080/catalog/searchByGroupId?groupId=home1)
  - search by ServiceType: [http://localhost:8080/catalog/searchByServiceType?serviceType=SERVICETYPE](http://localhost:8080/catalog/searchByServiceType?serviceType=SERVICE)
  - search by ServiceSubType: [http://localhost:8080/catalog/searchByServiceSubType?serviceSubType=SERVICESUBTYPE](http://localhost:8080/catalog/searchByServiceSubType?serviceSubType=EXTERNALWEATHERAPI)
  - get all GroupId: [http://localhost:8080/catalog/getAllGroupId](http://localhost:8080/catalog/getAllGroupId)
  - get all services: [http://localhost:8080/catalog/getAll](http://localhost:8080/catalog/getAll)
  - get system status: [http://localhost:8080/catalog/getSystemStatus](http://localhost:8080/catalog/getSystemStatus)
  - get the broker in use: [http://localhost:8080/catalog/getBroker](http://localhost:8080/catalog/getBroker)
* NODE-RED:
  - Web Interface address: [http://localhost/ui](http://localhost/ui)
  - Node-red framework access: [http://localhost](http://localhost)
* THINGSPEAK ADAPTOR:
 Reading Data from ThingSpeak:
  - get last N MEASURETYPE data from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getResultsData?results=N](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/temperature/getResultsData?results=1)
  - get last D days of measure type MEASURETYPE data from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getDaysData?days=D](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/humidity/getDaysData?days=1)
  - get last M minutes of measure type MEASURETYPE data from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getMinutesData?minutes=M](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/temperature/getMinutesData?minutes=5)
  - get measure type MEASURETYPE data from START to END date from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getStartEndData?start=START&end=END](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/temperature/getStartEndData?start=2021-03-30%2010:10:00&end=2021-04-03%2015:40:00)
  - get measure type MEASURETYPE data sum every SUM minutes (daily) from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getSum?sum=SUM](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/humidity/getSum?sum=daily)
  - get measure type MEASURETYPE data average every AVG minutes (daily) from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getAvg?average=AVG](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/co2/getAvg?average=daily)
  - get measure type MEASURETYPE data median every MEDIAN minutes (daily) from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/measureType/MEASURETYPE/getMedian    ?median=MEDIAN](http://localhost:8090/channel/SIMULATED-DEVICE-1/measureType/temperature/getMedian?median=60)
  - get last N data from all fields of channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getResultsData?results=N](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getResultsData?results=10)
  - get last D days of data from all fields of channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getDaysData?days=D](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getDaysData?days=7)
  - get last M minutes of data from all fields of channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getMinutesData?minutes=M](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getMinutesData?minutes=60)
  - get all fields data from START to END date in channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getStartEndData?start=START&snd=END](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getStartEndData?start=2021-02-31&end=2021-04-03)
  - get all fields data sum every SUM minutes (daily) from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getSum?sum=SUM](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getSum?sum=60)
  - get all fields data average every AVG minutes (daily) from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getAvg?average=AVG](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getAvg?average=720)
  - get all fields data median every MEDIAN minutes (daily) from channel CHANNELNAME: [http://localhost:8090/channel/CHANNELNAME/feeds/getMedian?median=MEDIAN](http://localhost:8090/channel/SIMULATED-DEVICE-1/feeds/getMedian?median=720)
  - get last MINUTES minutes GROUPID external feeds: [http://localhost:8090/group/GROUPID/getExternalFeeds?minutes=MINUTES](http://localhost:8090/group/home1/getExternalFeeds?minutes=60)
  - get last MINUTES minutes GROUPID internal feeds: [http://localhost:8090/group/GROUPID/getInternalFeeds?minutes=MINUTES](http://localhost:8090/group/home1/getInternalFeeds?minutes=60)
  - get DAILY statistics of TYPE MEASURETYPE from GROUPID group: [http://localhost:8090/group/GROUPID/getStats?measureType=MEASURETYPE&lapse=DAILY&type=TYPE](http://localhost:8090/group/home1/getStats?measureType=temperature&lapse=daily&type=external)
  - get WEEKLY statistics of TYPE MEASURETYPE from GROUPID group: [http://localhost:8090/group/GROUPID/getStats?measureType=MEASURETYPE&lapse=WEEKLY&type=TYPE](http://localhost:8090/group/home1/getStats?measureType=temperature&lapse=weekly&type=external)
  - get MONTHLY statistics of TYPE MEASURETYPE from GROUPID group: [http://localhost:8090/group/GROUPID/getStats?measureType=MEASURETYPE&lapse=MONTHLY&type=TYPE](http://localhost:8090/group/home1/getStats?measureType=temperature&lapse=monthly&type=external)
  - get all DAILY TYPE statistics from GROUPID group: [http://localhost:8090/group/GROUPID/getAllStats?lapse=DAILY&type=TYPE](http://localhost:8090/group/home1/getAllStats?lapse=daily&type=external)
  - get all WEEKLY TYPE statistics from GROUPID group: [http://localhost:8090/group/GROUPID/getAllStats?lapse=WEEKLY&type=TYPE](http://localhost:8090/group/home1/getAllStats?lapse=weekly&type=external)
  - get all MONTHLY TYPE statistics from GROUPID group: [http://localhost:8090/group/GROUPID/getAllStats?lapse=MONTHLY&type=TYPE](http://localhost:8090/group/home1/getAllStats?lapse=monthly&type=external)
* EXTERNAL WEATHER API:
  - get the current weather status at latitude LAT and longitude LON: [http://localhost:8070/currentWeatherStatus?lat=LAT&lon=LON](http://localhost:8070/currentWeatherStatus?lat=45.06226619601743&lon=7.661825314722597)
  - get the forecast weather status at latitude LAT and longitude LON for the next 60 minutes, 48 hours and 7 days: [http://localhost:8070/forecastWeatherStatus?lat=LAT&lon=LON](http://localhost:8070/forecastWeatherStatus?lat=45.06226619601743&lon=7.661825314722597)
  - get the forecast weather status at latitude LAT and longitude LON about the next MINUTES minutes, HOURS hours and DAYS days: [http://localhost:8070/forecastWeatherStatus?lat=LAT&lon=LON&minutes=MINUTES&hours=HOURS&days=DAYS](http://localhost:8070/forecastWeatherStatus?lat=45.06226619601743&lon=7.661825314722597&minutes=30&hours=5&days=2)
  - get the forecast pollution at latitude LAT and longitude LON: [http://localhost:8070/forecastPollution?lat=LAT&lon=LON](http://localhost:8070/forecastPollution?lat=45.06226619601743&lon=7.661825314722597)
  - get the tomorrow optimal hour to open the window in order to start the air circulation (at latitude LAT and longitude LON): [http://localhost:8070/whenToOpenTomorrow?lat=LAT&lon=LON](http://localhost:8070/whenToOpenTomorrow?lat=45.06226619601743&lon=7.661825314722597)]
