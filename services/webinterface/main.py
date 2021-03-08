# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
from commons.ping import *
from commons.netutils import *
import cherrypy
import os
import json


class WebSite():
    exposed=True

    def __init__(self, pingTime, serviceList, serviceName, catalogAddress):
        threading.Thread.__init__(self)
        self._ping = Ping(pingTime, serviceList, catalogAddress, serviceName, "SERVICE", homeId = None, notifier = None)
        print("[WEBSITE][INFO] Started")
        self._ping.start()

    def GET(self):
        return open("html/index.html")

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
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
    cherrypy.tree.mount(
        WebSite(
            settings['pingTime'],
            availableServices,
            settings['serviceName'],
            settings['catalogAddress']
        ),'/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.start()
    cherrypy.engine.block()
