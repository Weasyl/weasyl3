import logging

from pyramid.security import Allow, Deny, Everyone, Authenticated

from .models.content import Submission


log = logging.getLogger(__name__)


class SubmissionsResource:
    def __init__(self, request):
        self.request = request

    def __getitem__(self, segment):
        submission = Submission.query.get_or_404(int(segment))
        return SubmissionResource(self.request, submission)


class SubmissionResource:
    def __init__(self, request, submission):
        self.request = request
        self.submission = submission


class RootResource:
    __acl__ = [
        (Deny, Authenticated, 'signin'),
        (Allow, Everyone, 'signin'),
        (Allow, Authenticated, 'signout'),
        (Deny, Everyone, 'signout'),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, segment):
        factory = getattr(self, 'segment_' + segment, None)
        if factory is None:
            raise KeyError(segment)
        return factory(self.request)

    segment_submissions = SubmissionsResource
