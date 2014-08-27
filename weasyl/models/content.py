from pyramid.decorator import reify
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import contains_eager, relationship

from libweasyl.models.helpers import clauses_for
from libweasyl.models import tables
from libweasyl.text import markdown, slug_for
from .meta import Base
from .users import Login


class Tag(Base):
    __table__ = tables.searchtag


class SubmissionTag(Base):
    __table__ = tables.searchmapsubmit


class Submission(Base):
    __table__ = tables.submission

    owner = relationship(Login, backref='submissions')
    tag_objects = relationship(Tag, secondary=SubmissionTag.__table__)
    tags = association_proxy('tag_objects', 'title')

    def _comment_criteria(self):
        return {'target_sub': self.submitid}

    def to_json(self, request):
        return {
            'title': self.title,
            'rating': self.rating.name,
        }

    def canonical_path(self, request, operation='view', with_slug=None, mod=False):
        if with_slug is None:
            with_slug = operation == 'view'
        parts = ['submissions', str(self.submitid), operation]
        if mod:
            parts.insert(2, 'mod')
        if with_slug:
            parts.append(slug_for(self.title))
        return request.resource_path(None, *parts)

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
    __table__ = tables.comments

    _target_user = relationship(Login, foreign_keys=[__table__.c.target_user], backref='shouts')
    _target_sub = relationship(Submission, backref='comments')
    poster = relationship(Login, foreign_keys=[__table__.c.userid])

    @property
    def target(self):
        if self.target_user:
            return self._target_user
        elif self.target_sub:
            return self._target_sub
        else:
            raise ValueError('no target user or submission')

    def __json__(self, request):
        return {
            'id': self.commentid,
            'poster': self.poster,
            'children': self.subcomments,
            'content': markdown(self.content),
            'posted_at': self.unixtime,
        }

    subcomments = ()

    @classmethod
    def comment_tree(cls, target):
        # XXX: needs to filter more stuff out
        comments = (
            cls.query
            .filter_by(**target._comment_criteria())
            .join(Login, cls.userid == Login.userid)
            .options(contains_eager(cls.poster))
            .order_by(cls.unixtime.asc())
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
        ret.reverse()
        for comment in comment_map.values():
            comment.subcomments.reverse()
        return len(comment_map), ret



class Folder(Base):
    __table__ = tables.folder

    owner = relationship(Login, backref='folders')
    submissions = relationship(Submission)

    with clauses_for(__table__) as c:
        is_featured = c('featured-filter')
