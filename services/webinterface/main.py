# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *
from commons.netutils import *
from commons.settingsmanager import *
import cherrypy
import os
import json
import logging
from commons.logger import *


class WebSite():
    exposed=True

    def __init__(self, settings, serviceList):
        threading.Thread.__init__(self)
        self._settings = settings
        self._ping = Ping(
            int(self._settings.getField('pingTime')), 
            serviceList, 
            self._settings.getField('catalogAddress'),
            self._settings.getField('serviceName'),
            "SERVICE",
            self._settings.getField('serviceId'),
            "WEBINTERFACE",
            groupId = None)
        logging.debug("Started")
        self._ping.start()

    def GET(self):
        return open("html/index.html")

    def stop(self):
        self._ping.stop()

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
                    "uri": "/",
                    "parameter": []
                }
            ]
        }
    ]
    conf={
            '/':{
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
            '/css':{
                'tools.staticdir.on': True,
                'tools.staticdir.dir':'html/css'
            },
            '/js':{
                'tools.staticdir.on': True,
                'tools.staticdir.dir':'html/js'
            },
    }
    website = WebSite(
        settings,
        availableServices
    )

    # Remove reduntant date cherrypy log
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]
    cherrypy.log.error_log.setLevel(Logger.getLoggerLevel(settings.getField('logVerbosity')))

    app = cherrypy.tree.mount(website ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', website.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
