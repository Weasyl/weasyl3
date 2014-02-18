class APIPredicate:
    def __init__(self, val, config):
        self.must_be_api = val in {'true', 'yes'}

    def text(self):
        return 'api = %s' % (self.must_be_api,)

    phash = text

    def __call__(self, context, request):
        return request.is_api_request == self.must_be_api
