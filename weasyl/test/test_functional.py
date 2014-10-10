import os

import pytest
import webtest

from weasyl.test.common import skip_functional
from weasyl import wsgi


pytestmark = skip_functional


@pytest.fixture(scope='module')
def testapp():
    app = wsgi.make_app({}, **{
        'sqlalchemy.url': os.environ.get('WEASYL_TEST_SQLALCHEMY_URL', 'postgres:///weasyl_test'),
        'cache.backend': 'dogpile.cache.memory',
        'weasyl.static_root': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
    })
    return webtest.TestApp(app)
