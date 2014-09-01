import logging

from libweasyl.exceptions import ExpectedWeasylError
from ..sessions import make_session_id
from .decorators import also_api_view


log = logging.getLogger(__name__)


@also_api_view(context=Exception, template='errors/generic.jinja2')
def exception_catchall(exc, request):
    expected = isinstance(exc, ExpectedWeasylError)
    request.response.status = 200 if expected else 500
    if not expected and 'sentry.log_error' in request.environ:
        request_id = make_session_id(8)
        event_id, = request.environ['sentry.log_error'](request.exc_info, request_id=request_id)
    else:
        if not expected:
            log.exception(
                'an error occurred, but sentry was not configured to capture it',
                exc_info=request.exc_info)
        request_id = event_id = None
    return {
        'error': True,
        'event_id': event_id,
        'request_id': request_id,
        'message': str(exc),
    }
