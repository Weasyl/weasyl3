import logging
import sqlalchemy as sa

import colander as c
import deform.widget as w
from pyramid_deform import CSRFSchema
from pyramid.renderers import render_to_response
from pyramid.security import has_permission
from pyramid.view import view_config
from pyramid import httpexceptions
from sqlalchemy.orm import contains_eager

from ..media import populate_with_submission_media
from ..models.content import Submission
from ..models.users import Login, UserStream
from ..models.site import SiteUpdate
from ..resources import RootResource, SubmissionResource
from .forms import form_renderer


log = logging.getLogger(__name__)


class Comment(CSRFSchema):
    comment = c.SchemaNode(
        c.String(), description="Share your thoughts \u2026",
        widget=w.TextAreaWidget(css_class='comment-entry'))


def comment_success(context, request, appstruct):
    if request.is_api_request:
        return render_to_response('json', {'status': 'ok'}, request=request)
    return httpexceptions.HTTPSeeOther('/')


@view_config(name='view', context=SubmissionResource,
             renderer='content/submission.jinja2', api='false',
             permission='view')
@view_config(name='view', context=SubmissionResource, renderer='json',
             api='true', permission='view')
@form_renderer(Comment, 'comment', success=comment_success, button='save',
               name='comment', context=SubmissionResource,
               renderer='content/submission.jinja2', permission='comment')
def view_submission(context, request, forms):
    n_comments, comments = context.submission.comment_tree()
    ret = forms.copy()
    ret.update({
        'submission': context.submission,
        'n_comments': n_comments,
        'comments': comments,
    })
    return ret


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
