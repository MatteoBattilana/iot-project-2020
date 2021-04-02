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
  - Start the architecture (it will take a while): `docker-compose up`

Once the log messages are showing, the infrastructure is running and the web interface of node-red will be visible at: [http://localhost/ui](http://localhost/ui)


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
* ThinkSpeak channel with Temperature and Humidity from North Italy: [Stazione Meteo Carema - Airale](https://thingspeak.com/channels/297675)
* ThinkSpeak University Project: [CO2-measurement and demand-oriented ventilation](https://www.umwelt-campus.de/en/forschung/projekte/iot-werkstatt/translate-to-englisch-ideen-zur-corona-krise)
* Simulation Tool for CO2 distribution behavior: [Educational tool for CO2 concentration simulations](https://github.com/bph-tuwien/bph_co2)
* One example of informations about IAQ (there are several ones): [Indoor Air Quality](http://www.iaquk.org.uk/ESW/Files/IAQ_Rating_Index.pdf) 

