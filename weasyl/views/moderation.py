from pyramid.view import view_config
from sqlalchemy.orm import contains_eager

from libweasyl.models.content import Report
from libweasyl.models.users import Login
from ..resources import ModResource


@view_config(context=ModResource, renderer='mod/mod.jinja2', permission='mod', api='false')
def mod_portal(context, request):
    return dict()


@view_config(name='reports', context=ModResource, renderer='mod/reports.jinja2', permission='mod', api='false')
def reports(context, request):
    status = request.GET.get('status')
    violation = request.GET.get('violation')
    submitter = request.GET.get('submitter')

    mreports = (
        Report.query
        .order_by(Report.reportid.desc())
        .limit(20)
        .all())

    return {'reports': mreports}
