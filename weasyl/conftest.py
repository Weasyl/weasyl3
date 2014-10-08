import os

from pyramid.httpexceptions import HTTPNotFound
import pytest
import sqlalchemy as sa

from libweasyl.cache import region
from libweasyl.configuration import configure_libweasyl
from libweasyl.models.meta import registry
from libweasyl.models.tables import metadata
from weasyl.media import format_media_link


engine = sa.create_engine(os.environ.get('WEASYL_TEST_SQLALCHEMY_URL', 'postgres:///weasyl_test'))
sessionmaker = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine))


@pytest.fixture(scope='session', autouse=True)
def setup(request):
    db = sessionmaker()
    db.execute('DROP SCHEMA public CASCADE')
    db.execute('CREATE SCHEMA public')
    db.execute('CREATE EXTENSION HSTORE')
    db.commit()
    metadata.create_all(engine)
    region.configure('dogpile.cache.memory')


@pytest.fixture(autouse=True)
def libweasyl(tmpdir):
    tmpdir = tmpdir.join('libweasyl-staticdir')
    configure_libweasyl(
        dbsession=sessionmaker,
        not_found_exception=HTTPNotFound,
        base_file_path=tmpdir.strpath,
        media_link_formatter_callback=format_media_link,
    )
    region.invalidate()


@pytest.fixture
def db(libweasyl, request):
    db = sessionmaker()
    db.rollback()

    def tear_down():
        "Clears all rows from the test database."
        for k, cls in registry.items():
            if not k[0].isupper():
                continue
            db.query(cls).delete()
        db.flush()
        db.commit()

    request.addfinalizer(tear_down)
    return db


def pytest_addoption(parser):
    parser.addoption(
        '--skip-functional', action='store_true', help='skip functional tests')
