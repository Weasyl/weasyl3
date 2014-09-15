import logging

from pyramid.security import Authenticated
from pyramid import httpexceptions

from libweasyl.models.content import Submission
from libweasyl.models.users import Login


log = logging.getLogger(__name__)


class IntermediateResource:
    @classmethod
    def insert(cls, child, segment):
        inst = cls()
        inst.__name__ = child.__name__
        inst.__parent__ = child.__parent__
        child.__name__ = segment
        child.__parent__ = inst
        return child


def make_location_aware(func):
    def __getitem__(self, segment):
        ret = func(self, segment)
        ret.__name__ = segment
        ret.__parent__ = self
        return ret
    return __getitem__


def userid_from_principals(principals):
    return next((p for p in principals if isinstance(p, int)), None)


class SubmissionsResource:
    def __init__(self, request):
        self.request = request

    @make_location_aware
    def __getitem__(self, segment):
        if not segment.isdigit():
            raise KeyError(segment)
        submission = Submission.query.get_or_404(segment)
        if isinstance(self.__parent__, UserResource) and self.__parent__.user != submission.owner:
            raise httpexceptions.HTTPNotFound()
        return SubmissionResource(self.request, submission)


class SubmissionResource:
    def __init__(self, request, submission):
        self.request = request
        self.submission = submission

    def __getitem__(self, segment):
        if segment == 'mod':
            return IntermediateResource.insert(self, segment)
        raise KeyError(segment)

    def permits_view(self, principals):
        # XXX: this probably needs more checks
        if 'g:mod' in principals and (
                self.request.traversed[-1] == 'mod'
                or self.request.GET.get('anyway') == 'true'):
            return True
        if 'hidden' in self.submission.settings:
            return False
        if 'friends-only' in self.submission.settings:
            userid = userid_from_principals(principals)
            return userid and self.submission.owner.is_friends_with(userid)
        return True

    def permits_comment(self, principals):
        # XXX: this needs more checks
        if not self.permits_view(principals):
            return False
        return Authenticated in principals


class UsersResource:
    def __init__(self, request):
        self.request = request

    @make_location_aware
    def __getitem__(self, segment):
        user = Login.query.filter_by(login_name=segment).first_or_404()
        return UserResource(self.request, user)


class MethodDispatchResource:
    def __init__(self, request):
        self.request = request

    @make_location_aware
    def __getitem__(self, segment):
        factory = getattr(self, 'segment_' + segment, None)
        if factory is None:
            raise KeyError(segment)
        return factory(self.request)


class UserResource(MethodDispatchResource):
    def __init__(self, request, user):
        self.request = request
        self.user = user

    def permits_view(self, principals):
        # XXX: this probably needs more checks
        if 'hide-profile-from-guests' in self.user.profile.settings:
            return Authenticated in principals
        return True

    def permits_shout(self, principals):
        # XXX: this needs more checks
        if not self.permits_view(principals):
            return False
        return Authenticated in principals

    segment_submissions = SubmissionsResource


class OAuth2Resource(MethodDispatchResource):
    pass


class APIv2Resource(MethodDispatchResource):
    segment_oauth2 = OAuth2Resource
    segment_submissions = SubmissionsResource
    segment_users = UsersResource

    def __getitem__(self, segment):
        if segment == '_debug' and self.request.is_debug_on:
            return DebugResource(self.request)
        return super().__getitem__(segment)


class APIResource(MethodDispatchResource):
    segment_v2 = APIv2Resource


class DebugResource(MethodDispatchResource):
    pass


class RootResource(MethodDispatchResource):
    __name__ = ''
    __parent__ = None

    segment_submissions = SubmissionsResource
    segment_users = UsersResource
    segment_api = APIResource

    def __getitem__(self, segment):
        if segment.startswith('~'):
            return UsersResource(self.request)[segment[1:]]
        elif segment == '_debug' and self.request.is_debug_on:
            return DebugResource(self.request)
        return super().__getitem__(segment)

    def permits_signin(self, principals):
        return Authenticated not in principals

    def permits_signout(self, principals):
        return Authenticated in principals
