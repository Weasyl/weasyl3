import logging

from . import staff


log = logging.getLogger(__name__)


def groupfinder(userid, request):
    ret = list(staff.groups.get(userid, []))
    ret.append('u:%s' % (userid,))
    return ret
