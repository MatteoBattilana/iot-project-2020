# Path hack.
import sys, os
sys.path.insert(0, os.path.abspath('..'))
import requests
import json
import threading
import socket
import psutil
import cherrypy
import datetime
from logging.handlers import QueueHandler
from serviceManager import *
from commons.settingsmanager import *
import logging
from commons.logger import *

# Test comment
# Rest service that exposes POST and GET methods to handle the ping, getBroker,
# searchById, getAll requests.
# It is implemented using a thread
class RESTManagerService(threading.Thread):
    exposed=True

    def __init__(self, brokerList, serviceManager):
        threading.Thread.__init__(self)
        self._serv = serviceManager
        self._broker = self._getMQTTBrokerAvailable(brokerList)  #check first MQTT server available
        self.daemon = True

        if not self._broker:
            logging.error("No MQTT broker available")
        else:
            logging.debug(self._broker["uri"] + " MQTT broker selected")

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
        cherrypy.response.headers['Content-Type'] = 'application/json'
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
        elif uri[0] == 'searchByGroupId':
            return json.dumps(self._serv.searchByGroupId(params['groupId']), indent=4)
        elif uri[0] == 'searchByServiceType':
            return json.dumps(self._serv.searchByServiceType(params['serviceType']), indent=4)
        elif uri[0] == 'searchByServiceSubType':
            return json.dumps(self._serv.searchByServiceSubType(params['serviceSubType']), indent=4)
        elif uri[0] == 'getWebInterfaceUrlByGroup':
            url = self._serv.getWebInterfaceByGroup(params['groupId'])
            if url:
                return json.dumps({"url": url}, indent=4)
            else:
                cherrypy.response.status = 503
                return json.dumps({"error":{"status": 503, "message": "No web interface available for " + params['groupId']}}, indent=4)
        elif uri[0] == 'getAllGroupId':
            return json.dumps(self._serv.searchAllGroupId(), indent=4)
        elif uri[0] == 'getAll':
            return json.dumps(self._serv.getAll(), indent=4)
        elif uri[0] == 'getSystemStatus':
            return json.dumps({
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent
                }, indent=4)
        else:
            cherrypy.response.status = 404
            return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)



    def POST(self, *uri):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        body = json.loads(cherrypy.request.body.read())
        if len(uri) == 1:
            logging.info("Requested POST with uri " + str(uri))
            if uri[0] == 'ping':
                ret = self._serv.addService(body)
            else:
                cherrypy.response.status = 404
                ret = {"error":{"status": 404, "message": "Unknown method"}}
        else:
            cherrypy.response.status = 404
            ret = {"error":{"status": 404, "message": "Missing uri"}}


        return json.dumps(ret, indent=4)

class UIManager():
    exposed=True
    
    def __init__(self, serviceManager):
        self._serviceManager = serviceManager

    def GET(self, *uri, **params):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        print(str(uri))
        if len(uri) == 0:
            return json.dumps({"message": "UI interface endpoint"}, indent=4)
        else:
            url = self._serviceManager.getWebInterfaceByGroup(uri[0])
            if url:
                raise cherrypy.HTTPRedirect(url)
            else:
                cherrypy.response.status = 404
                return json.dumps({"error":{"status": 503, "message": "No web interface available for " + uri[0]}}, indent=4)

if __name__=="__main__":
    settings = SettingsManager("settings.json")
    Logger.setup(settings.getField('logVerbosity'), settings.getFieldOrDefault('logFile', ''))
    conf={
            '/':{
                'tools.encode.text_only': False,
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath(os.getcwd()),
            }
    }
    serviceManager = ServiceManager(int(settings.getField("retantionTimeout")))
    serviceCatalog = RESTManagerService(settings.getField("brokerList"), serviceManager)
    serviceCatalog.start()

    # Remove reduntant date cherrypy log
    #new_formatter = BlankFormatter()
    #for h in cherrypy.log.error_log.handlers:
    #    h.setFormatter(new_formatter)
    cherrypy._cplogging.LogManager.time = lambda uno: ""
    handler = MyLogHandler()
    handler.setFormatter(BlankFormatter())
    cherrypy.log.error_log.handlers = [handler]
    cherrypy.log.error_log.setLevel(Logger.getLoggerLevel(settings.getField('logVerbosity')))


    app = cherrypy.tree.mount(serviceCatalog,'/catalog/',conf)
    uiapp = cherrypy.tree.mount(UIManager(serviceManager),'/ui/',conf)
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    uiapp.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.server.socket_port = 8080
    cherrypy.engine.start()
    cherrypy.engine.block()
