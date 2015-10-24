
import logging

import colander as c
import deform.widget as w
from pyramid.response import Response
from pyramid_deform import CSRFSchema
from pyramid.security import remember, forget
from pyramid.view import view_config
from pyramid import httpexceptions

from libweasyl.exceptions import ExpectedWeasylError
from libweasyl.models.content import Report, ReportComment, Submission
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
    violation = c.SchemaNode(
        c.String(),
        widget=w.SelectWidget(values=violation_choices))
    content = c.SchemaNode(
        c.String(), description="Additional Comments", widget=w.TextAreaWidget(
            css_class='comment-entry', placeholder="Additional Comments\u2026"))

    def validator(self, form, values):
        request = form.bindings['request']
        try:
            # XXX: Missing a lot here. Mainly PoC right now.
            # This obviously doesn't make sense. Probably want a better way to get this.
            now = Submission.now()
            rep = Report(urgency=0, opened_at=now, target_sub=request.context.submission.submitid)
            Report.dbsession.add(rep)
            repcom = ReportComment(report=rep, violation=values['violation'], userid=12345, unixtime=now,
                                   content=values['content'])
            Report.dbsession.add(repcom)
            Report.dbsession.flush()
        except ExpectedWeasylError as e:
            raise c.Invalid(form, e.args[0]) from e


@view_config(name='report', context=SubmissionResource, renderer='report/report_submission.jinja2', permission='report', api='false')
class ReportSubmissionView(FormView):
    schema = SubmissionReportForm()
    buttons = 'submit',

    def submit_success(self, appstruct):
        return httpexceptions.HTTPSeeOther('/')


def report_forms(request):
    return {
        'submission': Form(SubmissionReportForm().bind(request=request))
    }
