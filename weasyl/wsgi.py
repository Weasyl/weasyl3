import datetime

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON

from .models.meta import configure as configure_db
from .resources import RootResource
from .sessions import WeasylSession
from .views.legacy import configure_urls
from .views.login import login_forms
from . import authorization, cache, predicates


def datetime_adapter(obj, request):
    return obj.isoformat()


def path_for(request, obj, *a, **kw):
    return obj.canonical_path(request, *a, **kw)


def format_datetime(request, dt):
    return dt.strftime('%d %B %Y at %H:%M:%S')


def make_app(global_config, **settings):
    settings['deform_jinja2.template_search_path'] = 'weasyl:widgets'
    settings['jinja2.filters'] = """
        static_path = pyramid_jinja2.filters:static_path_filter
        markdown = weasyl.text.markdown_filter
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
    config.add_view_predicate('api', predicates.APIPredicate)
    config.add_request_method(path_for)
    config.add_request_method(format_datetime)
    config.add_request_method(login_forms, reify=True)

    configure_urls(config)

    json_renderer = JSON()
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    config.add_renderer('json', json_renderer)

    config.set_authentication_policy(
        SessionAuthenticationPolicy(prefix='', callback=authorization.groupfinder))
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.scan('weasyl.views')
    config.scan('weasyl.models')

    cache.region.configure_from_config(settings, 'cache.')

    return config.make_wsgi_app()
