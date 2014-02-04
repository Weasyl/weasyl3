from pyramid.config import Configurator

from .session import WeasylSession
from .models.meta import configure as configure_db


def make_app(global_config, **settings):
    settings['deform_jinja2.template_search_path'] = 'weasyl:widgets'
    config = Configurator(
        settings=settings,
        session_factory=WeasylSession,
    )
    configure_db(config, settings)
    config.include('pyramid_jinja2')
    config.include('pyramid_deform')
    config.include('deform_jinja2')
    config.add_route('signin', '/signin')
    config.add_static_view(name='static', path='weasyl:static')
    config.add_jinja2_search_path('weasyl:templates')
    config.scan('weasyl.views')
    return config.make_wsgi_app()
