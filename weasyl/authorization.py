import logging

from pyramid.interfaces import IAuthorizationPolicy
from zope.interface import implementer

from . import staff


log = logging.getLogger(__name__)


def groupfinder(userid, request):
    ret = list(staff.groups.get(userid, []))
    ret.append('u:%s' % (userid,))
    return ret


@implementer(IAuthorizationPolicy)
class DelegatedAuthorizationPolicy:
    def permits(self, context, principals, permission):
        permits_meth = getattr(context, 'permits_' + permission, None)
        if permits_meth is not None:
            return permits_meth(principals)
        else:
            return False

    def principals_allowed_by_permission(self, context, permission):
        raise NotImplementedError()
