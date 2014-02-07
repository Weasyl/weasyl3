import colander as c
from pyramid_deform import FormView as _FormView

from ..legacy import login_name
from ..models.users import Login


class FormView(_FormView):
    def failure(self, exc):
        print(list(exc.error.paths()))
        return {'form': exc.field}

    def show(self, form):
        return {'form': form}


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
            raise c.Invalid(node, '%r is not a valid username' % (cstruct,))
        return user
