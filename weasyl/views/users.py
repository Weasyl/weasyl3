import random
import logging

from pyramid.view import view_config

from ..resources import UserResource
from .. import media
from ..models.content import Submission, Folder


log = logging.getLogger(__name__)


@view_config(context=UserResource, renderer='users/profile.jinja2', api='false', permission='view')
@view_config(context=UserResource, renderer='json', api='true', permission='view')
def view_user(context, request):
    submissions = (
        Submission.query
        .filter(Submission.userid == context.user.userid)
        .order_by(Submission.unixtime.desc())
        .limit(10)
        .all())

    media.populate_with_submission_media(submissions)

    available_featured_submissions = (
        Submission.query
        .join(Folder)
        .filter(Submission.userid == context.user.userid)
        .filter(Folder.is_featured)
        .order_by(Submission.unixtime.desc())
        .all())

    featured = random.choice(available_featured_submissions) if available_featured_submissions else None

    return {
        'user': context.user,
        'submissions': submissions,
        'featured': featured,
        'sidebar': None,
    }


@view_config(name='works', context=UserResource, renderer='users/works.jinja2', api='false', permission='view')
@view_config(name='works', context=UserResource, renderer='json', api='true', permission='view')
def view_user_works(context, request):
    submissions = (
        Submission.query
        .filter(Submission.userid == context.user.userid)
        .order_by(Submission.unixtime.desc())
        .limit(30)
        .all())

    media.populate_with_submission_media(submissions)

    return {
        'user': context.user,
        'submissions': submissions,
        'sidebar': 'works',
    }
