import cgi
import json
import re
from urllib.parse import urlparse

from pyramid.testing import DummyRequest, DummySecurityPolicy
from pyramid import httpexceptions
import pytest

from libweasyl.cache import region
from libweasyl.test.common import Bag, make_oauth_consumer, make_password, make_user
from weasyl.views import api
from weasyl.test.common import auth_policy_request


def test_whoami():
    """
    whoami gives the login_namd and userid of the current_user.
    """
    resp = api.whoami(DummyRequest(current_user=Bag(login_name='spam', userid=9)))
    assert resp == {
        'login': 'spam',
        'userid': 9,
    }


def test_whoami_unauthorized():
    """
    If there is no current user, whoami returns an HTTP 401.
    """
    resp = api.whoami(DummyRequest(current_user=None))
    assert isinstance(resp, httpexceptions.HTTPUnauthorized)


def test_json_version():
    """
    json_version returns an object containing the version and short_hash of
    weasyl and libweasyl.
    """
    resp = api.json_version(DummyRequest())
    assert resp.keys() == {'weasyl', 'libweasyl'}
    assert resp['weasyl'].keys() == {'version', 'short_hash'}
    assert resp['libweasyl'].keys() == {'version', 'short_hash'}


_text_version_pattern = re.compile('\n'.join([
    r'libweasyl: [^ ]+ \([0-9a-f]+\)',
    r'weasyl: [^ ]+ \([0-9a-f]+\)',
]))


def test_text_version():
    """
    text_version returns the version and short hash of weasyl and libweasyl as
    a text string in a particular format.
    """
    resp = api.text_version(DummyRequest())
    assert _text_version_pattern.match(resp).group() == resp


_valid_params = {
    'response_type': 'code',
    'client_id': 'client_id',
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'state': 'some state',
}


def test_oauth2_authorize_invalid_client_id(db):
    """
    If an unknown client_id is passed in to the OAuth2AuthorizeView, an HTTP
    422 exception comes out.
    """
    make_oauth_consumer(db)
    with pytest.raises(httpexceptions.HTTPUnprocessableEntity):
        api.OAuth2AuthorizeView(DummyRequest(dict(_valid_params, client_id='bad_client_id')))()


def test_oauth2_authorize_invalid_response_type(db):
    """
    If an invalid response_type is passed in to the OAuth2AuthorizeView, an
    HTTP 302 exception comes out with a particular Location set.
    """
    make_oauth_consumer(db)
    with pytest.raises(httpexceptions.HTTPFound) as exc:
        api.OAuth2AuthorizeView(DummyRequest(dict(_valid_params, response_type='bad_code')))()
    assert exc.value.headers['Location'] == 'urn:ietf:wg:oauth:2.0:oob?error=unauthorized_client'


def test_oauth2_authorize_invalid_redirect_uri(db):
    """
    If an unknown redirect_uri is passed in to the OAuth2AuthorizeView, an HTTP
    422 exception comes out.
    """
    make_oauth_consumer(db)
    with pytest.raises(httpexceptions.HTTPUnprocessableEntity):
        api.OAuth2AuthorizeView(DummyRequest(dict(_valid_params, redirect_uri='bad:urn:ietf:wg:oauth:2.0:oob')))()


def test_oauth2_authorize_form_display(db):
    """
    The OAuth2AuthorizeView issues an appropriate response context when
    provided with a valid set of parameters.
    """
    make_oauth_consumer(db)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params))()
    assert result['_form']
    assert not result['_errors']
    assert result['client'].clientid == 'client_id'
    assert result['credentials'] == {
        'client_id': 'client_id',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'response_type': 'code',
        'scopes': ['wholesite'],
        'state': 'some state',
    }


_valid_credentials = {
    'client_id': 'client_id',
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'response_type': 'code',
    'scopes': ['wholesite'],
    'state': 'some state',
}


def assert_good_authorization(result, as_userid):
    """
    Assert that a response object is a good authorization response for a
    particular user.
    """
    assert isinstance(result, httpexceptions.HTTPFound)
    parsed = urlparse(result.headers['Location'])
    assert parsed.scheme == 'urn'
    assert parsed.path == 'ietf:wg:oauth:2.0:oob'
    query = cgi.parse_qs(parsed.query)
    assert query['state'] == ['some state']
    code = query['code'][0]
    assert code
    code_data = region.get('oauth2-grant-tokens:' + code)
    assert code_data['userid'] == as_userid


def test_oauth2_authorize_form_login(db):
    """
    If there is no current user, specifying a valid login at the OAuth2
    authorization form will create an authorization for that login.
    """
    consumer = make_oauth_consumer(db)
    make_password(db, consumer.owner)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'user': consumer.owner.login_name,
        'password': 'password',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=None))()
    assert_good_authorization(result, as_userid=consumer.owner.userid)


def test_oauth2_authorize_form_login_remember_me(db):
    """
    Specifying 'remember me' will tell the authentication policy to remember
    the user who logged in.
    """
    policy = DummySecurityPolicy()
    consumer = make_oauth_consumer(db)
    make_password(db, consumer.owner)
    result = api.OAuth2AuthorizeView(auth_policy_request(policy, params=_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'user': consumer.owner.login_name,
        'password': 'password',
        'remember_me': 'true',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=None))()
    assert isinstance(result, httpexceptions.HTTPFound)
    assert policy.remembered == consumer.owner.userid


