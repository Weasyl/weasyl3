import logging

import pkg_resources
from pyramid.view import view_config

import libweasyl
import weasyl
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


extra_info = {
    'weasyl': weasyl,
    'libweasyl': libweasyl,
}


@view_config(name='version', context=APIv2Resource, renderer='json', api='true')
@view_config(name='version.json', context=APIv2Resource, renderer='json', api='true')
def json_version(request):
    ret = {}
    for dist in pkg_resources.working_set:
        ret[dist.key] = info = {'version': dist.version}
        if dist.key in extra_info:
            info['short_hash'] = extra_info[dist.key].__sha__.lstrip('g')
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
