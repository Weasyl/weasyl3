import logging

from pyramid import httpexceptions

from libweasyl.exceptions import ExpectedWeasylError
from libweasyl.security import generate_key
from .decorators import also_api_view


log = logging.getLogger(__name__)


@also_api_view(context=Exception, template='errors/generic.jinja2')
def exception_catchall(exc, request):
    expected = isinstance(exc, ExpectedWeasylError)
    exc_type = type(exc)
    request.response.status = exc_type.code if expected else 500
    if not expected and 'sentry.log_error' in request.environ:
        request_id = generate_key(8)
        event_id, = request.environ['sentry.log_error'](request.exc_info, request_id=request_id)
    else:
        if not expected:
            log.error(
                'an error occurred, but sentry was not configured to capture it',
                exc_info=request.exc_info)
        request_id = event_id = None
    ret = {
        'error': True,
        'event_id': event_id,
        'request_id': request_id,
    }
    if expected:
        ret.update({
            'message': str(exc),
            'code': exc_type.__name__,
            'description': exc_type.__doc__,
        })
    return ret


@also_api_view(context=httpexceptions.HTTPException, template='errors/generic.jinja2')
def http_exception_catchall(exc, request):
    request.response.status = exc.code
    return {
        'error': True,
        'event_id': None,
        'request_id': None,
        '_http_code': exc.code,
        'code': exc.title,
        'description': None,
        'message': exc.explanation,
    }
