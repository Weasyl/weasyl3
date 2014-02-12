import collections
import hashlib
import os

from pyramid.threadlocal import get_current_registry
from sqlalchemy.orm import relationship, foreign, remote, joinedload
import sqlalchemy as sa

from ..text import slug_for
from .. import images
from .content import Submission
from .helpers import JSONValuesColumn
from .meta import Base, DBSession
from .users import Profile


class MediaItem(Base):
    __tablename__ = 'media'

    mediaid = sa.Column(sa.Integer, primary_key=True)
    media_type = sa.Column(sa.String(32), nullable=False)
    file_type = sa.Column(sa.String(8), nullable=False)
    attributes = sa.Column(JSONValuesColumn, nullable=False, server_default='')
    sha256 = sa.Column(sa.String(64))

    __mapper_args__ = dict(polymorphic_on=media_type)

    @classmethod
    def fetch_or_create(cls, data, file_type):
        sha256 = hashlib.sha256(data).hexdigest()
        obj = (cls.query
               .filter(cls.sha256 == sha256)
               .first())
        if obj is None:
            obj = cls(sha256=sha256, file_type=file_type)
            obj.init_from_data(data)
            DBSession.add(obj)
        return obj

    def to_json(self, request, recursive=1, link=None):
        ret = super(MediaItem, self).to_json(request)
        if False and link.link_type == 'submission':
            login_name = link.submission.owner.login_name
            ret['display_url'] = request.resource_path(
                None, '~' + login_name, 'submissions', str(link.submitid),
                '%s-%s-%s.%s' % (
                    login_name, slug_for(link.submission.title), self.mediaid,
                    self.file_type))
        else:
            ret['display_url'] = self.display_url
        if recursive > 0:
            buckets = collections.defaultdict(list)
            for link in self.described:
                buckets[link.link_type].append(
                    link.media_item.to_json(request, recursive=recursive - 1, link=link))
            ret['described'] = dict(buckets)
        else:
            ret['described'] = {}
        if 'width' in self.attributes and 'height' in self.attributes:
            ret['aspect_ratio'] = self.attributes['width'] / self.attributes['height']
        return ret

    def ensure_cover_image(self, source_image=None):
        if self.file_type not in ('jpg', 'png', 'gif'):
            raise ValueError('can only auto-cover image media items')
        cover_link = next((link for link in self.described if link.link_type == 'cover'), None)
        if cover_link is not None:
            return cover_link.media_item

        if source_image is None:
            source_image = self.as_image()
        cover = images.make_cover_image(source_image)
        if cover is source_image:
            cover_media_item = self
        else:
            cover_media_item = fetch_or_create_media_item(
                cover.to_buffer(format=str(self.file_type)), file_type=self.file_type)
        MediaMediaLink.make_or_replace_link(self.mediaid, 'cover', cover_media_item)
        return cover_media_item


class DiskMediaItem(MediaItem):
    __tablename__ = 'disk_media'

    mediaid = sa.Column(sa.Integer, sa.ForeignKey('media.mediaid'), primary_key=True)
    file_path = sa.Column(sa.String(255), nullable=False)
    file_url = sa.Column(sa.String(255), nullable=False)

    __mapper_args__ = dict(polymorphic_identity='disk')

    def init_from_data(self, data):
        fanout = [self.sha256[x:x+2] for x in xrange(0, 6, 2)]
        path = ['static', 'media'] + fanout + ['%s.%s' % (self.sha256, self.file_type)]
        self.file_path = os.path.join(*path)
        self.file_url = '/' + self.file_path
        real_path = self.full_file_path
        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        with open(real_path, 'wb') as outfile:
            outfile.write(data)

    @property
    def display_url(self):
        return self.file_url

    @property
    def full_file_path(self):
        registry = get_current_registry()
        return os.path.join(registry.settings['weasyl.static_root'], self.file_path)

    def to_json(self, request, recursive=1, link=None):
        ret = super(DiskMediaItem, self).to_json(request, recursive=recursive, link=link)
        ret['full_file_path'] = self.full_file_path
        return ret

    def as_image(self):
        return images.read(self.full_file_path.encode())


def fetch_or_create_media_item(*a, **kw):
    return DiskMediaItem.fetch_or_create(*a, **kw)


