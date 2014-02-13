import sqlalchemy as sa
from sqlalchemy.orm import relationship

from .helpers import WeasylTimestampColumn
from .meta import Base
from .users import Login

class SiteUpdate(Base):
    __tablename__ = 'siteupdate'

    updateid = sa.Column(sa.Integer, primary_key=True)
    userid = sa.Column(sa.Integer, sa.ForeignKey('login.userid'))
    title = sa.Column(sa.String(100), nullable=False)
    content = sa.Column(sa.Text, nullable=False)
    unixtime = sa.Column(WeasylTimestampColumn, nullable=False)

    owner = relationship(Login, backref='siteupdate')
