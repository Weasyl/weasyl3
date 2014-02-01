from pyramid.config import Configurator
from pyramid.renderers import render_to_response


def signin(request):
    return render_to_response('signin.jinja2', {})


def make_app():
    config = Configurator()
    config.include('pyramid_jinja2')
    config.add_route('signin', '/signin')
    config.add_view(signin, route_name='signin')
    config.add_static_view(name='static', path='weasyl:static')
    config.add_jinja2_search_path('weasyl:templates')
    app = config.make_wsgi_app()
    return app
