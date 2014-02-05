import logging

from pyramid.view import view_config

from ..resources import SubmissionResource


log = logging.getLogger(__name__)


@view_config(name='view', context=SubmissionResource, renderer='content/submission.jinja2')
def view_submission(context, request):
    return {'sub': context.submission}
