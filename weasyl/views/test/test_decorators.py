from pyramid.config import Configurator
import pytest
import webtest

from weasyl.views import decorators
from weasyl import predicates


@pytest.mark.parametrize(('attr', 'value'), [
    ('__doc__', 'spam eggs'),
    ('__module__', 'spam.eggs'),
    ('__name__', 'spam'),
    ('arbitrary', 1),
    ('arbitrary', 'spam eggs'),
])
def test_wraps_respecting_view_config_copies_attributes(attr, value):
    """
    wraps_respecting_view_config copies attributes from one function to
    another, just like functools.wraps.
    """
    def f():
        pass

    setattr(f, attr, value)

    @decorators.wraps_respecting_view_config(f)
    def g():
        pass

    assert getattr(g, attr) == value


@pytest.fixture(scope='module')
def wrapped_testapp():
    config = Configurator()
    config.scan('weasyl.views.test.decorators_support_wrapped')
    return webtest.TestApp(config.make_wsgi_app())


@pytest.mark.parametrize(('url', 'content'), [
    ('/base', b'twice'),
    ('/once', b'twice'),
    ('/twice', b'twice'),
])
def test_wraps_respecting_view_config_copies_view_config_decorations(wrapped_testapp, url, content):
    """
    While only the wrapped-most function gets called, all of the @view_config
    decorations applied to the function being wrapped also apply to the wrapped
    function.
    """
    resp = wrapped_testapp.get(url)
    assert resp.body == content


def is_api_request(request):
    return 'api' in request.GET


@pytest.fixture(scope='module')
def api_testapp():
    config = Configurator()
    config.include('pyramid_jinja2')
    config.add_view_predicate('api', predicates.APIPredicate)
    config.add_request_method(is_api_request, reify=True)
    config.scan('weasyl.views.test.decorators_support_api')
    return webtest.TestApp(config.make_wsgi_app())


def test_also_api_view_creates_a_normal_view(api_testapp):
    """
    also_api_view creates a normal view with the parameters and template
    specified.
    """
    resp = api_testapp.get('/basic')
    assert resp.body == b'spam: eggs'


def test_also_api_view_creates_an_api_view(api_testapp):
    """
    also_api_view also creates an API view with a JSON renderer and the same
    @view_config parameters.
    """
    resp = api_testapp.get('/basic?api=true')
    assert resp.body == b'{"spam": "eggs"}'
