import logging

import colander as c
import deform.widget as w
import deform
from pyramid_deform import CSRFSchema
from pyramid.view import view_config
from pyramid import httpexceptions

from libweasyl.exceptions import ExpectedWeasylError
from libweasyl.models.content import Submission
from libweasyl.security import generate_key
from ..resources import ShareResource
from . import forms


log = logging.getLogger(__name__)


def maybe_read(appstruct, key):
    info = appstruct[key]
    if info is None:
        return None
    return info['fp'].read()


class BaseShareForm(CSRFSchema):
    thumbnail = c.SchemaNode(deform.FileData(), description='Thumbnail', missing=None, widget=forms.upload_widget)
    title = c.SchemaNode(c.String(), description='Title')
    folder = c.SchemaNode(forms.Folder(), description='Folder', widget=forms.folder_widget)
    rating = c.SchemaNode(forms.Rating(), description='Rating', widget=forms.rating_widget)
    description = c.SchemaNode(c.String(), description='Description', widget=w.TextAreaWidget())
    tags = c.SchemaNode(c.String(), description='Tags')
    category = None


@view_config(context=ShareResource, renderer='sharing/share.jinja2')
class BaseShareView(forms.FormView):
    schema = BaseShareForm()
    buttons = ['post']

    def post_success(self, appstruct):
        log.debug('share %s success: %r', self.schema.category, appstruct)
        return httpexceptions.HTTPSeeOther(appstruct['submission_obj'].canonical_path(self.request))

    def extra_fields(self):
        fields = {'category': self.schema.category}
        if 'ajax' in self.request.GET:
            fields['ajax'] = True
        return fields


class ShareVisualForm(BaseShareForm):
    submission = c.SchemaNode(deform.FileData(), description='Submission file', widget=forms.upload_widget)
    subcategory = c.SchemaNode(forms.Subcategory(), description='Subcategory', widget=forms.subcategory_widget(1))
    category = 'visual'

    def validator(self, form, values):
        request = form.bindings['request']
        try:
            sub = Submission.create(
                submission_data=values['submission']['fp'].read(), thumbnail_data=maybe_read(values, 'thumbnail'),
                owner=request.current_user, title=values['title'], rating=values['rating'],
                description=values['description'], category='visual', subtype=values['subcategory'].value,
                folder=values['folder'], tags=values['tags'].split())
        except ExpectedWeasylError as e:
            raise c.Invalid(form, e.args[0]) from e
        values['submission_obj'] = sub


@view_config(name='visual', context=ShareResource, renderer='sharing/share_form.jinja2')
class ShareVisualView(BaseShareView):
    schema = ShareVisualForm()


class ShareCharacterForm(BaseShareForm):
    submission = c.SchemaNode(deform.FileData(), description='Submission file', widget=forms.upload_widget)
    title = c.SchemaNode(c.String(), description='Name')
    age = c.SchemaNode(c.String(), description='Age')
    gender = c.SchemaNode(c.String(), description='Gender')
    height = c.SchemaNode(c.String(), description='Height')
    weight = c.SchemaNode(c.String(), description='Weight')
    species = c.SchemaNode(c.String(), description='Species')
    category = 'character'


@view_config(name='character', context=ShareResource, renderer='sharing/share_form.jinja2')
class ShareCharacterView(BaseShareView):
    schema = ShareCharacterForm()


class ShareJournalForm(CSRFSchema):
    """
    Journal is a bit weird in that it doesnt have a lot of the fields
    that are in every other form type, so it doesn't inherit from BaseShareForm
    """
    title = c.SchemaNode(c.String(), description='Title')
    content = c.SchemaNode(c.String(), description='Content', widget=w.TextAreaWidget())
    rating = c.SchemaNode(forms.Rating(), description='Rating', widget=forms.rating_widget)
    tags = c.SchemaNode(c.String(), description='Tags')
    category = 'journal'


@view_config(name='journal', context=ShareResource, renderer='sharing/share_form.jinja2')
class ShareJournalView(BaseShareView):
    schema = ShareJournalForm()


class BaseShareLiteraryMultimediaForm(BaseShareForm):
    submission = c.SchemaNode(
        deform.FileData(), description='Submission file', missing=None, widget=forms.upload_widget)
    cover = c.SchemaNode(deform.FileData(), description='Cover image', missing=None, widget=forms.upload_widget)
    embed_link = c.SchemaNode(c.String(), description='Embed link', missing=None)
    category = None

    def validator(self, form, values):
        request = form.bindings['request']
        try:
            sub = Submission.create(
                submission_data=maybe_read(values, 'submission'), thumbnail_data=maybe_read(values, 'thumbnail'),
                cover_data=maybe_read(values, 'cover'), embed_link=values['embed_link'], owner=request.current_user,
                title=values['title'], rating=values['rating'], description=values['description'],
                category=self.category, subtype=values['subcategory'].value, folder=values['folder'],
                tags=values['tags'].split())
        except ExpectedWeasylError as e:
            raise c.Invalid(form, e.args[0]) from e
        values['submission_obj'] = sub


class ShareLiteraryForm(BaseShareLiteraryMultimediaForm):
    subcategory = c.SchemaNode(forms.Subcategory(), description='Subcategory', widget=forms.subcategory_widget(2))
    category = 'literary'


@view_config(name='literary', context=ShareResource, renderer='sharing/share_form.jinja2')
class ShareLiteraryView(BaseShareView):
    schema = ShareLiteraryForm()


class ShareMultimediaForm(BaseShareLiteraryMultimediaForm):
    subcategory = c.SchemaNode(forms.Subcategory(), description='Subcategory', widget=forms.subcategory_widget(3))
    category = 'multimedia'


@view_config(name='multimedia', context=ShareResource, renderer='sharing/share_form.jinja2')
class ShareMultimediaView(BaseShareView):
    schema = ShareMultimediaForm()


@view_config(name='upload', context=ShareResource, renderer='json', request_method='PUT')
def upload_file(request):
    store = forms.DiskFileUploadTempStore(request)
    key = generate_key(16)
    body = request.body_file_seekable
    data = {
        'fp': body,
        'filename': request.GET.get('name'),
        'mimetype': request.GET.get('type'),
        'size': request.content_length,
        'uid': key,
    }
    store[key] = data
    return {'uid': key}
