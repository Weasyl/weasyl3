import datetime
import functools

import arrow
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.traversal import quote_path_segment
from pyramid import url

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


def is_api_request(request):
    return bool(request.traversed and request.traversed[0] == 'api')


def format_datetime(request, dt):
    return dt.strftime('%d %B %Y at %H:%M:%S')


@functools.lru_cache(1000)
def _join_elements(elements):
    return '/'.join([quote_path_segment(s, safe=':@&+$,~') for s in elements])

# ugly hack to make ~ not escaped in URLs
url._join_elements = _join_elements


def make_app(global_config, **settings):
    settings['deform_jinja2.template_search_path'] = 'weasyl:widgets'
    settings['jinja2.filters'] = """
        static_path = pyramid_jinja2.filters:static_path_filter
        markdown = weasyl.text.markdown_filter
        relative_date = weasyl.text.relative_date
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
    config.add_request_method(is_api_request, reify=True)
    config.add_request_method(login_forms, reify=True)

    configure_urls(config)

    json_renderer = JSON()
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    json_renderer.add_adapter(arrow.Arrow, datetime_adapter)
    config.add_renderer('json', json_renderer)

    config.set_authentication_policy(
        SessionAuthenticationPolicy(prefix='', callback=authorization.groupfinder))
    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.scan('weasyl.views')
    config.scan('weasyl.models')

    cache.region.configure_from_config(settings, 'cache.')

    return config.make_wsgi_app()
