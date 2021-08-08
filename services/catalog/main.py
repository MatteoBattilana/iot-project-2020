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

# Rest service that exposes POST and GET methods to handle the ping, getBroker,
# searchById, getAll requests.
# It is implemented using a thread
class RESTManagerService(threading.Thread):
    exposed=True

    def __init__(self, brokerList, retantionTimeout):
        threading.Thread.__init__(self)
        # configuuring the service manager, that is usedo to manage the service list available in the 
        # infrastructure
        self._serv = ServiceManager(retantionTimeout)
        # Set as broker the first mqtt broker url that works from the list
        self._broker = self._getMQTTBrokerAvailable(brokerList)  #check first MQTT server available
        # The retation timeout is used to remove services from the servicemanager that did not ping it
        # within the last retantionTimeout seconds
        self._retantionTimeout = retantionTimeout
        self.daemon = True

        if not self._broker:
            logging.error("No MQTT broker available")
        else:
            logging.debug(self._broker["uri"] + " MQTT broker selected")

    # Method that given the list from the settings file, it tries all the broker and returns
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

    # Thread used to check which services did not perform a ping in time and remove them
    # from the list in the service manager
    def run(self):
        while 1:
            time.sleep(10)
            self._serv.cleanOldServices();

    # Method used to manage the GET REST request from the services
    def GET(self, *uri, **params):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if len(uri) == 0:
            # Base endpoint, accessible at /catalog/
            return json.dumps({"message": "Catalog API endpoint"}, indent=4)
        elif uri[0] == 'getBroker':
            # REST endpoint, accessible at /catalog/getBroker
            # Used to return as REST the selected MQTT broker 
            if not self._broker:
                cherrypy.response.status = 503
                return json.dumps({"error":{"status": 503, "message": "No MQTT server available"}}, indent=4)
            else:
                return json.dumps(self._broker, indent=4)
        elif uri[0] == 'searchById':
            # REST endpoint, accessible at /catalog/searchById
            # Used to get the service information from its serviceId
            if self._serv.searchById(params['serviceId']) != {}:
                return json.dumps(self._serv.searchById(params['serviceId']), indent=4)
            else:
                cherrypy.response.status = 404
                return json.dumps({"error":{"status": 404, "message": f" Service {params['serviceId']} do not exist"}}, indent=4)
        elif uri[0] == 'searchByGroupId':
            # REST endpoint, accessible at /catalog/searchByGroupId
            # Used to return the list of all DEVICE that are within a groupId
            return json.dumps(self._serv.searchByGroupId(params['groupId']), indent=4)
        elif uri[0] == 'searchByServiceType':
            # REST endpoint, accessible at /catalog/searchByServiceType
            # Used to return the list of the service that are of the specificed type: DEVICE or SERVICE
            return json.dumps(self._serv.searchByServiceType(params['serviceType']), indent=4)
        elif uri[0] == 'searchByServiceSubType':
            # REST endpoint, accessible at /catalog/searchByServiceSubType
            # Used to return the list of all services that have the desired sub type
            return json.dumps(self._serv.searchByServiceSubType(params['serviceSubType']), indent=4)
        elif uri[0] == 'getAllGroupId':
            # REST endpoint, accessible at /catalog/getAllGroupId
            # Used to return all the group ids in the infrastructure, 
            return json.dumps(self._serv.searchAllGroupId(), indent=4)
        elif uri[0] == 'getAll':
            # REST endpoint, accessible at /catalog/getAll
            # Used to return the list of all DEVICE and SERVICE
            return json.dumps(self._serv.getAll(), indent=4)
        elif uri[0] == 'getSystemStatus':
            # REST endpoint, accessible at /catalog/getSystemStatus
            # Used to return the status of the server, like the memory and CPU load
            return json.dumps({
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent
                }, indent=4)
        else:
            cherrypy.response.status = 404
            return json.dumps({"error":{"status": 404, "message": "Invalid request"}}, indent=4)


    # Used to handle the REST POST request, like th ping 
    def POST(self, *uri):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        body = json.loads(cherrypy.request.body.read())
        if len(uri) == 1:
            logging.info("Requested POST with uri " + str(uri))
            if uri[0] == 'ping':
                # Used to update the ping record in the list, like updating the last update paramenter
                ret = self._serv.addService(body)
                if not ret:
                    cherrypy.response.status = 404
                    ret = {"error":{"status": 404, "message": "Missing serviceId"}}
            else:
                cherrypy.response.status = 404
                ret = {"error":{"status": 404, "message": "Unknown method"}}
        else:
            cherrypy.response.status = 404
            ret = {"error":{"status": 404, "message": "Missing uri"}}


        return json.dumps(ret, indent=4)

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
    serviceCatalog = RESTManagerService(settings.getField("brokerList"), int(settings.getField("retantionTimeout")))
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
    #used to remove from log the incoming requests
    app.log.access_log.addFilter( IgnoreRequests() )
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.start()
    cherrypy.engine.block()
