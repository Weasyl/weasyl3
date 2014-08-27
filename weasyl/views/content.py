import logging
import sqlalchemy as sa

from pyramid.renderers import render_to_response
from pyramid.view import view_config
from pyramid import httpexceptions
from sqlalchemy.orm import contains_eager

from ..media import populate_with_submission_media
from ..models.content import Comment, Submission
from ..models.users import Login, UserStream
from ..models.site import SiteUpdate
from ..resources import RootResource, SubmissionResource
from .decorators import also_api_view
from .forms import CommentForm, form_renderer


log = logging.getLogger(__name__)


def comment_success(context, request, appstruct):
    if request.is_api_request:
        return render_to_response('json', {'status': 'ok'}, request=request)
    return httpexceptions.HTTPSeeOther('/')


@also_api_view(name='view', context=SubmissionResource,
               template='content/submission.jinja2', permission='view')
@form_renderer(CommentForm, 'comment', success=comment_success, button='save',
               name='comment', context=SubmissionResource,
               renderer='content/submission.jinja2', permission='comment')
def view_submission(context, request, forms):
    n_comments, comments = Comment.comment_tree(context.submission)
    ret = forms.copy()
    ret.update({
        'submission': context.submission,
        'n_comments': n_comments,
        'comments': comments,
    })
    return ret


@view_config(context=RootResource, renderer='content/index.jinja2', api='false')
def index(request):
    # XXX: tag filtering, etc.
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
        'latest_update': latest_update,
    }
