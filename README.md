# iot-project-2020
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
* EXTERNAL WEATHER API:
  - get the current weather status at latitude LAT and longitude LON: [http://localhost:8070/currentWeatherStatus?lat=LAT&lon=LON](http://localhost:8070/currentWeatherStatus?lat=45.06226619601743&lon=7.661825314722597)