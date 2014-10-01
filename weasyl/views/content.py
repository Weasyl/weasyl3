import logging
import os
import sqlalchemy as sa

from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config
from pyramid import httpexceptions
from sqlalchemy.orm import contains_eager

from libweasyl.media import populate_with_submission_media
from libweasyl.models.content import Comment, Submission
from libweasyl.models.users import Login, UserStream
from libweasyl.models.site import SiteUpdate
from ..resources import RootResource, SubmissionResource, SubmissionsResource
from .decorators import also_api_view
from .forms import CommentForm, form_renderer


log = logging.getLogger(__name__)


def comment_success(context, request, appstruct):
    log.debug('comment success: %r', appstruct)
    if request.is_api_request:
        return render_to_response('json', {'status': 'ok'}, request=request)
    #TODO: Hacky?
    redirect_url = appstruct["comment_obj"]._target_sub.canonical_path(request)
    return httpexceptions.HTTPSeeOther(redirect_url)


@also_api_view(name='view', context=SubmissionResource,
               template='content/submission.jinja2', permission='view')
@view_config(context=SubmissionResource, renderer='content/submission.jinja2', permission='view')
@form_renderer(CommentForm, 'comment', success=comment_success, button='post',
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


@view_config(name='media', context=SubmissionResource, api='false')
def view_submission_media(context, request):
    if len(request.subpath) != 2:
        return httpexceptions.HTTPNotFound()
    link_type, filename = request.subpath
    base, ext = os.path.splitext(filename)
    _, _, mediaid = base.rpartition('-')
    if not mediaid.isdigit():
        return httpexceptions.HTTPNotFound()
    mediaid = int(mediaid)
    media = context.submission.media
    if link_type not in media:
        return httpexceptions.HTTPNotFound()
    media_item = next((m for m in media[link_type] if m['mediaid'] == mediaid), None)
    if media_item is None:
        return httpexceptions.HTTPNotFound()
    return Response(status=204, headers={
        'X-Accel-Redirect': media_item['file_url'],
        'Cache-Control': 'max-age=0',
    })


@view_config(name='frontpage', context=SubmissionsResource, renderer='json', api='true')
def frontpage_submissions(request):
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

    return {'submissions': submissions}


@view_config(context=RootResource, renderer='content/index.jinja2', api='false')
def index(request):
    streams = (
        UserStream.query
        .filter(sa.func.to_timestamp(UserStream.end_time) > sa.func.now())
        .order_by(UserStream.start_time.desc())
        .all())

    latest_update = (
        SiteUpdate.query
        .order_by(SiteUpdate.updateid.desc())
        .first())

    ret = frontpage_submissions(request)
    ret.update({
        'streams': streams,
        'latest_update': latest_update,
    })
    return ret
