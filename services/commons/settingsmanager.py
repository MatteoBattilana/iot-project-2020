import json
import os

# Class used to simplify the read and write to the settings file
# Settings are managed in json
class SettingsManager:
    def __init__(self, settingsFileName):
        self._settingsFileName = settingsFileName

    # update the field and update also the local file
    def updateField(self, field, value):
        settings = open(self._settingsFileName, "r+")
        jsonContent = json.load(settings)
        try:
            jsonContent[field] = value
            settings.seek(0)
            settings.write(json.dumps(jsonContent, indent=4))
            settings.truncate()
        finally:
            settings.close()

    # get the field field
    def getField(self, field):
        settings = open(self._settingsFileName, "r")
        jsonContent = json.load(settings)
        fielVal = jsonContent[field]
        settings.close()
        return fielVal

    # get the field field of set the default value if not present
    def getFieldOrDefault(self, field, defaultValue):
        settings = open(self._settingsFileName, "r")
        jsonContent = json.load(settings)
        fielVal = defaultValue
        if field in jsonContent:
            fielVal = jsonContent[field]
        settings.close()
        return fielVal
