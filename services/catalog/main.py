import requests
import json
import threading
import socket
import cherrypy
from serviceManager import *

class RESTManagerService(threading.Thread):
    exposed=True
    def __init__(self, brokerList):
        threading.Thread.__init__(self)
        self.__serv = ServiceManager()
        self.__broker = self.__checkFirstAvailable(brokerList)
        self.daemon = True

        if not self.__broker:
            print ("[CATALOG][ERROR] No MQTT broker available")
        else:
            print ("[CATALOG][INFO] " + self.__broker["uri"] + " selected")


    def __checkFirstAvailable(self, brokerList):
        for server in brokerList:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((server["uri"], int(server["port"])))
                s.shutdown(2)
                return server
            except:
                continue
        return {}

    def run(self):
        while 1:
            time.sleep(10)
            self.__serv.cleanOldServices();

    def GET(self, *uri, **params):
        if uri[0] == 'getBroker':
            if not self.__broker:
                cherrypy.response.status = 503
                return json.dumps({"error":{"status": 503, "message": "No mqtt server available"}}, indent=4)
            else:
                return json.dumps(self.__broker, indent=4)

        if uri[0] == 'searchById':
            if not self.__broker:
                cherrypy.response.status = 404
                return json.dumps({"error":{"status": 404, "message": "service wit the specified serviceId not found"}}, indent=4)
            else:
                return json.dumps(self.__serv.searchById(params['serviceId']), indent=4)

        if uri[0] == 'getAll':
            return json.dumps(self.__serv.getAll(), indent=4)

    def POST(self, *uri):
        body = json.loads(cherrypy.request.body.read())
        return json.dumps(self.__serv.addService(body), indent=4)

if __name__=="__main__":
    settings = json.load(open("settings.json"))
    conf={
            '/':{
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
    }
    serviceCatalog = RESTManagerService(settings["brokerList"])
    serviceCatalog.start()
    cherrypy.tree.mount(serviceCatalog,'/catalog/',conf)
    cherrypy.engine.start()

    cherrypy.engine.block()
