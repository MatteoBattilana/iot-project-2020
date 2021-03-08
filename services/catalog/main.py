import requests
import json
import threading
import socket
import cherrypy
from serviceManager import *

# Test comment
# Rest service that exposes POST and GET methods to handle the ping, getBroker,
# searchById, getAll requests.
# It is implemented using a thread
class RESTManagerService(threading.Thread):
    exposed=True
    def __init__(self, brokerList, retantionTimeout):
        threading.Thread.__init__(self)
        self._serv = ServiceManager(retantionTimeout)
        self._broker = self._getMQTTBrokerAvailable(brokerList)  #check first MQTT server available
        self._retantionTimeout = retantionTimeout
        self.daemon = True

        if not self._broker:
            print ("[CATALOG][ERROR] No MQTT broker available")
        else:
            print ("[CATALOG][INFO] " + self._broker["uri"] + " MQTT broker selected")

    # Given the list from the settings file, it tries all the broker and returns
    # the first one that works
    def _getMQTTBrokerAvailable(self, brokerList):
        for server in brokerList:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((server["uri"], int(server["port"])))
                s.shutdown(2)
                return server
            except:
                continue
        return {}

    # Request a clean for the devices that did not perform a ping in the constraint
    # time
    def run(self):
        while 1:
            time.sleep(10)
            self._serv.cleanOldServices();

    def GET(self, *uri, **params):
        if len(uri) == 0:
            return json.dumps({"message": "Catalog API endpoint"}, indent=4)
        elif uri[0] == 'getBroker':
            if not self._broker:
                cherrypy.response.status = 503
                return json.dumps({"error":{"status": 503, "message": "No MQTT server available"}}, indent=4)
            else:
                return json.dumps(self._broker, indent=4)
        elif uri[0] == 'searchById':
            return json.dumps(self._serv.searchById(params['serviceId']), indent=4)
        elif uri[0] == 'searchByHomeId':
            return json.dumps(self._serv.searchByHomeId(params['homeId']), indent=4)
        elif uri[0] == 'getAll':
            return json.dumps(self._serv.getAll(), indent=4)
        else:
            cherrypy.response.status = 404
            return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)



    def POST(self, *uri):
        body = json.loads(cherrypy.request.body.read())
        if len(uri) == 1:
            print ("[CATALOG][INFO] Requested POST with uri " + str(uri))
            if uri[0] == 'ping':
                ret = self._serv.addService(body)
            else:
                cherrypy.response.status = 404
                ret = {"error":{"status": 404, "message": "Unknown method"}}
        else:
            cherrypy.response.status = 404
            ret = {"error":{"status": 404, "message": "Missing uri"}}


        return json.dumps(ret, indent=4)

if __name__=="__main__":
    settings = json.load(open(os.path.join(os.path.dirname(__file__), "settings.json")))
    conf={
            '/':{
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            }
    }
    serviceCatalog = RESTManagerService(settings["brokerList"], settings["retantionTimeout"])
    serviceCatalog.start()
    cherrypy.tree.mount(serviceCatalog,'/catalog/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.start()

    cherrypy.engine.block()
