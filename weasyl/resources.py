import logging

from pyramid.security import Allow, Deny, Everyone, Authenticated

from .models.content import Submission
from .models.users import Login


log = logging.getLogger(__name__)


def make_location_aware(func):
    def __getitem__(self, segment):
        ret = func(self, segment)
        ret.__name__ = segment
        ret.__parent__ = self
        return ret
    return __getitem__


class SubmissionsResource:
    __acl__ = [
        (Allow, 'g:mod', 'view'),
        (Allow, 'g:mod', 'view-anything'),
    ]

    def __init__(self, request):
        self.request = request

    @make_location_aware
    def __getitem__(self, segment):
        submission = Submission.query.get_or_404(segment)
        return SubmissionResource(self.request, submission)


class SubmissionResource:
    def __init__(self, request, submission):
        self.request = request
        self.submission = submission

    @property
    def __acl__(self):
        if 'hidden' in self.submission.settings:
            return [
                (Deny, Everyone, 'view'),
            ]
        elif 'friends-only' in self.submission.settings:
            return [
                (Deny, Everyone, 'view'),
            ]
        else:
            return [
                (Allow, Everyone, 'view'),
            ]


class UsersResource:
    def __init__(self, request):
        self.request = request

    @make_location_aware
    def __getitem__(self, segment):
        user = Login.query.filter_by(login_name=segment).first_or_404()
        return UserResource(self.request, user)


class UserResource:
    def __init__(self, request, user):
        self.request = request
        self.user = user

    @property
    def __acl__(self):
        if 'hide-profile-from-guests' in self.user.profile.settings:
            return [
                (Allow, Authenticated, 'view'),
                (Deny, Everyone, 'view'),
            ]
        else:
            return [
                (Allow, Everyone, 'view'),
            ]


class MethodDispatchResource:
    def __init__(self, request):
        self.request = request

    @make_location_aware
    def __getitem__(self, segment):
        factory = getattr(self, 'segment_' + segment, None)
        if factory is None:
            raise KeyError(segment)
        return factory(self.request)


class APIResource(MethodDispatchResource):
    segment_submissions = SubmissionsResource
    segment_users = UsersResource


class RootResource(MethodDispatchResource):
    __name__ = ''
    __parent__ = None

    __acl__ = [
        (Deny, Authenticated, 'signin'),
        (Allow, Everyone, 'signin'),
        (Allow, Authenticated, 'signout'),
        (Deny, Everyone, 'signout'),
    ]

    segment_submissions = SubmissionsResource
    segment_users = UsersResource
    segment_api = APIResource

    def __getitem__(self, segment):
        if segment.startswith('~'):
            return UsersResource(self.request)[segment[1:]]
        return super().__getitem__(segment)
