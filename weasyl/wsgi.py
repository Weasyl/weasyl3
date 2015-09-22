import datetime
import json

import arrow
import pkg_resources
from pyramid_authstack import AuthenticationStackPolicy
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.security import authenticated_userid
from pyramid import httpexceptions, url
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from libweasyl.configuration import configure_libweasyl
from libweasyl.models.users import Login
from .media import format_media_link
from .resources import RootResource
from .sessions import WeasylSession
from .views.legacy import configure_urls
from .views.login import login_forms
from . import authentication, authorization, hacks, predicates, staff


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def datetime_adapter(obj, request):
    return obj.isoformat()


def path_for(request, obj, *a, **kw):
    return obj.canonical_path(request, *a, **kw)


def is_api_request(request):
    # this used to use request.traversed, but request.traversed isn't
    # always available. specifically, in the case of an HTTPException
    # raised fairly early in the request's life, a new request is
    # spawned which won't do any traversal. request.environ is pretty
    # much the only thing guaranteed to exist, so examine that.
    return bool(request.environ['PATH_INFO'].startswith('/api/'))


def is_debug_on(request):
    return bool(request.registry.settings.get('weasyl.debug') == 'true')


def format_datetime(request, dt):
    return dt.strftime('%d %B %Y at %H:%M:%S')


def current_user(request):
    userid = authenticated_userid(request)
    if userid is None:
        return None
    return Login.query.get(userid)


def configure_db(config, settings):
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)
    config.add_request_method(db, reify=True)


def db(request):
    return DBSession()


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


def load_assets():
    assets = pkg_resources.resource_string('weasyl', 'assets.json')
    return json.loads(assets.decode())


def make_asset_path_finder():
    assets = load_assets()
    def asset_path(request, asset):
        nonlocal assets
        if request.is_debug_on:
            assets = load_assets()
        return url.static_path('weasyl:' + assets[asset], request)
    return asset_path


def make_app(global_config, **settings):
    hacks.install()

    settings['deform_jinja2.template_search_path'] = 'weasyl:widgets'
    settings['jinja2.filters'] = """
        asset_path = weasyl.filters.asset_path_filter
        json = weasyl.filters.json_filter
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
        staff_config_path=settings['weasyl.staff_config'],
        media_link_formatter_callback=format_media_link,
    )
    staff.init_groups()

    config.include('pyramid_tm')
    config.include('pyramid_jinja2')
    config.include('pyramid_deform')
    config.include('deform_jinja2')
    config.add_static_view(name='static', path='weasyl:static')
    config.add_jinja2_search_path('weasyl:templates')
    config.add_view_predicate('api', predicates.APIPredicate)
    config.add_request_method(path_for)
    config.add_request_method(format_datetime)
    config.add_request_method(make_asset_path_finder())
    config.add_request_method(current_user, reify=True)
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

    auth_stack = AuthenticationStackPolicy(callback=authorization.groupfinder)
    auth_stack.add_policy(
        'api_key', authentication.APIKeyAuthenticationPolicy(callback=authorization.groupfinder))
    auth_stack.add_policy(
        'session', SessionAuthenticationPolicy(prefix='', callback=authorization.groupfinder))

    config.set_authentication_policy(auth_stack)
    config.set_authorization_policy(authorization.DelegatedAuthorizationPolicy())

    config.scan('weasyl.views', ignore='weasyl.views.test')

    return config.make_wsgi_app()
