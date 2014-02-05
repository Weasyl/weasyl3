from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

from .models.meta import configure as configure_db
from .resources import RootResource
from .sessions import WeasylSession
from .views.urls import configure as configure_urls
from . import cache, staff


def make_app(global_config, **settings):
    settings['deform_jinja2.template_search_path'] = 'weasyl:widgets'
    settings['jinja2.filters'] = """
        model_url = pyramid_jinja2.filters:model_url_filter
        route_url = pyramid_jinja2.filters:route_url_filter
        static_url = pyramid_jinja2.filters:static_url_filter
    """
    settings['cache.wrap'] = [cache.ThreadCacheProxy, cache.JSONProxy]

    config = Configurator(
        settings=settings,
        session_factory=WeasylSession,
        root_factory=RootResource,
    )

    configure_db(config, settings)
    config.include('pyramid_jinja2')
    config.include('pyramid_deform')
    config.include('deform_jinja2')
    config.add_static_view(name='static', path='weasyl:static')
    config.add_jinja2_search_path('weasyl:templates')
    #configure_urls(config)

    config.set_authentication_policy(
        SessionAuthenticationPolicy(prefix='', callback=staff.groupfinder))
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.scan('weasyl.views')
    config.scan('weasyl.models')

    cache.region.configure_from_config(settings, 'cache.')

    return config.make_wsgi_app()
