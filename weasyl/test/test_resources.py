from pyramid.security import Authenticated, Everyone
from pyramid.testing import DummyRequest
from pyramid import httpexceptions
import pytest

from libweasyl.test.common import make_friendship, make_submission, make_user
from weasyl import resources


def assert_lineage(resource, *segments):
    collected = []
    while resource is not None:
        collected.append(resource.__name__)
        resource = resource.__parent__
    collected.reverse()
    assert collected == list(segments)


def rootify(resource, parent=None):
    """
    Give a resource a __name__ and __parent__.

    Most resources won't already have these.
    """
    resource.__name__ = ''
    resource.__parent__ = parent
    return resource


def test_submissions_resource_extant_submission(db):
    """
    A SubmissionsResource queried for an extant submission ID will give back a
    SubmissionResource with the right submission set on it.
    """
    sub = make_submission(db)
    parent = rootify(resources.SubmissionsResource(DummyRequest()))
    child = parent[str(sub.submitid)]
    assert isinstance(child, resources.SubmissionResource)
    assert child.submission.submitid == sub.submitid


def test_submissions_resource_nonextant_submission(db):
    """
    A query for a nonextant submission ID results in an HTTP 404 exception
    getting raised.
    """
    sub = make_submission(db)
    parent = rootify(resources.SubmissionsResource(DummyRequest()))
    with pytest.raises(httpexceptions.HTTPNotFound):
        parent[str(sub.submitid + 1)]


def test_submissions_resource_not_a_number(db):
    """
    A query for a segment that isn't a number (submission numbers can't be
    negative) results in a KeyError.
    """
    parent = rootify(resources.SubmissionsResource(DummyRequest()))
    with pytest.raises(KeyError):
        parent['hello world']


def test_submissions_resource_wrong_owner(db):
    """
    If the parent resource is a UserResource, the UserResource refers to a user
    that isn't the owner of a submission, and a SubmissionsResource is queried
    for that submission, the result is an HTTP 404 exception.
    """
    req = DummyRequest()
    sub = make_submission(db)
    other_user = make_user(db)
    grandparent = resources.UserResource(req, other_user)
    parent = rootify(resources.SubmissionsResource(req), grandparent)
    with pytest.raises(httpexceptions.HTTPNotFound):
        parent[str(sub.submitid)]


def test_submissions_resource_right_owner(db):
    """
    If the parent resource is a UserResource, the UserResource refers to the
    owner of a submission, and a SubmissionsResource is queried for that
    submission, the result is the correct submission.
    """
    req = DummyRequest()
    sub = make_submission(db)
    grandparent = resources.UserResource(req, sub.owner)
    parent = rootify(resources.SubmissionsResource(req), grandparent)
    child = parent[str(sub.submitid)]
    assert isinstance(child, resources.SubmissionResource)
    assert child.submission.submitid == sub.submitid


def update_principals_for_user(db, principals, submission, viewer):
    """
    Update a list of principals to indicate a particular user in relation to a
    submission.

    Currently the relation can be ``'owner'`` to update the principals to refer
    to the submission's owner, ``'friend'`` to refer to a friend of the
    submission's owner, ``'other'`` to refer to some, unrelated user, or
    :py:data:`None` to indicate an anonymous user.
    """
    principals.append(Everyone)
    if viewer == 'owner':
        principals.append(submission.owner.userid)
    elif viewer in ('friend', 'other'):
        other_user = make_user(db)
        principals.append(other_user.userid)
        if viewer == 'friend':
            make_friendship(db, other_user, submission.owner)
    if viewer in ('owner', 'friend', 'other'):
        principals.append(Authenticated)


def update_request_for_features(request, features):
    """
    Update a request object to support some number of features.

    :param features: A collection of strings. If the collection contains the
        string ``'mod'``, ``mod`` will be added to the list of segements
        traversed in the request. If the collection contains the string
        ``anyway``, ``anyway=true`` will be added to the request's GET
        parameters.
    """
    if 'mod' in features:
        request.traversed = ['mod']
    else:
        request.traversed = ['bogus']
    if 'anyway' in features:
        request.GET['anyway'] = 'true'


@pytest.mark.parametrize(('principals', 'viewer', 'features', 'permitted'), [
    ([], 'owner', (), True),
    ([], 'friend', (), True),
    ([], 'other', (), True),
    ([], None, (), True),
    (['g:mod'], 'owner', (), True),
    (['g:mod'], 'other', (), True),
    (['g:mod'], 'other', ('mod',), True),
    (['g:mod'], 'other', ('anyway',), True),
    (['g:mod'], 'owner', ('mod', 'anyway'), True),
    (['g:mod'], 'friend', ('mod', 'anyway'), True),
    (['g:mod'], 'other', ('mod', 'anyway'), True),
])
def test_submission_resource_view_basic_submission(db, principals, viewer, features, permitted):
    """
    A basic submission (i.e. one without any settings set) should be viewable
    by everyone.
    """
    req = DummyRequest()
    sub = make_submission(db)
    resource = resources.SubmissionResource(req, sub)
    update_principals_for_user(db, principals, sub, viewer)
    update_request_for_features(req, features)
    assert resource.permits_view(principals) == permitted


