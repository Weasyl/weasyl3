import logging

import colander as c
import deform.widget as w
import deform
from pyramid_deform import CSRFSchema
from pyramid.view import view_config
from pyramid import httpexceptions

from libweasyl.exceptions import ExpectedWeasylError
from libweasyl.models.content import Submission
from ..resources import ShareResource
from . import forms


log = logging.getLogger(__name__)


def maybe_read(appstruct, key):
    info = appstruct[key]
    if info is None:
        return None
    return info['fp'].read()


class ShareVisualForm(CSRFSchema):
    submission = c.SchemaNode(deform.FileData(), description='Submission file', widget=forms.upload_widget)
    thumbnail = c.SchemaNode(deform.FileData(), description='Thumbnail', missing=None, widget=forms.upload_widget)
    title = c.SchemaNode(c.String(), description='Title')
    folder = c.SchemaNode(forms.Folder(), description='Folder', widget=forms.folder_widget)
    rating = c.SchemaNode(forms.Rating(), description='Rating', widget=forms.rating_widget)
    subcategory = c.SchemaNode(forms.Subcategory(), description='Subcategory', widget=forms.subcategory_widget(1))
    description = c.SchemaNode(c.String(), description='Description', widget=w.TextAreaWidget())
    tags = c.SchemaNode(c.String(), description='Tags')

    def validator(self, form, values):
        request = form.bindings['request']
        try:
            sub = Submission.create(
                submission_data=values['submission']['fp'].read(), thumbnail_data=maybe_read(values, 'thumbnail'),
                owner=request.current_user, title=values['title'], rating=values['rating'],
                description=values['description'], category='visual', subtype=values['subcategory'].id,
                folder=values['folder'], tags=values['tags'].split())
        except ExpectedWeasylError as e:
            raise c.Invalid(form, e.args[0]) from e
        values['submission'] = sub


def share_visual_success(context, request, appstruct):
    log.debug('share visual success: %r', appstruct)
    return httpexceptions.HTTPSeeOther(appstruct['submission'].canonical_path(request))


@view_config(name='visual', context=ShareResource, renderer='sharing/visual.jinja2')
@forms.form_renderer(ShareVisualForm, 'share', success=share_visual_success, button='post',
                     name='visual', context=ShareResource, renderer='sharing/visual.jinja2')
def share_visual(context, request, forms):
    return forms
