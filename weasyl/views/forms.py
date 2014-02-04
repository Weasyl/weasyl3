from pyramid_deform import FormView as _FormView


class FormView(_FormView):
    def failure(self, exc):
        print(list(exc.error.paths()))
        return {'form': exc.field}

    def show(self, form):
        return {'form': form}
