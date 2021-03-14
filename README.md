# iot-project-2020
IoT platform for user-involved air recirculation system

## Quick test - Docker-compose
In order to test the docker-compose file and turn on the entire architecture, you can do:
```
cd services
make start
```

### If you want to rebuild everything (long process)
```
cd services
make clean-start
```

### Modules
In order to make the modules available for all services and devices implementation we need to use:
```python
import sys, os
sys.path.insert(0, os.path.abspath('..'))
```

In order to make the external API work correctly, you need to set the `OPENWETHERMAPAPIKEY` variable with the key from openweathermap.com
This mean that each Raspberry and ThinkSpeakAdaptor can be lauched only from inside its folder





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

### Push your changes to GitHub, to your branch
```
git add .
git commit -m "Added servicetest"
git push origin newbranch
```
Once you have done your work, open a pull request using the GitHub interface
