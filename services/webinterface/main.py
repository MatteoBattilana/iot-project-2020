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

    def __init__(self, pingTime, serviceList, serviceName, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceName, "SERVICE", groupId = None, notifier = None)
        logging.debug("Started")
        self._ping.start()

    def GET(self):
        return open("html/index.html")

    def stop(self):
        self._ping.stop()

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getField('logFile'))
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
        int(settings.getField('pingTime')),
        availableServices,
        settings.getField('serviceName'),
        settings.getField('catalogAddress')
    )

    # Remove reduntant date cherrypy log
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]

    app = cherrypy.tree.mount(website ,'/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.subscribe('stop', website.stop)
    cherrypy.engine.start()
    cherrypy.engine.block()
