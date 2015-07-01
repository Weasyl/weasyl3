"""
A collection of ugly hacks.

Currently this is limited to two hacks to make pyramid behave slightly
differently:

- ``~`` is no longer escaped when building URLs. `RFC 2396`_ allows it, and
  there are arguments for escaped tildes, but the unescaped version has become
  the canonical URL for Weasyl user pages.
- Calling :py:meth:`~pyramid.request.Request.resource_path` can take
  :py:data:`None` as the resource. It's unclear why this was removed in later
  versions of pyramid, as it's a useful feature. Specifically, it means 'from
  the application root'.

Yes, it is technically monkeypatching.

.. _RFC 2396: https://www.ietf.org/rfc/rfc2396.txt
"""

import functools

from pyramid.traversal import quote_path_segment
from pyramid import traversal, url


@functools.lru_cache(1000)
def _join_elements(elements):
    return '/'.join([quote_path_segment(s, safe=':@&+$,~') for s in elements])


class _Root:
    pass

_Root.__name__ = ''


def _lineage(resource):
    """
    Return a generator representing the :term:`lineage` of the
    :term:`resource` object implied by the ``resource`` argument.  The
    generator first returns ``resource`` unconditionally.  Then, if
    ``resource`` supplies a ``__parent__`` attribute, return the resource
    represented by ``resource.__parent__``.  If *that* resource has a
    ``__parent__`` attribute, return that resource's parent, and so on,
    until the resource being inspected either has no ``__parent__``
    attribute or which has a ``__parent__`` attribute of :py:data:`None`.
    For example, if the resource tree is::

      thing1 = Thing()
      thing2 = Thing()
      thing2.__parent__ = thing1

    Calling ``lineage(thing2)`` will return a generator.  When we turn
    it into a list, we will get::

      list(lineage(thing2))
      [ <Thing object at thing2>, <Thing object at thing1> ]
    """
    if resource is None:
        yield _Root
        return

    while resource is not None:
        yield resource
        # The common case is that the AttributeError exception below
        # is exceptional as long as the developer is a "good citizen"
        # who has a root object with a __parent__ of None.  Using an
        # exception here instead of a getattr with a default is an
        # important micro-optimization, because this function is
        # called in any non-trivial application over and over again to
        # generate URLs and paths.
        try:
            resource = resource.__parent__
        except AttributeError:
            resource = None



def install():
    """
    Install the ugly hacks.

    There is currently no way to reverse the process.
    """
    # ugly hack to make ~ not escaped in URLs
    url._join_elements = _join_elements

    # ugly hack to make None work as a root
    traversal.lineage = _lineage
