from pyramid import httpexceptions
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from libweasyl.models.meta import BaseQuery


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def configure(config, settings):
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)
    config.add_request_method(db, reify=True)


def db(request):
    return DBSession()
