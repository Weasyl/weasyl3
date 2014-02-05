from pyramid.security import Allow, Deny, Everyone, Authenticated


class Root:
    __acl__ = [
        (Deny, Authenticated, 'signin'),
        (Allow, Everyone, 'signin'),
        (Allow, Authenticated, 'signout'),
        (Deny, Everyone, 'signout'),
    ]

    def __init__(self, request):
        self.request = request