class _LinkMixin(object):
    cache_func = None
    _linkjoin = ()

    @classmethod
    def refresh_cache(cls, identity):
        if cls.cache_func:
            cls.cache_func.refresh(identity)

    @classmethod
    def clear_link(cls, identity, link_type):
        (cls.query
         .filter(cls.link_type == link_type)
         .filter(getattr(cls, cls._identity) == identity)
         .delete('fetch'))
        cls.refresh_cache(identity)

    @classmethod
    def make_or_replace_link(cls, identity, link_type, media_item, **attributes):
        obj = (cls.query
               .filter(cls.link_type == link_type)
               .filter(getattr(cls, cls._identity) == identity)
               .first())
        if obj is None:
            obj = cls(link_type=link_type)
            setattr(obj, cls._identity, identity)
            DBSession.add(obj)
        obj.media_item = media_item
        obj.attributes = attributes
        cls.refresh_cache(identity)

    @classmethod
    def bucket_links(cls, request, identities):
        if not identities:
            return []
        pairs = (
            request.db.query(MediaItem, cls)
            .with_polymorphic([DiskMediaItem])
            .join(cls, *cls._linkjoin)
            .options(joinedload('described'))
            .options(joinedload(cls._linkname))
            .filter(getattr(cls, cls._identity).in_(identities))
            .all())
        buckets = collections.defaultdict(lambda: collections.defaultdict(list))
        for media_item, link in pairs:
            media_data = media_item.to_json(request, link=link)
            media_data['link_attributes'] = link.attributes
            buckets[getattr(link, cls._identity)][link.link_type].append(media_data)
        return [dict(buckets[identity]) for identity in identities]

    @classmethod
    def register_cache(cls, func):
        cls.cache_func = staticmethod(func)
        return func


class SubmissionMediaLink(Base, _LinkMixin):
    __tablename__ = 'submission_media_links'

    linkid = sa.Column(sa.Integer, primary_key=True)
    mediaid = sa.Column(sa.Integer, sa.ForeignKey('media.mediaid'), nullable=False)
    submitid = sa.Column(sa.Integer, sa.ForeignKey('submission.submitid'), nullable=False, index=True)
    link_type = sa.Column(sa.String(32), nullable=False)
    attributes = sa.Column(JSONValuesColumn, nullable=False, server_default='')

    _identity = 'submitid'
    _linkname = 'submission_links'

    submission = relationship(Submission, backref='media_links')
    media_item = relationship(MediaItem, backref='submission_links')


class UserMediaLink(Base, _LinkMixin):
    __tablename__ = 'user_media_links'

    linkid = sa.Column(sa.Integer, primary_key=True)
    mediaid = sa.Column(sa.Integer, sa.ForeignKey('media.mediaid'), nullable=False)
    userid = sa.Column(sa.Integer, sa.ForeignKey('login.userid'), nullable=False, index=True)
    link_type = sa.Column(sa.String(32), nullable=False)
    attributes = sa.Column(JSONValuesColumn, nullable=False, server_default='')

    _identity = 'userid'
    _linkname = 'user_links'

    user = relationship(
        Profile, backref='media_links',
        primaryjoin=foreign(userid) == remote(Profile.userid))
    media_item = relationship(MediaItem, backref='user_links')


class MediaMediaLink(Base, _LinkMixin):
    __tablename__ = 'media_media_links'

    linkid = sa.Column(sa.Integer, primary_key=True)
    described_with_id = sa.Column(sa.Integer, sa.ForeignKey('media.mediaid'), nullable=False)
    describee_id = sa.Column(sa.Integer, sa.ForeignKey('media.mediaid'), nullable=False, index=True)
    link_type = sa.Column(sa.String(32), nullable=False)
    attributes = sa.Column(JSONValuesColumn, nullable=False, server_default='')

    _identity = 'describee_id'
    _linkname = 'describing'
    _linkjoin = described_with_id == MediaItem.mediaid,
    _type_attributes = JSONValuesColumn()

    describee = relationship(
        MediaItem, backref='described',
        primaryjoin=foreign(describee_id) == remote(MediaItem.mediaid))
    media_item = relationship(
        MediaItem, backref='describing',
        primaryjoin=foreign(described_with_id) == remote(MediaItem.mediaid))
