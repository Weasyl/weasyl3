from pyramid import httpexceptions
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, scoped_session, sessionmaker, object_mapper
from sqlalchemy import engine_from_config


class BaseQuery(Query):
    def get_or_404(self, ident):
        ret = self.get(ident)
        if ret is None:
            raise httpexceptions.HTTPNotFound()
        return ret

    def first_or_404(self):
        ret = self.first()
        if ret is None:
            raise httpexceptions.HTTPNotFound()
        return ret


class _BaseObject:
    def to_json(self):
        return {col.name: getattr(self, col.name)
                for col in object_mapper(self).mapped_table.c}


Base = declarative_base(cls=_BaseObject)
DBSession = Base.DBSession = scoped_session(sessionmaker())
Base.query = DBSession.query_property(BaseQuery)


def configure(config, settings):
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)
    config.add_request_method(db, reify=True)


def db(request):
    session = DBSession(query_cls=BaseQuery)

    def cleanup(request):
        if request.exception:
            session.rollback()
        else:
            session.commit()
        session.close()
    request.add_finished_callback(cleanup)

    return session
