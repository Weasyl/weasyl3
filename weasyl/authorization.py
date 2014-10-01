"""
Authorization!

The contents of this module are for determining what things a user can and
can't do once successfully authenticated.
"""

import logging

from pyramid.interfaces import IAuthorizationPolicy
from zope.interface import implementer

from . import staff


log = logging.getLogger(__name__)


def groupfinder(userid, request):
    """
    Determine what additional groups a userid belongs to.

    Note that this doesn't validate the userid; it's assumed that the
    authentication policy will only return valid userids from their
    ``unauthenticated_userid`` methods. In practice this works out just fine
    since Weasyl controls all of the used authentication policies.

    The only additional groups returned by this function correspond to staff
    roles. That is: ``g:director``, ``g:admin``, ``g:mod``, and ``g:tech``.
    """
    return staff.groups.get(userid, [])


@implementer(IAuthorizationPolicy)
class DelegatedAuthorizationPolicy:
    """
    An authorization policy which delegates its permission checking.
    """

    def permits(self, context, principals, permission):
        """
        Determine whether a particular permission is permitted for a resource.

        This determination is done by delegating the check to the resource
        itself. It's assumed that for a permission ``spam``, the resource will
        have a ``permits_spam`` method on it. These delegates are expected to
        be unary callables which take the list of principals as their only
        argument. If the method doesn't exist on the resource, the default
        behavior is to deny access.
        """
        permits_meth = getattr(context, 'permits_' + permission, None)
        if permits_meth is not None:
            return permits_meth(principals)
        else:
            return False

    def principals_allowed_by_permission(self, context, permission):
        """
        It's not feasible to determine this, so just raise an error.

        Weasyl doesn't even need this anywhere.
        """
        raise NotImplementedError()
