import datetime
import functools

import arrow
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.traversal import quote_path_segment
from pyramid import httpexceptions, traversal, url
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from libweasyl.configuration import configure_libweasyl
from libweasyl import cache
from .media import format_media_link
from .resources import RootResource
from .sessions import WeasylSession
from .views.legacy import configure_urls
from .views.login import login_forms
from . import authorization, predicates


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def datetime_adapter(obj, request):
    return obj.isoformat()


def path_for(request, obj, *a, **kw):
    return obj.canonical_path(request, *a, **kw)


def is_api_request(request):
    return bool(request.traversed and request.traversed[0] == 'api')


def is_debug_on(request):
    return bool(request.registry.settings.get('weasyl.debug') == 'true')


def format_datetime(request, dt):
    return dt.strftime('%d %B %Y at %H:%M:%S')


def configure_db(config, settings):
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)
    config.add_request_method(db, reify=True)


def db(request):
    return DBSession()


@functools.lru_cache(1000)
def _join_elements(elements):
    return '/'.join([quote_path_segment(s, safe=':@&+$,~') for s in elements])

# ugly hack to make ~ not escaped in URLs
url._join_elements = _join_elements


class _Root:
    pass

_Root.__name__ = ''


def _lineage(resource):
    """
    Return a generator representing the :term:`lineage` of the
    :term:`resource` object implied by the ``resource`` argument.  The
    generator first returns ``resource`` unconditionally.  Then, if
    ``resource`` supplies a ``__parent__`` attribute, return the resource
    represented by ``resource.__parent__``.  If *that* resource has a
    ``__parent__`` attribute, return that resource's parent, and so on,
    until the resource being inspected either has no ``__parent__``
    attribute or which has a ``__parent__`` attribute of ``None``.
    For example, if the resource tree is::

      thing1 = Thing()
      thing2 = Thing()
      thing2.__parent__ = thing1

    Calling ``lineage(thing2)`` will return a generator.  When we turn
    it into a list, we will get::

      list(lineage(thing2))
      [ <Thing object at thing2>, <Thing object at thing1> ]
    """
    if resource is None:
        yield _Root
        return

    while resource is not None:
        yield resource
        # The common case is that the AttributeError exception below
        # is exceptional as long as the developer is a "good citizen"
        # who has a root object with a __parent__ of None.  Using an
        # exception here instead of a getattr with a default is an
        # important micro-optimization, because this function is
        # called in any non-trivial application over and over again to
        # generate URLs and paths.
        try:
            resource = resource.__parent__
        except AttributeError:
            resource = None

# ugly hack to make None work as a root
traversal.lineage = _lineage


class NoLeadingUnderscoresJSON(JSON):
    def __call__(self, info):
        super_render = super().__call__(info)

        def _render(value, system):
            if isinstance(value, dict):
                for key in list(value.keys()):
                    if key.startswith('_'):
                        del value[key]
            return super_render(value, system)

        return _render


def make_app(global_config, **settings):
    settings['deform_jinja2.template_search_path'] = 'weasyl:widgets'
    settings['jinja2.filters'] = """
        static_path = pyramid_jinja2.filters:static_path_filter
        markdown = weasyl.filters.markdown_filter
        relative_date = weasyl.filters.relative_date
    """

    config = Configurator(
        settings=settings,
        session_factory=WeasylSession,
        root_factory=RootResource,
    )

    configure_db(config, settings)
    configure_libweasyl(
        dbsession=DBSession,
        not_found_exception=httpexceptions.HTTPNotFound,
        base_file_path=settings['weasyl.static_root'],
        media_link_formatter_callback=format_media_link,
    )

    config.include('pyramid_tm')
    config.include('pyramid_jinja2')
    config.include('pyramid_deform')
    config.include('deform_jinja2')
    config.add_static_view(name='static', path='weasyl:static')
    config.add_jinja2_search_path('weasyl:templates')
    config.add_view_predicate('api', predicates.APIPredicate)
    config.add_request_method(path_for)
    config.add_request_method(format_datetime)
    config.add_request_method(is_api_request, reify=True)
    config.add_request_method(is_debug_on, reify=True)
    config.add_request_method(login_forms, reify=True)
    config.add_tween(
        'weasyl.sessions.session_tween_factory',
        under='pyramid_tm.tm_tween_factory')

    configure_urls(config)

    json_renderer = NoLeadingUnderscoresJSON()
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    json_renderer.add_adapter(arrow.Arrow, datetime_adapter)
    config.add_renderer('json', json_renderer)

    config.set_authentication_policy(
        SessionAuthenticationPolicy(prefix='', callback=authorization.groupfinder))
    config.set_authorization_policy(authorization.DelegatedAuthorizationPolicy())

    config.scan('weasyl.views')

    cache.region.configure_from_config(settings, 'cache.')
    for wrapper in [cache.JSONProxy, cache.ThreadCacheProxy]:
        cache.region.wrap(wrapper)

    return config.make_wsgi_app()
