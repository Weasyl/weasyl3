import logging

import bcrypt
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy import orm
import sqlalchemy as sa

from ..legacy import plaintext
from .helpers import CharSettingsColumn, JSONValuesColumn, WeasylTimestampColumn
from .meta import Base


log = logging.getLogger(__name__)


class Login(Base):
    __tablename__ = 'login'

    userid = sa.Column(sa.Integer, primary_key=True)
    login_name = sa.Column(sa.String(40), nullable=False, unique=True)
    salt = sa.Column(sa.String(40), nullable=False)
    passhash = sa.Column(sa.String(40), nullable=False)
    last_login = sa.Column(WeasylTimestampColumn, nullable=False)
    settings = sa.Column(CharSettingsColumn({
        'p': 'reset-password',
        'i': 'reset-birthday',
        'e': 'reset-email',
    }, {
        'account-state': {
            'd': 'premium',
            'b': 'banned',
            's': 'suspended',
        },
    }), nullable=False, server_default='')
    email = sa.Column(sa.String(100), nullable=False, server_default='')


class AuthBCrypt(Base):
    __tablename__ = 'authbcrypt'

    userid = sa.Column(sa.Integer, sa.ForeignKey('login.userid'), primary_key=True)
    hashsum = sa.Column(sa.String(100), nullable=False)

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
    __tablename__ = 'profile'

    userid = sa.Column(sa.Integer, sa.ForeignKey('login.userid'), primary_key=True)
    username = sa.Column(sa.String(40), nullable=False, unique=True)
    full_name = sa.Column(sa.String(100), nullable=False)
    catchphrase = sa.Column(sa.String(200), nullable=False, server_default='')
    artist_type = sa.Column(sa.String(100), nullable=False, server_default='')
    unixtime = sa.Column(WeasylTimestampColumn, nullable=False)
    profile_text = sa.Column(sa.Text, nullable=False, server_default='')
    settings = sa.Column(sa.String(20), nullable=False, server_default='ccci')
    stream_url = sa.Column(sa.String(500), nullable=False, server_default='')
    page_views = sa.Column(sa.Integer, nullable=False, server_default='0')
    config = sa.Column(CharSettingsColumn({
        'b': 'show-birthday',
        '2': '12-hour-time',

        'l': 'use-only-tag-blacklist',

        'g': 'tagging-disabled',
        'd': 'premium',

        'w': 'staff-shouts-only',
        'x': 'friend-shouts-only',
        'y': 'staff-notes-only',
        'z': 'friend-notes-only',
        'h': 'hide-profile-from-guests',
        'i': 'hide-profile-stats',
        'k': 'disallow-others-tag-removal',
        'r': 'disallow-others-tag-editing',

        's': 'watch-user-submissions',
        'c': 'watch-user-collections',
        'f': 'watch-user-characters',
        't': 'watch-user-stream-status',
        'j': 'watch-user-journals',

        'o': 'watch-group-collections',
        'n': 'watch-group-journals',
        'e': 'watch-group-events',
    }, {
        'tagging-level': {
            'm': 'max-rating-moderate',
            'a': 'max-rating-mature',
            'p': 'max-rating-explicit',
        },
        'thumbnail-bar': {
            'O': 'collections',
            'A': 'characters',
        },
    }), nullable=False, server_default='')
    stream_time = sa.Column(sa.Integer)
    stream_text = sa.Column(sa.String)

    user = orm.relationship(Login, backref=orm.backref('profile', uselist=False))


class Session(Base):
    __tablename__ = 'sessions'

    sessionid = sa.Column(sa.String(64), primary_key=True)
    created_at = sa.Column(
        TIMESTAMP, nullable=False, server_default='now()', index=True)
    userid = sa.Column(sa.Integer, sa.ForeignKey('login.userid'))
    csrf_token = sa.Column(sa.String(64))
    additional_data = sa.Column(JSONValuesColumn(), nullable=False, server_default='')

    user = orm.relationship(Login, backref='sessions')

    def __repr__(self):
        return '<Session for %s: %r>' % (self.userid, self.additional_data)
