import json
import os

class SettingsManager:
    def __init__(self, settingsFileName):
        self._settingsFileName = settingsFileName

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

    def getField(self, field):
        settings = open(self._settingsFileName, "r")
        jsonContent = json.load(settings)
        fielVal = jsonContent[field]
        settings.close()
        return fielVal
