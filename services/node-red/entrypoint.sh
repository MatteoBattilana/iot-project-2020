#!/bin/bash
DIR=`pwd`

cd /data
npm install
export MQTT_BROKER="test.mosquitto.org"

resp=$(curl -s 'http://127.0.0.1:8080/catalog/getBroker')
if [[ "$resp" == *"uri"* ]]; then
        uri=$(echo "${resp}" | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["uri"]')
        port=$(echo "${resp}" | python -c 'import json,sys;obj=json.load(sys.stdin);print obj["port"]')
        export MQTT_BROKER=$uri
        export MQTT_PORT=$port
else
        export MQTT_BROKER="test.mosquitto.org"
        export MQTT_PORT="1883"
fi

cd "$DIR"
npm start -- --userDir /data
