import logging

from pyramid.view import view_config

from ..resources import APIv2Resource


log = logging.getLogger(__name__)


@view_config(name='whoami', context=APIv2Resource, renderer='json', api='true')
def whoami(request):
    if request.session.user:
        return {
            'login': request.session.user.login_name,
            'userid': request.session.user.userid,
        }
    else:
        return {
            'login': None,
            'userid': 0,
        }
