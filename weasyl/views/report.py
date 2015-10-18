
import logging

import colander as c
import deform.widget as w
from pyramid.response import Response
from pyramid_deform import CSRFSchema
from pyramid.security import remember, forget
from pyramid.view import view_config
from pyramid import httpexceptions

from ..resources import RootResource, SubmissionResource
from .forms import Form, FormView, User


log = logging.getLogger(__name__)


violation_choices = (
                    ('2010', 'Harassing content'),
                    ('2020', 'Tracing or plagiarism'),
                    ('2030', 'Rapidly flashing colors'),
                    ('2040', 'Incorrect content rating'),
                    ('2050', 'Perpetual incorrect tagging'),
                    ('2060', 'Low-quality photography'),
                    ('2070', 'Spamming or flooding'),
                    ('2080', 'Meme or image macro'),
                    ('2090', 'Unacceptable screenshot'),
                    ('2100', 'Non-original audio upload'),
                    ('2110', 'Illegal content'),
                    ('2120', 'Photographic pornography'),
                    ('2999', 'Other (please comment)')
                    )


class SubmissionReportForm(CSRFSchema):
    report_type = c.SchemaNode(
        c.String(),
        widget=w.SelectWidget(values=violation_choices))
    report_comment = c.SchemaNode(
        c.String(), description="Additional Comments", widget=w.TextAreaWidget(
        css_class='comment-entry', placeholder="Additional Comments\u2026"))

    def validator(self, form, values):
        pass


@view_config(name='report', context=SubmissionResource, renderer='report/report_submission.jinja2', permission='report', api='false')
class ReportSubmissionView(FormView):
    schema = SubmissionReportForm()
    buttons = 'submit',

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return Response('hello')

    def report_success(self, appstruct):
        return httpexceptions.HTTPSeeOther(
            '/', headers=remember(self.request, appstruct['user'].userid))


def report_forms(request):
    return {
        'submission': Form(SubmissionReportForm().bind(request=request))
    }
