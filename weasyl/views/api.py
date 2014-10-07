import json
import logging

import colander as c
import deform.widget as w
from oauthlib.oauth2 import FatalClientError, OAuth2Error
from pyramid_deform import CSRFSchema
from pyramid.security import remember
from pyramid.view import view_config
from pyramid import httpexceptions

from libweasyl.exceptions import LoginFailed
from libweasyl.models.api import OAuthConsumer
from libweasyl.oauth import get_consumers_for_user, revoke_consumers_for_user, server
import libweasyl
import weasyl
from .forms import FormView, JSON, User
from ..login import try_login
from ..resources import APIv2Resource, OAuth2Resource


log = logging.getLogger(__name__)


@view_config(name='whoami', context=APIv2Resource, renderer='json', api='true')
def whoami(request):
    if request.current_user:
        return {
            'login': request.current_user.login_name,
            'userid': request.current_user.userid,
        }
    else:
        return {
            'login': None,
            'userid': 0,
        }


package_info = {
    'weasyl': weasyl,
    'libweasyl': libweasyl,
}


@view_config(name='version', context=APIv2Resource, renderer='json', api='true')
@view_config(name='version.json', context=APIv2Resource, renderer='json', api='true')
def json_version(request):
    ret = {}
    for name, package in package_info.items():
        ret[name] = {
            'version': package.__version__,
            'short_hash': package.__sha__.lstrip('g'),
        }
    return ret


@view_config(name='version.txt', context=APIv2Resource, renderer='string', api='true')
def text_version(request):
    ret = []
    for name, info in json_version(request).items():
        if 'short_hash' in info:
            ret.append('%s: %s (%s)' % (name, info['version'], info['short_hash']))
        else:
            ret.append('%s: %s' % (name, info['version']))
    return '\n'.join(sorted(ret))


class AuthorizeForm(CSRFSchema):
    user = c.SchemaNode(User(), missing=None)
    password = c.SchemaNode(c.String(), missing='')
    not_me = c.SchemaNode(c.Boolean())
    remember_me = c.SchemaNode(c.Boolean())
    credentials = c.SchemaNode(JSON())

    def validator(self, form, values):
        request = self.bindings['request']
        if values['user'] is None:
            if values['not_me']:
                raise c.Invalid(form, 'A login is required if "not me" is selected')
            elif not request.current_user:
                raise c.Invalid(form, 'A login is required')
        else:
            try:
                try_login(user=values['user'], password=values['password'])
            except LoginFailed as e:
                raise c.Invalid(form, e.args[0]) from e


@view_config(name='authorize', context=OAuth2Resource, renderer='oauth2/authorize.jinja2', api='true')
class OAuth2AuthorizeView(FormView):
    schema = AuthorizeForm()
    buttons = 'authorize',

    def extra_fields(self):
        request = self.request
        try:
            scopes, credentials = server.validate_authorization_request(
                request.path, request.method, request.GET, request.headers)
        except FatalClientError:
            raise httpexceptions.HTTPUnprocessableEntity()
        except OAuth2Error as e:
            raise httpexceptions.HTTPFound(e.in_uri(e.redirect_uri))
        client = OAuthConsumer.query.get(credentials['client_id'])
        del credentials['request']
        credentials['scopes'] = scopes
        return {
            'credentials': credentials,
            'client': client,
        }

    def authorize_success(self, values):
        request = self.request
        credentials = values['credentials']
        scopes = credentials.pop('scopes')
        credentials['userid'] = (values['user'] or request.current_user).userid
        headers, body, status = server.create_authorization_response(
            request.path, request.method, request.GET, request.headers, scopes, credentials)
        if status // 100 not in {4, 5} and not request.current_user and values['remember_me']:
            headers.update(remember(request, values['user'].userid))
        log.debug('authorization success %r %r %r', headers, body, status)
        return httpexceptions.status_map[status](
            headers=headers, body=body, location=headers.pop('Location', None))


@view_config(name='token', context=OAuth2Resource, api='true', request_method='POST')
def oauth2_token(request):
    headers, body, status = server.create_token_response(
        request.path, request.method, request.POST, request.headers)
    log.debug('token success %r %r %r', headers, body, status)
    return httpexceptions.status_map[status](
        headers=headers, body=body, location=headers.pop('Location', None))
