from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
import sqlalchemy as sa

from ..text import slug_for
from .helpers import CharSettingsColumn, RatingColumn, WeasylTimestampColumn
from .meta import Base
from .users import Login


class Tag(Base):
  __tablename__ = "searchtag"

  tagid = sa.Column(sa.Integer, primary_key=True)
  title = sa.Column(sa.Text, nullable=False, unique=True)


class SubmissionTag(Base):
  __tablename__ = 'searchmapsubmit'

  tagid = sa.Column(sa.Integer, sa.ForeignKey('searchtag.tagid'), primary_key=True)
  targetid = sa.Column(sa.Integer, sa.ForeignKey('submission.submitid'), primary_key=True)
  settings = sa.Column(sa.String, nullable=False, server_default='')


class Submission(Base):
    __tablename__ = 'submission'

    submitid = sa.Column(sa.Integer, primary_key=True)
    folderid = sa.Column(sa.Integer, nullable=False, index=True)
    userid = sa.Column(sa.Integer, sa.ForeignKey('login.userid'), index=True)
    unixtime = sa.Column(WeasylTimestampColumn, nullable=False)
    title = sa.Column(sa.String(200), nullable=False)
    content = sa.Column(sa.Text, nullable=False)
    subtype = sa.Column(sa.Integer, nullable=False)
    rating = sa.Column(RatingColumn, nullable=False)
    settings = sa.Column(CharSettingsColumn({
        'h': 'hidden',
        'f': 'friends-only',
        'q': 'critique',
        'p': 'pool',
        'o': 'collaboration',
        't': 'tag-locked',
        'c': 'comment-locked',
        'a': 'admin-locked',
        'e': 'encored',
        'u': 'thumbnail-required',
    }, {
        'embed-type': {
            'D': 'google-drive',
            'v': 'other',
        },
    }), nullable=False, server_default='')
    page_views = sa.Column(sa.Integer, nullable=False, server_default='0')
    sorttime = sa.Column(sa.Integer, nullable=False)
    fave_count = sa.Column(sa.Integer, nullable=False, server_default='0')

    owner = relationship(Login, backref='submissions')
    tag_objects = relationship(Tag, secondary=SubmissionTag.__table__)
    tags = association_proxy('tag_objects', 'title')

    def to_json(self):
        return {
            'title': self.title,
            'rating': self.rating,
        }

    def canonical_path(self, request, operation='view', with_slug=None):
        if with_slug is None:
            with_slug = operation == 'view'
        parts = ['submissions', str(self.submitid), operation]
        if with_slug:
            parts.append(slug_for(self.title))
        return request.resource_path(None, *parts)
