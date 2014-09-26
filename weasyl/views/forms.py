import json
import logging
import os

import colander as c
import deform.widget as w
from deform.exception import ValidationFailure
from deform.form import Form as _Form
from pyramid_deform import FormView as _FormView, CSRFSchema
from pyramid.view import view_config
from translationstring import TranslationStringFactory

from libweasyl.files import fanout, makedirs_exist_ok
from libweasyl.legacy import login_name
from libweasyl.models.content import Folder as _Folder
from libweasyl.models.users import Login
from libweasyl import ratings
from .decorators import wraps_respecting_view_config


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


class Folder(c.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is c.null:
            return appstruct
        return str(appstruct.folderid)

    def deserialize(self, node, cstruct):
        if cstruct is c.null:
            return cstruct
        elif cstruct == '0':
            return None
        folder = _Folder.query.get(cstruct)
        if folder is None or folder.owner != node.bindings['request'].current_user:
            raise c.Invalid(node, _('"${val}" is not a valid folder', mapping=dict(val=cstruct)))
        return folder


@c.deferred
def folder_widget(node, kw):
    folders = kw['request'].current_user.folders
    values = [(0, '')]
    values.extend((str(f.folderid), f.title) for f in folders)
    return w.SelectWidget(values=values)


class Rating(c.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is c.null:
            return appstruct
        return str(appstruct.code)

    def deserialize(self, node, cstruct):
        if cstruct is c.null:
            return cstruct
        try:
            code = int(cstruct)
        except ValueError:
            raise c.Invalid(node, _('"${val}" is not a valid rating', mapping=dict(val=cstruct)))
        rating = ratings.CODE_MAP.get(code)
        if rating is None:
            raise c.Invalid(node, _('"${val}" is not a valid rating', mapping=dict(val=cstruct)))
        return rating


@c.deferred
def rating_widget(node, kw):
    age = kw['request'].current_user.info.age
    return w.SelectWidget(values=[(str(r.code), r.name_with_age) for r in ratings.get_ratings_for_age(age)])


class JSON(c.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is c.null:
            return appstruct
        return json.dumps(appstruct)

    def deserialize(self, node, cstruct):
        if cstruct is c.null:
            return cstruct
        try:
            return json.loads(cstruct)
        except ValueError as e:
            raise c.Invalid(node, _('"${val}" is not valid JSON', mapping=dict(val=cstruct))) from e


def form_renderer(schema, key, *, success, button, **kwargs):
    form_key = '_%s_form' % (key,)
    errors_key = '_%s_errors' % (key,)
    def deco(func):
        @view_config(_depth=1, request_method='POST', **kwargs)
        @wraps_respecting_view_config(func)
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
        c.String(), description="Comment", widget=w.TextAreaWidget(
            css_class='comment-entry', placeholder="Share your thoughts\u2026"))


def chunks(stream, chunk_size=8192):
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        yield chunk


_MISSING = object()


class DiskFileUploadTempStore(object):
    def __init__(self, request):
        self.tmpdir = request.registry.settings['weasyl.upload_tempdir']

    def preview_url(self, uid):
        return None

    def _fanned(self, name):
        return os.path.join(self.tmpdir, *fanout(name, (1, 1)))

    def __setitem__(self, name, data):
        data = data.copy()
        base_dir = self._fanned(name)
        log.debug('writing out file data to %r for %r (%r)', base_dir, name, data)
        makedirs_exist_ok(base_dir)
        stream = data.pop('fp', None)
        if stream is not None:
            with open(os.path.join(base_dir, name), 'wb') as outfile:
                for chunk in chunks(stream):
                    outfile.write(chunk)
            stream.seek(0)
        with open(os.path.join(base_dir, name + '.meta'), 'w') as outfile:
            json.dump(data, outfile)

    def get(self, name, default=None):
        base_dir = self._fanned(name)
        try:
            infile = open(os.path.join(base_dir, name + '.meta'))
        except OSError:
            return default
        with infile:
            data = json.load(infile)
        try:
            data['fp'] = open(os.path.join(base_dir, name), 'rb')
        except OSError:
            pass
        return data

    def __getitem__(self, name):
        ret = self.get(name, _MISSING)
        if ret is _MISSING:
            raise KeyError(name)
        return ret

    def __contains__(self, name):
        # this API kind of sucks.
        return os.path.exists(os.path.join(self._fanned(name), name + '.meta'))


@c.deferred
def upload_widget(node, kw):
    tmpstore = DiskFileUploadTempStore(kw['request'])
    return w.FileUploadWidget(tmpstore)
