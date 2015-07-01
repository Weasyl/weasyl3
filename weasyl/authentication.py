"""
Authentication!

The contents of this module are for authenticating that an incoming request was
issued by a particular user. Users can't actually directly specify the supposed
issuer of a request. Instead, authentication is done indirectly by using opaque
tokens which are assigned to exactly one user.
"""

import logging

from zope.interface import implementer
from pyramid.authentication import IAuthenticationPolicy, CallbackAuthenticationPolicy
from pyramid import httpexceptions

from libweasyl.models.api import APIToken


log = logging.getLogger(__name__)


def find_token_for_authorization(authorization):
    """
    Given an authorization, look up the associated OAuth2 bearer token.

    :param authorization: The value of the :http:header:`Authorization` HTTP
        request header.
    """
    return None


@implementer(IAuthenticationPolicy)
class APIKeyAuthenticationPolicy(CallbackAuthenticationPolicy):
    """
    An authentication policy for Weasyl API keys.

    This works by examining the :http:header:`X-Weasyl-API-Key` request header
    and determining which user owns the API key.
    """

    def __init__(self, callback):
        """
        Set the principal locator callback for this authentication policy.

        :param callback: A callback passed the userid and request, expected to
            return :py:data:`None` if the userid doesn't exist or a sequence of
            principals if the user does exist.
        """
        self.callback = callback

    def unauthenticated_userid(self, request):
        """
        Find the owner of the :http:header:`X-Weasyl-API-Key`.

        If there was no :http:header:`X-Weasyl-API-Key` header set, this will
        return :py:data:`None`. If the API key provided was invalid (i.e.
        doesn't map to a user), an
        :py:class:`~pyramid.httpexceptions.HTTPUnauthorized` exception will be
        raised. Otherwise, the API key's owner's userid is returned.

        :param request: The current pyramid
            :py:class:`~pyramid.request.Request`.
        """
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
        """
        API keys can't be remembered.

        So, this returns no headers.
        """
        return []

    def forget(self, request):
        """
        API keys can't be forgotten.

        This *could* deauthorize the API key, but there probably isn't any
        utility in giving API keys a way to deauthorize themselves. Anyway,
        returns no headers.
        """
        return []


@implementer(IAuthenticationPolicy)
class OAuth2AuthenticationPolicy(CallbackAuthenticationPolicy):
    """
    An authentication policy for OAuth2 consumers.

    This works by examining the :http:header:`Authorization` request header and
    passing that through to the OAuth2 server provided by oauthlib_. Since
    no other parts of the site will use the :http:header:`Authorization` header
    (i.e. no HTTP basic authentication), this is safe.

    .. _oauthlib: http://oauthlib.readthedocs.org/en/latest/
    """

    def __init__(self, callback):
        """
        Set the principal locator callback for this authentication policy.

        :param callback: A callback passed the userid and request, expected to
            return :py:data:`None` if the userid doesn't exist or a sequence of
            principals if the user does exist.
        """
        self.callback = callback

    def unauthenticated_userid(self, request):
        """
        Find the owner of the OAuth2 bearer token.

        If there was no :http:header:`Authorization` header set, this will
        return :py:data:`None`. If the bearer token provided was invalid
        (because e.g. the bearer token was invalid), an
        :py:class:`~pyramid.httpexceptions.HTTPUnauthorized` exception will be
        raised. Otherwise, the bearer token's owner's userid is returned.

        :param request: The current pyramid
            :py:class:`~pyramid.request.Request`.
        """
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
        """
        API keys can't be remembered.

        So, this returns no headers.
        """
        return []

    def forget(self, request):
        """
        API keys can't be forgotten.

        This *could* deauthorize the bearer token, but there probably isn't any
        utility in giving bearer tokens a way to deauthorize themselves.
        Anyway, returns no headers.
        """
        return []
