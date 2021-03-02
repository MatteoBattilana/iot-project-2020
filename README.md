# iot-project-2020
IoT platform for user-involved air recirculation system

## Quick test - Docker-compose
In order to test the docker-compose file and turn on the entire architecture, you can do:
```
cd services
make rebuild-and-start
```

### Normal docker
If no docker-compose is used, the image must be built like this:
```
cd services
docker build -t sim1 -f simulateddevice/Dockerfile .
```

### Modules
In order to make the modules available for all services and devices implementation we need to use:
```python
import sys, os
sys.path.insert(0, os.path.abspath('..'))
```

This mean that each Raspberry and ThinkSpeakAdaptor can be lauched only from inside its folder
