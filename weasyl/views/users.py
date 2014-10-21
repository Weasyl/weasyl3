import random
import logging

from pyramid.renderers import render_to_response
from pyramid import httpexceptions

from libweasyl.models.content import Comment, Submission, Folder
from libweasyl.models.users import Login, Follow
from libweasyl.media import populate_with_submission_media, populate_with_user_media
from ..resources import UserResource
from .decorators import also_api_view
from .forms import CommentForm, form_renderer


log = logging.getLogger(__name__)


def comment_success(context, request, appstruct):
    if request.is_api_request:
        return render_to_response('json', {'status': 'ok'}, request=request)
    return httpexceptions.HTTPSeeOther('/')


def limit_and_count(query, limit):
    return query.limit(limit).all(), query.count()


@also_api_view(context=UserResource, template='users/profile.jinja2', permission='view')
@form_renderer(CommentForm, 'comment', success=comment_success, button='save',
               name='shout', context=UserResource, renderer='users/profile.jinja2', permission='shout')
def view_user(context, request, forms):
    user = context.user

    following, following_count = limit_and_count(Login.query.with_parent(user), 10)
    followers, follower_count = limit_and_count(Login.query.with_parent(user, property='followers'), 10)

    populate_with_user_media(following)
    populate_with_user_media(followers)
    populate_with_user_media(user.friends[:10])

    # XXX: tag filtering, etc.
    submissions = (
        Submission.query
        .filter(Submission.userid == user.userid)
        .order_by(Submission.unixtime.desc())
        .limit(10)
        .all())

    populate_with_submission_media(submissions)

    # XXX: tag filtering here too
    available_featured_submissions = (
        Submission.query
        .join(Folder)
        .filter(Submission.userid == user.userid)
        .filter(Folder.is_featured)
        .order_by(Submission.unixtime.desc())
        .all())

    featured = random.choice(available_featured_submissions) if available_featured_submissions else None
    n_shouts, shouts = Comment.comment_tree(user)

    ret = forms.copy()
    ret.update({
        'user': user,
        'submissions': submissions,
        'featured': featured,
        'following': following,
        'following_count': following_count,
        'followers': followers,
        'follower_count': follower_count,
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

    populate_with_submission_media(submissions)

    return {
        'user': context.user,
        'submissions': submissions,
        '_sidebar': 'works',
    }
