# iot-project-2020
IoT platform for user-involved air recirculation system

## Modules
In order to make the modules available for all services and devices implementation we need to use:
```python
import sys, os
sys.path.insert(0, os.path.abspath('..'))
```

This mean that each raspberry, simulateddevice and ThinkSpeakAdaptor can be lauched only from inside its folder
