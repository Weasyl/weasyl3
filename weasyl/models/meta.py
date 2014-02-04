from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import engine_from_config


DBSession = scoped_session(sessionmaker())
Base = declarative_base()


def configure(config, settings):
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    DBSession.configure(bind=engine)
    config.registry.dbmaker = DBSession
    config.add_request_method(db, reify=True)


def db(request):
    session = request.registry.dbmaker()

    def cleanup(request):
        if request.exception:
            session.rollback()
        else:
            session.commit()
        session.close()
    request.add_finished_callback(cleanup)

    return session
