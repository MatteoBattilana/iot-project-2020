import cherrypy
import os
import json

class SiteExample():
    exposed=True
    list = []

    def GET(self):
        return open("html/index.html")

if __name__=="__main__":
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
    cherrypy.tree.mount(SiteExample(),'/',conf)
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.engine.start()
    cherrypy.engine.block()
