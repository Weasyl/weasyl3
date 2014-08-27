import random
import logging

from pyramid.renderers import render_to_response
from pyramid import httpexceptions

from ..resources import UserResource
from .. import media
from ..models.content import Comment, Submission, Folder
from .decorators import also_api_view
from .forms import CommentForm, form_renderer


log = logging.getLogger(__name__)


def comment_success(context, request, appstruct):
    if request.is_api_request:
        return render_to_response('json', {'status': 'ok'}, request=request)
    return httpexceptions.HTTPSeeOther('/')


@also_api_view(context=UserResource, template='users/profile.jinja2', permission='view')
@form_renderer(CommentForm, 'comment', success=comment_success, button='save',
               name='shout', context=UserResource, renderer='users/profile.jinja2', permission='shout')
def view_user(context, request, forms):
    # XXX: tag filtering, etc.
    submissions = (
        Submission.query
        .filter(Submission.userid == context.user.userid)
        .order_by(Submission.unixtime.desc())
        .limit(10)
        .all())

    media.populate_with_submission_media(submissions)

    # XXX: tag filtering here too
    available_featured_submissions = (
        Submission.query
        .join(Folder)
        .filter(Submission.userid == context.user.userid)
        .filter(Folder.is_featured)
        .order_by(Submission.unixtime.desc())
        .all())

    featured = random.choice(available_featured_submissions) if available_featured_submissions else None
    n_shouts, shouts = Comment.comment_tree(context.user)

    ret = forms.copy()
    ret.update({
        'user': context.user,
        'submissions': submissions,
        'featured': featured,
        'n_shouts': n_shouts,
        'shouts': shouts,
        '_sidebar': None,
    })
    return ret


@also_api_view(name='works', context=UserResource, template='users/works.jinja2', permission='view')
def view_user_works(context, request):
    # XXX: also tag filtering
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
        '_sidebar': 'works',
    }
