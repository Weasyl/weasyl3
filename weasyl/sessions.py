import collections
import logging
import time

from pyramid.interfaces import ISession, ISessionFactory
from sqlalchemy.orm import contains_eager
from zope.interface import implementer, provider

from libweasyl.models.users import Login, Session
from libweasyl.security import generate_key


log = logging.getLogger(__name__)


@implementer(ISession)
@provider(ISessionFactory)
class WeasylSession(collections.MutableMapping):
    _static_fields = 'userid', 'csrf_token'
    _cookie_name = 'WZL'

    def __init__(self, request):
        self.request = request
        self._changed = False
        self._invalidated = False
        self._dict = {'userid': None, 'csrf_token': None, 'flash': {}}
        cookie = self.request.cookies.get(self._cookie_name)
        self._session_obj = None
        if cookie is not None:
            self._session_obj = (
                Session.query
                .filter_by(sessionid=cookie)
                .outerjoin(Login)
                .options(contains_eager(Session.user))
                .first())
        if self._session_obj is not None:
            self._dict.update(self._session_obj.additional_data)
            self._dict.update({k: getattr(self._session_obj, k) for k in self._static_fields})
            self.created = int(self._session_obj.created_at.timestamp)
        else:
            self.created = time.time()

    def __repr__(self):
        return '<WeasylSession %r>' % (self._dict,)

    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, item, value):
        self._dict[item] = value
        self._changed = True

    def __delitem__(self, item):
        if item in {'userid', 'csrf_token'}:
            self._dict[item] = None
        else:
            del self._dict[item]
        self._changed = True

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def get_csrf_token(self):
        ret = self['csrf_token']
        if not ret:
            ret = self.new_csrf_token()
        return ret

    def new_csrf_token(self):
        ret = self['csrf_token'] = generate_key(64)
        return ret

    def changed(self):
        self._changed = True

    def invalidate(self):
        self._invalidated = True

    def flash(self, msg, queue='', allow_duplicate=True):
        queue = self['flash'].setdefault(queue, [])
        if not allow_duplicate and msg in queue:
            return
        queue.append(msg)
        self.changed()

    def peek_flash(self, queue=''):
        return self['flash'].get(queue, [])

    def pop_flash(self, queue=''):
        ret = self['flash'].pop(queue, [])
        self.changed()
        return ret

    def _serialize(self, request, response):
        if self._invalidated:
            response.delete_cookie(self._cookie_name)
            return
        if not self._changed:
            return
        if self._session_obj is None:
            self._session_obj = Session(sessionid=generate_key(64))
            response.set_cookie(self._cookie_name, value=self._session_obj.sessionid, httponly=True)
        additional_data = self._dict.copy()
        for k in self._static_fields:
            setattr(self._session_obj, k, additional_data.pop(k, None))
        self._session_obj.additional_data = additional_data
        request.db.add(self._session_obj)
        request.db.flush()


def session_tween_factory(handler, registry):
    def session_tween(request):
        response = handler(request)
        request.session._serialize(request, response)
        return response

    return session_tween
