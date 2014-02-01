from wsgiref.simple_server import make_server
from .wsgi import make_app


app = make_app()
server = make_server('0.0.0.0', 8880, app)
server.serve_forever()
