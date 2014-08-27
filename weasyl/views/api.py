import logging

from pyramid.view import view_config

from ..resources import APIv2Resource
from .. import _version


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


@view_config(name='version', context=APIv2Resource, renderer='json', api='true')
@view_config(name='version.json', context=APIv2Resource, renderer='json', api='true')
def json_version(request):
    return {
        'short_sha': _version.__revision__.lstrip('g'),
        'version': _version.__version__,
    }


@view_config(name='version.txt', context=APIv2Resource, renderer='string', api='true')
def text_version(request):
    return '{0.__version__}-{0.__revision__}'.format(_version)
