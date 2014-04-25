import logging

import bcrypt
from pyramid.decorator import reify
from sqlalchemy import orm
import sqlalchemy as sa

from libweasyl.legacy import plaintext
from libweasyl.models import tables
from .. import staff
from .meta import Base


log = logging.getLogger(__name__)


class Login(Base):
    __table__ = tables.login

    def _comment_criteria(self):
        return {'target_user': self.userid}

    def canonical_path(self, request, operation=None):
        parts = ['~' + self.login_name]
        if operation is not None:
            parts.append(operation)
        return request.resource_path(None, *parts)

    @reify
    def media(self):
        from ..media import get_user_media
        return get_user_media(self.userid)

    @reify
    def avatar(self):
        return self.media['avatar'][0]

    @reify
    def banner(self):
        if not self.media.get('banner'):
            return None
        return self.media['banner'][0]

    @reify
    def is_staff(self):
        return self.userid in staff.MODS

    def is_friends_with(self, other):
        return bool(
            Friendship.query
            .filter(sa.or_(
                (Friendship.userid == self.userid) & (Friendship.otherid == other),
                (Friendship.otherid == self.userid) & (Friendship.userid == other)))
            .count())

    def is_ignoring(self, other):
        return bool(
            Ignorama.query
            .filter(
                (Ignorama.userid == self.userid) & (Ignorama.otherid == other))
            .count())

    def is_ignored_by(self, other):
        return bool(
            Ignorama.query
            .filter(
                (Ignorama.userid == other) & (Ignorama.otherid == self.userid))
            .count())

    def __json__(self, request):
        return {
            'login': self.login_name,
            'username': self.profile.username,
            'full_name': self.profile.full_name,
        }


class AuthBCrypt(Base):
    __table__ = tables.authbcrypt

    user = orm.relationship(Login, backref=orm.backref('bcrypt', uselist=False))

    def does_authenticate(self, password):
        if bcrypt.hashpw(password.encode('utf-8'), self.hashsum) == self.hashsum:
            return True
        elif bcrypt.hashpw(plaintext(password).encode('utf-8'), self.hashsum) == self.hashsum:
            log.debug('updated old non-ASCII password for userid %d', self.userid)
            self.set_password(password)
            return True
        else:
            return False

    def set_password(self, password):
        self.hashsum = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(13))


class Profile(Base):
    __table__ = tables.profile

    user = orm.relationship(Login, backref=orm.backref('profile', uselist=False, lazy='joined'))


class Session(Base):
    __table__ = tables.sessions

    user = orm.relationship(Login, backref='sessions')

    def __repr__(self):
        return '<Session for %s: %r>' % (self.userid, self.additional_data)


class UserStream(Base):
    __table__ = tables.user_streams

    owner = orm.relationship(Login, backref='user_streams')


class Friendship(Base):
    __table__ = tables.frienduser


class Ignorama(Base):
    __table__ = tables.ignoreuser
