#coding=utf-8
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from config import app_host, app_port
from run import app

# xheaders=True is for Running behind a load balancer: http://www.tornadoweb.org/en/stable/guide/running.html#running-behind-a-load-balancer
http_server = HTTPServer(WSGIContainer(app),xheaders=True)
http_server.listen(app_port, address=app_host)
IOLoop.instance().start()