def test_oauth2_authorize_form_login_does_not_remember_without_remember_me(db):
    """
    If the user doesn't specify 'remember me' while logging in, the user won't
    get remembered by the authentication policy.
    """
    policy = DummySecurityPolicy()
    consumer = make_oauth_consumer(db)
    make_password(db, consumer.owner)
    result = api.OAuth2AuthorizeView(auth_policy_request(policy, params=_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'user': consumer.owner.login_name,
        'password': 'password',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=None))()
    assert isinstance(result, httpexceptions.HTTPFound)
    assert not hasattr(policy, 'remembered')


def test_oauth2_authorize_form_login_does_not_remember_with_current_user(db):
    """
    If a user is already logged in, tries to log in with a different acccount,
    and specifies 'not me' and 'remember me', nothing happens; the user is not
    remembered by the authentication policy.
    """
    policy = DummySecurityPolicy()
    consumer = make_oauth_consumer(db)
    other_user = make_user(db)
    make_password(db, other_user)
    result = api.OAuth2AuthorizeView(auth_policy_request(policy, params=_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'user': other_user.login_name,
        'password': 'password',
        'not_me': 'true',
        'remember_me': 'true',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=consumer.owner))()
    assert isinstance(result, httpexceptions.HTTPFound)
    assert not hasattr(policy, 'remembered')


def test_oauth2_authorize_form_login_failure(db):
    """
    Specifying the wrong password makes the form fail validation.
    """
    consumer = make_oauth_consumer(db)
    make_password(db, consumer.owner)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'user': consumer.owner.login_name,
        'password': 'bad-password',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=None))()
    errors = result['_errors']
    assert len(errors) == 1
    assert errors[0][1] == ['Password incorrect.']


def test_oauth2_authorize_form_without_login(db):
    """
    When there is no current user, a login is required or the form will fail
    validation.
    """
    make_oauth_consumer(db)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=None))()
    errors = result['_errors']
    assert len(errors) == 1
    assert errors[0][1] == ['A login is required.']


def test_oauth2_authorize_form_without_not_me_login(db):
    """
    If there is a current user and the user selects 'not me', then a login is
    required or the form will fail validation.
    """
    consumer = make_oauth_consumer(db)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'not_me': 'true',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=consumer.owner))()
    errors = result['_errors']
    assert len(errors) == 1
    assert errors[0][1] == ['A login is required if "not me" is selected.']


def test_oauth2_authorize_form_login_as_other_user(db):
    """
    If there is a current user and the user specifies both 'not me' and a
    login, the authorization is granted for the specified login and not the
    current user.
    """
    consumer = make_oauth_consumer(db)
    other_user = make_user(db)
    make_password(db, other_user)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'not_me': 'true',
        'user': other_user.login_name,
        'password': 'password',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=consumer.owner))()
    assert_good_authorization(result, as_userid=other_user.userid)


def test_oauth2_authorize_form_login_as_other_user_without_not_me(db):
    """
    If there is a current user and the user specifies a login without
    specifying 'not me', the authorization is granted for the current user.
    """
    consumer = make_oauth_consumer(db)
    other_user = make_user(db)
    make_password(db, other_user)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'user': other_user.login_name,
        'password': 'password',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=consumer.owner))()
    assert_good_authorization(result, as_userid=consumer.owner.userid)


def test_oauth2_authorize_form_success(db):
    """
    If there's a current user, no login is required to grant an authorization
    for the current user.
    """
    consumer = make_oauth_consumer(db)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=consumer.owner))()
    assert_good_authorization(result, as_userid=consumer.owner.userid)


def setup_oauth2_code(db):
    """
    Set up an authorization grant by posting data to the OAuth2AuthorizeView
    and return the code required to get a token from the grant.
    """
    consumer = make_oauth_consumer(db)
    result = api.OAuth2AuthorizeView(DummyRequest(_valid_params, post={
        'csrf_token': '0123456789012345678901234567890123456789',
        'credentials': json.dumps(_valid_credentials),
        'authorize': 'yes',
    }, current_user=consumer.owner))()
    parsed = urlparse(result.headers['Location'])
    query = cgi.parse_qs(parsed.query)
    return query['code'][0]


_valid_grant = {
    'client_id': 'client_id',
    'client_secret': 'secret',
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    'grant_type': 'authorization_code',
}


def test_oauth2_token_retrieval_success(db):
    """
    Given an authorization code, a token can be obtained from the oauth2_token
    view.
    """
    code = setup_oauth2_code(db)
    token_result = api.oauth2_token(DummyRequest(post=dict(_valid_grant, code=code)))
    assert token_result.status == '200 OK'
    j = json.loads(token_result.body.decode())
    assert j.keys() == {'access_token', 'refresh_token', 'scope', 'expires_in', 'token_type'}
    assert j['scope'] == 'wholesite'
    assert j['expires_in'] == 3600
    assert j['token_type'] == 'Bearer'


@pytest.mark.parametrize('override', [
    {'client_id': 'bad_client_id'},
    {'client_secret': 'bad_secret'},
    {'redirect_uri': 'bad:urn:ietf:wg:oauth:2.0:oob'},
    {'grant_type': 'bad_authorization_code'},
    {'code': 'bad code'},
])
def test_oauth2_token_retrieval_failure_on_invalid_parameter(db, override):
    """
    If any parameter to oauth2_token is invalid, the token request will fail
    with an HTTP 400 error.
    """
    code = setup_oauth2_code(db)
    grant = dict(_valid_grant, code=code)
    grant.update(override)
    token_result = api.oauth2_token(DummyRequest(post=grant))
    assert token_result.status == '400 Bad Request'
