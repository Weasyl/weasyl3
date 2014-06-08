import functools
import logging

import colander as c
import deform.widget as w
from deform.exception import ValidationFailure
from deform.form import Form as _Form
from pyramid_deform import FormView as _FormView, CSRFSchema
from pyramid.view import view_config
from translationstring import TranslationStringFactory

from libweasyl.legacy import login_name
from ..models.users import Login


_ = TranslationStringFactory(__name__)
log = logging.getLogger(__name__)


def determine_errors(exc):
    return [(t[-1].node, list(c.interpolate(t[-1].messages()))) for t in exc.error.paths()]


class Form(_Form):
    def determine_autofocus(self):
        for field in self:
            if not field.error or isinstance(field.widget, w.HiddenWidget):
                continue
            field.autofocus = True
            log.debug('%r autofocused %r', self, field)
            return
        log.debug("%r couldn't autofocus anything", self)
        self.focus_on_submit = True


class FormView(_FormView):
    form_class = Form
    form_key = '_form'
    errors_key = '_errors'

    def extra_fields(self):
        return {}

    def failure(self, exc):
        errors = determine_errors(exc)
        log.debug('form failed to validate: %r', errors)
        ret = {self.form_key: exc.field, self.errors_key: errors}
        ret.update(self.extra_fields())
        exc.field.determine_autofocus()
        return ret

    def show(self, form):
        ret = {self.form_key: form}
        ret.update(self.extra_fields())
        return ret


class User(c.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is c.null:
            return appstruct
        return appstruct.profile.username

    def deserialize(self, node, cstruct):
        if cstruct is c.null:
            return cstruct
        user = Login.query.filter_by(login_name=login_name(cstruct)).first()
        if user is None:
            raise c.Invalid(node, _('"${val}" is not a valid username', mapping=dict(val=cstruct)))
        return user


def form_renderer(schema, key, *, success, button, **kwargs):
    form_key = '_%s_form' % (key,)
    errors_key = '_%s_errors' % (key,)
    def deco(func):
        @view_config(_depth=1, request_method='POST', **kwargs)
        @functools.wraps(func)
        def wrapper(context, request, forms=()):
            forms = dict(forms)
            form = forms[form_key] = Form(schema().bind(request=request))
            forms[errors_key] = None

            if button in request.POST:
                controls = request.POST.items()
                try:
                    validated = form.validate(controls)
                except ValidationFailure as exc:
                    forms[errors_key] = determine_errors(exc)
                    form.determine_autofocus()
                else:
                    return success(context, request, validated)

            return func(context, request, forms=forms)
        return wrapper
    return deco


class CommentForm(CSRFSchema):
    comment = c.SchemaNode(
        c.String(), description="Share your thoughts \u2026",
        widget=w.TextAreaWidget(css_class='comment-entry'))
