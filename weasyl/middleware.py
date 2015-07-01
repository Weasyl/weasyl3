import logging
import sys

from pyramid.threadlocal import get_current_request
import raven

from libweasyl.security import generate_key


log = logging.getLogger(__name__)


class SentryMiddleware:
    def __init__(self, app, global_config, **kwargs):
        self.app = app
        self.client = raven.Client(kwargs['sentry.dsn'])

    def __call__(self, environ, start_response):
        environ['sentry.log_error'] = self.log_error
        environ['sentry.log_message'] = self.log_message

        try:
            return self.app(environ, start_response)
        except Exception:
            exc_info = sys.exc_info()
        request_id = generate_key(8)
        event_id, = self.log_error(exc_info, request_id=request_id)
        start_response(
            '500 Internal Server Error',
            [('Content-Type', 'text/plain')],
            exc_info)
        return [('%s-%s' % (event_id, request_id)).encode('utf-8')]

    def raven_capture_arguments(self, extra):
        data = {}
        if 'level' in extra:
            data['level'] = extra.pop('level')
        request = get_current_request()
        if request is not None:
            extra['request'] = vars(request)
            extra['session'] = request.session
        return dict(data=data, extra=extra)

    def log_error(self, exc_info, **extra):
        kwargs = self.raven_capture_arguments(extra)
        log.error('raven error: %r', kwargs, exc_info=exc_info)
        return self.client.captureException(exc_info, **kwargs)

    def log_message(self, message, **extra):
        kwargs = self.raven_capture_arguments(extra)
        log.info('raven message: %r %r', kwargs)
        return self.client.captureMessage(message, **kwargs)
