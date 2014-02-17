import logging
import sqlalchemy as sa

from pyramid.security import has_permission
from pyramid.view import view_config
from pyramid import httpexceptions
from sqlalchemy.orm import contains_eager

from ..media import populate_with_submission_media
from ..models.content import Submission
from ..models.users import Login, UserStream
from ..models.site import SiteUpdate
from ..resources import RootResource, SubmissionResource


log = logging.getLogger(__name__)


@view_config(name='view', context=SubmissionResource,
             renderer='content/submission.jinja2', api='false',
             permission='view')
@view_config(name='view', context=SubmissionResource, renderer='json',
             api='true', permission='view')
def view_submission(context, request):
    show_anyway = (
        (len(request.subpath) > 1 and request.subpath[-1] == 'anyway')
        or request.GET.get('anyway') == 'true')
    sub = context.submission
    if 'hidden' in sub.settings:
        if has_permission('view-anything', context, request) and show_anyway:
            pass
        else:
            return httpexceptions.HTTPNotFound()
    n_comments, comments = context.submission.comment_tree()
    return {
        'submission': context.submission,
        'n_comments': n_comments,
        'comments': comments,
    }


@view_config(context=RootResource, renderer='content/index.jinja2', api='false')
def index(request):
    submissions = (
        Submission.query
        .order_by(Submission.submitid.desc())
        .filter_by(rating=10)
        .join(Login)
        .options(contains_eager(Submission.owner))
        .limit(20)
        .all())
    populate_with_submission_media(submissions)

    streams = (
        UserStream.query
        .filter(sa.func.to_timestamp(UserStream.end_time) > sa.func.now())
        .order_by(UserStream.start_time.desc())
        .all())

    latest_update = (
        SiteUpdate.query
        .order_by(SiteUpdate.updateid.desc())
        .first())

    return {
        'submissions': submissions,
        'streams': streams,
        'latest_update': latest_update
    }
