import logging

from pyramid.security import has_permission
from pyramid.view import view_config
from pyramid import httpexceptions
from sqlalchemy.orm import contains_eager

from ..media import populate_with_submission_media
from ..models.content import Submission
from ..models.users import Login
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
    return {'submission': context.submission}


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

    latest_update = (
        SiteUpdate.query
        .order_by(SiteUpdate.updateid.desc())
        .first())

    return {'submissions': submissions, 'latest_update': latest_update}