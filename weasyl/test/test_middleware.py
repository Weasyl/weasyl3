import sys

from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
import pytest
import webtest

from libweasyl.test.common import Bag
from weasyl import middleware


class FakeRavenClient:
    event_id = 'event'

    def __init__(self):
        self.exceptions = []
        self.messages = []

    def __call__(self, dsn):
        self.dsn = dsn
        return self

    def captureException(self, exc_info, **kwargs):
        self.exceptions.append((exc_info, kwargs))
        return self.event_id,

    def captureMessage(self, message, **kwargs):
        self.messages.append((message, kwargs))
        return self.event_id,


def test_sentry_dsn_passed(monkeypatch):
    """
    The DSN is passed from the SentryMiddleware to the raven Client.
    """
    raven = Bag(Client=FakeRavenClient())
    monkeypatch.setattr(middleware, 'raven', raven)
    app = middleware.SentryMiddleware(None, {}, **{'sentry.dsn': 'dsn'})
    assert app.client.dsn == 'dsn'


def raise_exc_view(request):
    raise RuntimeError('oh no!')


def log_message_view(request):
    return {
        'event': request.environ['sentry.log_message']('spam eggs'),
    }


def log_error_view(request):
    try:
        raise_exc_view(request)
    except Exception:
        exc_info = sys.exc_info()
    return {
        'event': request.environ['sentry.log_error'](exc_info),
    }


@pytest.fixture(scope='module')
def sentry_wsgiapp():
    config = Configurator()
    config.set_session_factory(SignedCookieSessionFactory('secret'))
    config.add_view(raise_exc_view, name='raise')
    config.add_view(log_message_view, name='log-message', renderer='json')
    config.add_view(log_error_view, name='log-error', renderer='json')
    return config.make_wsgi_app()


@pytest.fixture
def raven_client(monkeypatch):
    raven = Bag(Client=FakeRavenClient())
    monkeypatch.setattr(middleware, 'raven', raven)
    return raven.Client


@pytest.fixture
def sentry_testapp(raven_client, sentry_wsgiapp):
    app = middleware.SentryMiddleware(sentry_wsgiapp, {}, **{'sentry.dsn': 'dsn'})
    return webtest.TestApp(app)


def test_sentry_exception_capturing_returns_500(sentry_testapp):
    """
    SentryMiddleware captures exceptions raised by the wrapped WSGI app and
    turns them into 500 status code responses.
    """
    resp = sentry_testapp.get('/raise', expect_errors=True)
    assert resp.status_int == 500


def test_sentry_exception_capturing_logs_error(raven_client, sentry_testapp):
    """
    Captured exceptions get logged as errors to the raven Client.
    """
    sentry_testapp.get('/raise', status=500)
    [(exc_info, kwargs)] = raven_client.exceptions
    assert exc_info[0] == RuntimeError
    assert isinstance(exc_info[1], RuntimeError)
    assert kwargs.keys() == {'data', 'extra'}
    assert not kwargs['data']
    assert kwargs['extra'].keys() == {'request_id'}
    assert kwargs['extra']['request_id']


def test_sentry_log_message_in_environment(raven_client, sentry_testapp):
    """
    SentryMiddleware puts a 'sentry.log_message' callable into the WSGI
    environment, which can be used to log messages.
    """
    raven_client.event_id = 'log_message'
    resp = sentry_testapp.get('/log-message')
    assert resp.json == {'event': ['log_message']}
    [(message, kwargs)] = raven_client.messages
    assert message == 'spam eggs'
    assert kwargs.keys() == {'data', 'extra'}
    assert not kwargs['data']
    assert kwargs['extra'].keys() == {'request', 'session'}


def test_sentry_log_exception_in_environment(raven_client, sentry_testapp):
    """
    SentryMiddleware puts a 'sentry.log_error' callable into the WSGI
    environment, which can be used to log errors.
    """
    raven_client.event_id = 'log_error'
    resp = sentry_testapp.get('/log-error')
    assert resp.json == {'event': ['log_error']}
    [(exc_info, kwargs)] = raven_client.exceptions
    assert exc_info[0] == RuntimeError
    assert isinstance(exc_info[1], RuntimeError)
    assert kwargs.keys() == {'data', 'extra'}
    assert not kwargs['data']
    assert kwargs['extra'].keys() == {'request', 'session'}
