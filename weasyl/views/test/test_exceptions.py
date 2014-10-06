import sys

from pyramid.testing import DummyRequest
from pyramid import httpexceptions
import pytest
from testfixtures import LogCapture

from libweasyl.exceptions import ExpectedWeasylError
from weasyl.views import exceptions


def fake_exc_info_request(exc_value=RuntimeError(), **kwargs):
    try:
        raise exc_value
    except:
        return DummyRequest(exc_info=sys.exc_info(), **kwargs)


def test_unexpected_exceptions_get_logged_without_sentry():
    """
    If sentry is not configured in the environment, in the case of an
    unexpected exception, a log message gets emitted.
    """
    request = fake_exc_info_request()
    with LogCapture() as l:
        exceptions.exception_catchall(RuntimeError(), request)
    assert len(l.records) == 1
    assert l.records[-1].exc_info == request.exc_info
    assert l.records[-1].msg == 'an error occurred, but sentry was not configured to capture it'


def test_expected_exceptions_do_not_get_logged_without_sentry():
    """
    If sentry is not configured in the environment, in the case of an
    expected exception, no log messages are emitted.
    """
    with LogCapture() as l:
        exceptions.exception_catchall(ExpectedWeasylError(), DummyRequest())
    assert len(l.records) == 0


def test_unexpected_exceptions_have_almost_bare_contexts():
    """
    Unexpected exceptions don't return much from the view function.
    """
    request = fake_exc_info_request()
    result = exceptions.exception_catchall(RuntimeError(), request)
    assert result.keys() == {'error', 'event_id', 'request_id'}
    assert result['error']


def test_expected_exceptions_have_more_in_their_contexts():
    """
    Expected exceptions return more information from the view function.
    """
    exc = ExpectedWeasylError('spam eggs')
    request = fake_exc_info_request(exc)
    result = exceptions.exception_catchall(exc, request)
    assert result.keys() == {'error', 'event_id', 'request_id', 'message', 'code', 'description'}
    assert result['error']
    assert result['message'] == 'spam eggs'
    assert result['code'] == 'ExpectedWeasylError'
    assert result['description'] == ExpectedWeasylError.__doc__


@pytest.mark.parametrize(('expected', 'with_sentry', 'has_id'), [
    (False, False, False),
    (False, True, True),
    (True, False, False),
    (True, True, False),
])
def test_exception_returned_ids(expected, with_sentry, has_id):
    """
    Whether or not the view function returns non-None event_id and request_id
    depends on whether the error was expected and whether sentry is configured.
    """
    exc = ExpectedWeasylError() if expected else RuntimeError()
    environ = {}
    if with_sentry:
        def log_error(exc_info, request_id):
            return 'spam eggs',
        environ['sentry.log_error'] = log_error
    request = fake_exc_info_request(exc, environ=environ)
    result = exceptions.exception_catchall(exc, request)
    if has_id:
        assert result['event_id'] == 'spam eggs'
        assert result['request_id'] is not None
    else:
        assert result['event_id'] is None
        assert result['request_id'] is None


def test_log_error_passed_exc_info():
    """
    The sentry.log_error function is passed the exc_info from the request.
    """
    called = False
    def log_error(exc_info, request_id):
        nonlocal called
        assert exc_info == request.exc_info
        called = True
        return 'spam eggs',
    environ = {'sentry.log_error': log_error}
    request = fake_exc_info_request(environ=environ)
    exceptions.exception_catchall(request.exc_info[0], request)
    assert called


def test_http_exception_catchall_response_status():
    """
    http_exception_catchall sets the response's status code appropriately.
    """
    req = DummyRequest()
    exceptions.http_exception_catchall(httpexceptions.HTTPGone(), req)
    assert req.response.status == '410 Gone'


def test_http_exception_catchall_context():
    """
    http_exception_catchall returns context describing the exception.
    """
    result = exceptions.http_exception_catchall(httpexceptions.HTTPGone(), DummyRequest())
    assert result.keys() == {'error', 'event_id', 'request_id', '_http_code', 'code', 'description', 'message'}
    assert result['error']
    assert result['event_id'] is None
    assert result['request_id'] is None
    assert result['_http_code'] == 410
    assert result['code'] == 'Gone'
    assert result['description'] is None
    assert result['message']
