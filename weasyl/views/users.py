import logging

from pyramid.view import view_config

from ..resources import UserResource


log = logging.getLogger(__name__)


@view_config(context=UserResource, renderer='users/profile.jinja2', api='false', permission='view')
@view_config(context=UserResource, renderer='json', api='true', permission='view')
def view_user(context, request):
    return {'user': context.user}
