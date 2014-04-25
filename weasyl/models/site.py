from sqlalchemy.orm import relationship

from libweasyl.models import tables
from .meta import Base
from .users import Login


class SiteUpdate(Base):
    __table__ = tables.siteupdate

    owner = relationship(Login, backref='siteupdate')


class Favorite(Base):
    __table__ = tables.favorite
