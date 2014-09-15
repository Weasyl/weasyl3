import logging

from pyramid.view import view_config

import libweasyl
import weasyl
from ..resources import APIv2Resource


log = logging.getLogger(__name__)


@view_config(name='whoami', context=APIv2Resource, renderer='json', api='true')
def whoami(request):
    if request.current_user:
        return {
            'login': request.current_user.login_name,
            'userid': request.current_user.userid,
        }
    else:
        return {
            'login': None,
            'userid': 0,
        }


package_info = {
    'weasyl': weasyl,
    'libweasyl': libweasyl,
}


@view_config(name='version', context=APIv2Resource, renderer='json', api='true')
@view_config(name='version.json', context=APIv2Resource, renderer='json', api='true')
def json_version(request):
    ret = {}
    for name, package in package_info.items():
        ret[name] = {
            'version': package.__version__,
            'short_hash': package.__sha__.lstrip('g'),
        }
    return ret


@view_config(name='version.txt', context=APIv2Resource, renderer='string', api='true')
def text_version(request):
    ret = []
    for name, info in json_version(request).items():
        if 'short_hash' in info:
            ret.append('%s: %s (%s)' % (name, info['version'], info['short_hash']))
        else:
            ret.append('%s: %s' % (name, info['version']))
    return '\n'.join(sorted(ret))
