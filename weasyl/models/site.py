from sqlalchemy.orm import relationship

from .meta import Base
from .users import Login
from . import tables


class SiteUpdate(Base):
    __table__ = tables.siteupdate

    owner = relationship(Login, backref='siteupdate')


class Favorite(Base):
    __table__ = tables.favorite
