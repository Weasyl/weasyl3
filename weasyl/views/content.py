import logging

from pyramid.security import has_permission
from pyramid.view import view_config
from pyramid import httpexceptions

from ..resources import SubmissionResource


log = logging.getLogger(__name__)


@view_config(name='view', context=SubmissionResource,
             renderer='content/submission.jinja2', api='false',
             permission='view')
@view_config(name='view', context=SubmissionResource, renderer='json',
             api='true', permission='view')
def view_submission(context, request):
    show_anyway = (
        (len(request.subpath) > 1 and request.subpath[-1] == 'anyway')
        or request.GET.get('anyway') == 'true')
    sub = context.submission
    if 'hidden' in sub.settings:
        if has_permission('view-anything', context, request) and show_anyway:
            pass
        else:
            return httpexceptions.HTTPNotFound()
    return {'submission': context.submission}