@pytest.mark.parametrize(('principals', 'viewer', 'features', 'permitted'), [
    ([], 'owner', (), False),
    ([], 'friend', (), False),
    ([], 'other', (), False),
    ([], None, (), False),
    (['g:mod'], 'owner', (), False),
    (['g:mod'], 'other', (), False),
    (['g:mod'], 'other', ('mod',), True),
    (['g:mod'], 'other', ('anyway',), True),
    (['g:mod'], 'owner', ('mod', 'anyway'), True),
    (['g:mod'], 'friend', ('mod', 'anyway'), True),
    (['g:mod'], 'other', ('mod', 'anyway'), True),
])
def test_submission_resource_view_hidden_submission(db, principals, viewer, features, permitted):
    """
    A hidden submission should only be viewable by mods who specifically
    request to view it.
    """
    req = DummyRequest()
    sub = make_submission(db, settings=['hidden'])
    resource = resources.SubmissionResource(req, sub)
    update_principals_for_user(db, principals, sub, viewer)
    update_request_for_features(req, features)
    assert resource.permits_view(principals) == permitted


@pytest.mark.parametrize(('principals', 'viewer', 'features', 'permitted'), [
    ([], 'owner', (), True),
    ([], 'friend', (), True),
    ([], 'other', (), False),
    ([], None, (), False),
    (['g:mod'], 'owner', (), True),
    (['g:mod'], 'friend', (), True),
    (['g:mod'], 'other', (), False),
    (['g:mod'], 'other', ('mod',), True),
    (['g:mod'], 'other', ('anyway',), True),
    (['g:mod'], 'owner', ('mod', 'anyway'), True),
    (['g:mod'], 'friend', ('mod', 'anyway'), True),
    (['g:mod'], 'other', ('mod', 'anyway'), True),
])
def test_submission_resource_view_friends_only_submission(db, principals, viewer, features, permitted):
    """
    A friends-only submission should only be viewable by the owner of a
    submission, their friends, and mods who specifically request to view it.
    """
    req = DummyRequest()
    sub = make_submission(db, settings=['friends-only'])
    resource = resources.SubmissionResource(req, sub)
    update_principals_for_user(db, principals, sub, viewer)
    update_request_for_features(req, features)
    assert resource.permits_view(principals) == permitted


@pytest.mark.parametrize(('principals', 'commenter', 'features', 'permitted'), [
    ([], 'owner', (), True),
    ([], 'friend', (), True),
    ([], 'other', (), True),
    ([], None, (), False),
    (['g:mod'], 'owner', (), True),
    (['g:mod'], 'other', (), True),
    (['g:mod'], 'other', ('mod',), True),
    (['g:mod'], 'other', ('anyway',), True),
    (['g:mod'], 'owner', ('mod', 'anyway'), True),
    (['g:mod'], 'friend', ('mod', 'anyway'), True),
    (['g:mod'], 'other', ('mod', 'anyway'), True),
])
def test_submission_resource_comment_basic_submission(db, principals, commenter, features, permitted):
    """
    Anyone who can view a submission can comment on it, unless they're not
    logged in.
    """
    req = DummyRequest()
    sub = make_submission(db)
    resource = resources.SubmissionResource(req, sub)
    update_principals_for_user(db, principals, sub, commenter)
    update_request_for_features(req, features)
    assert resource.permits_comment(principals) == permitted


@pytest.mark.parametrize(('principals', 'commenter', 'features', 'permitted'), [
    ([], 'owner', (), False),
    ([], 'friend', (), False),
    ([], 'other', (), False),
    ([], None, (), False),
    (['g:mod'], 'owner', (), False),
    (['g:mod'], 'other', (), False),
    (['g:mod'], 'other', ('mod',), False),
    (['g:mod'], 'other', ('anyway',), False),
    (['g:mod'], 'owner', ('mod', 'anyway'), False),
    (['g:mod'], 'friend', ('mod', 'anyway'), False),
    (['g:mod'], 'other', ('mod', 'anyway'), False),
])
def test_submission_resource_comment_hidden_submission(db, principals, commenter, features, permitted):
    """
    Nobody can comment on a hidden submission.
    """
    req = DummyRequest()
    sub = make_submission(db, settings=['hidden'])
    resource = resources.SubmissionResource(req, sub)
    update_principals_for_user(db, principals, sub, commenter)
    update_request_for_features(req, features)
    assert resource.permits_comment(principals) == permitted


@pytest.mark.parametrize(('principals', 'commenter', 'features', 'permitted'), [
    ([], 'owner', (), True),
    ([], 'friend', (), True),
    ([], 'other', (), False),
    ([], None, (), False),
    (['g:mod'], 'owner', (), True),
    (['g:mod'], 'friend', (), True),
    (['g:mod'], 'other', (), False),
    (['g:mod'], 'other', ('mod',), True),
    (['g:mod'], 'other', ('anyway',), True),
    (['g:mod'], 'owner', ('mod', 'anyway'), True),
    (['g:mod'], 'friend', ('mod', 'anyway'), True),
    (['g:mod'], 'other', ('mod', 'anyway'), True),
])
def test_submission_resource_comment_friends_only_submission(db, principals, commenter, features, permitted):
    """
    Anyone who can view a friends-only submission can comment on it.
    """
    req = DummyRequest()
    sub = make_submission(db, settings=['friends-only'])
    resource = resources.SubmissionResource(req, sub)
    update_principals_for_user(db, principals, sub, commenter)
    update_request_for_features(req, features)
    assert resource.permits_comment(principals) == permitted
