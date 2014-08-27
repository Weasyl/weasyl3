import logging

from pyramid.view import view_config

from ..exceptions import WeasylError
from ..sessions import make_session_id


log = logging.getLogger(__name__)


@view_config(context=Exception, renderer='errors/generic.jinja2', api='false')
@view_config(context=Exception, renderer='json', api='true')
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
