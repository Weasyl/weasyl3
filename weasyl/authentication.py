import logging

from zope.interface import implementer
from pyramid.authentication import IAuthenticationPolicy, CallbackAuthenticationPolicy
from pyramid import httpexceptions

from libweasyl.models.api import APIToken


log = logging.getLogger(__name__)


def find_token_for_authorization(authorization):
    return None


@implementer(IAuthenticationPolicy)
class APIKeyAuthenticationPolicy(CallbackAuthenticationPolicy):
    def __init__(self, callback):
        self.callback = callback

    def unauthenticated_userid(self, request):
        api_token = request.headers.get('X-Weasyl-API-Key')
        if api_token is None:
            return None
        token_object = APIToken.query.filter_by(token=api_token).first()
        if token_object is None:
            raise httpexceptions.HTTPUnauthorized(headers={
                'WWW-Authenticate': 'Weasyl-API-Key realm="Weasyl"',
            })
        return token_object.userid

    def remember(self, request, principal, **kw):
        pass

    def forget(self, request):
        pass


@implementer(IAuthenticationPolicy)
class OAuth2AuthenticationPolicy(CallbackAuthenticationPolicy):
    def __init__(self, callback):
        self.callback = callback

    def unauthenticated_userid(self, request):
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return None
        token_object = find_token_for_authorization(authorization)
        if token_object is None:
            raise httpexceptions.HTTPUnauthorized(headers={
                'WWW-Authenticate': 'Bearer realm="Weasyl" error="invalid_token"',
            })
        return token_object.userid

    def remember(self, request, principal, **kw):
        pass

    def forget(self, request):
        pass
