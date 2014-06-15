import bottle

from BioTK.ui import root

if __name__ == '__main__':
    bottle.run(root, server="cherrypy", host="0.0.0.0")
