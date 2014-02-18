from pyramid.decorator import reify
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import contains_eager, relationship

from ..text import slug_for
from .helpers import clauses_for
from .meta import Base
from .users import Login
from . import tables


class Tag(Base):
    __table__ = tables.searchtag


class SubmissionTag(Base):
    __table__ = tables.searchmapsubmit


class Submission(Base):
    __table__ = tables.submission

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

    def comment_tree(self):
        comments = (
            Comment.query
            .filter_by(targetid=self.submitid)
            .join(Login)
            .options(contains_eager(Comment.poster))
            .order_by(Comment.unixtime.asc())
            .all())

        comment_map = {}
        ret = []
        users = set()
        for c in comments:
            comment_map[c.commentid] = c
            c.subcomments = []
            if c.parentid:
                comment_map[c.parentid].subcomments.append(c)
            else:
                ret.append(c)
            users.add(c.poster)

        from ..media import populate_with_user_media
        populate_with_user_media(users)
        return len(comment_map), ret

    @reify
    def media(self):
        from ..media import get_submission_media
        return get_submission_media(self.submitid)

    @reify
    def submission_media(self):
        ret = self.media.get('submission')
        if ret:
            return ret[0]
        return None

    @reify
    def cover_media(self):
        ret = self.media.get('cover')
        if not ret and self.submission_media:
            ret = self.submission_media['described'].get('cover')
        if ret:
            return ret[0]
        return None


class Comment(Base):
    __table__ = tables.submitcomment

    target = relationship(Submission, backref='comments')
    poster = relationship(Login, backref='comments')

    subcomments = ()


class Folder(Base):
    __table__ = tables.folder

    owner = relationship(Login, backref='folders')
    submissions = relationship(Submission)

    with clauses_for(__table__) as c:
        is_featured = c('featured')
