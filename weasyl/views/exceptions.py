import logging

from ..exceptions import WeasylError
from ..sessions import make_session_id
from .decorators import also_api_view


log = logging.getLogger(__name__)


@also_api_view(context=Exception, template='errors/generic.jinja2')
def exception_catchall(exc, request):
    if not isinstance(exc, WeasylError) and 'sentry.log_error' in request.environ:
        request_id = make_session_id(8)
        exc_info = type(exc), exc, exc.__traceback__
        event_id, = request.environ['sentry.log_error'](exc_info, request_id=request_id)
    else:
        request_id = event_id = None
    return {
        'error': True,
        'event_id': event_id,
        'request_id': request_id,
        'message': str(exc),
    }
