from urllib.parse import urlparse

from pyramid.config import Configurator
import pytest
import webtest

from weasyl.views import legacy
from weasyl import hacks


@pytest.fixture(scope='module')
def testapp():
    hacks.install()
    config = Configurator()
    legacy.configure_urls(config)
    return webtest.TestApp(config.make_wsgi_app())


@pytest.mark.parametrize(('old_url', 'redirect_path'), [
    ('/user/spam', '/~spam'),
    ('/profile/spam', '/~spam'),
    ('/submissions/spam', '/~spam/submissions'),
    ('/journals/spam', '/~spam/journals'),
    ('/collections/spam', '/~spam/collections'),
    ('/characters/spam', '/~spam/characters'),
    ('/shouts/spam', '/~spam/shouts'),
    ('/favorites/spam', '/~spam/favorites'),
    ('/friends/spam', '/~spam/friends'),
    ('/following/spam', '/~spam/following'),
    ('/followed/spam', '/~spam/followed'),
    ('/staffnotes/spam', '/~spam/staff-notes'),
    ('/view/123', '/submissions/123/view'),
    ('/view/123/spam', '/submissions/123/view/spam'),
    ('/submission/123', '/submissions/123/view'),
    ('/submission/123/spam', '/submissions/123/view/spam'),
    ('/submission/tag-history/123', '/submissions/123/tag-history'),
    ('/character/123', '/characters/123/view'),
    ('/character/123/spam', '/characters/123/view/spam'),
    ('/journal/123', '/journals/123/view'),
    ('/journal/123/spam', '/journals/123/view/spam'),
])
def test_legacy_redirects(testapp, old_url, redirect_path):
    """
    Legacy redirects forward from an old URL to a new URL via a 301.
    """
    resp = testapp.get(old_url)
    assert resp.status_int == 301
    parsed = urlparse(resp.headers['Location'])
    assert parsed.path == redirect_path
