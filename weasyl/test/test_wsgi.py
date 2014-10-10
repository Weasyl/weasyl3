import json

from pyramid.testing import DummySecurityPolicy

from libweasyl.test.common import make_user
from weasyl.test.common import auth_policy_request
from weasyl import wsgi


def auth_registry_request(userid, **kwargs):
    policy = DummySecurityPolicy(userid=userid)
    return auth_policy_request(policy, **kwargs)


def test_current_user_logged_out():
    """
    current_user returns None if there is no current user.
    """
    assert wsgi.current_user(auth_registry_request(userid=None)) is None


def test_current_user_logged_in(db):
    """
    current_user returns a user object if there is a current user.
    """
    user = make_user(db)
    fetched_user = wsgi.current_user(auth_registry_request(userid=user.userid))
    assert fetched_user.userid == user.userid


def test_no_leading_underscore_keys_in_json_root_object():
    """
    NoLeadingUnderscoresJSON does, indeed, strip keys with leading underscores
    from the root JSON object.
    """
    serializer = wsgi.NoLeadingUnderscoresJSON()
    j = json.loads(serializer(None)({'_spam': 'eggs', 'eggs': 'spam'}, {}))
    assert j == {'eggs': 'spam'}


def test_leading_underscore_keys_in_object_below_json_root_object():
    """
    Only the root object has keys with leading underscores stripped; objects
    nested under the root object do not get their keys stripped.
    """
    serializer = wsgi.NoLeadingUnderscoresJSON()
    j = json.loads(serializer(None)({'obj': {'_spam': 'eggs', 'eggs': 'spam'}}, {}))
    assert j == {'obj': {'_spam': 'eggs', 'eggs': 'spam'}}


def test_leading_underscore_keys_in_object_below_json_root_array():
    """
    The root of the serialized JSON can also be an array, and leading
    underscores under the root still won't be stripped.
    """
    serializer = wsgi.NoLeadingUnderscoresJSON()
    j = json.loads(serializer(None)([{'_spam': 'eggs', 'eggs': 'spam'}], {}))
    assert j == [{'_spam': 'eggs', 'eggs': 'spam'}]
