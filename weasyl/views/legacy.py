from pyramid import httpexceptions


def configure_urls(config):
    def redirect(route, *transformed):
        def forward(request):
            new_segments = [x.format(**request.matchdict) for x in transformed]
            url = request.resource_url(None, *new_segments)
            return httpexceptions.HTTPMovedPermanently(url)

        config.add_route(route, route)
        config.add_view(forward, route_name=route)

    redirect('user/{name}', '~{name}')
    redirect('profile/{name}', '~{name}')
    redirect('~{name}/submission/{id}/{title}', '~{name}', 'submissions', '{id}', '{title}')
    for segment in ['submissions', 'journals', 'collections', 'characters',
                    'shouts', 'favorites', 'friends', 'following', 'followed']:
        redirect(segment + '/{name}', '~{name}', segment)
    redirect('staffnotes/{name}', '~{name}', 'staff-notes')

    redirect('view/{id}', 'submissions', '{id}', 'view')
    redirect('submission/{id}', 'submissions', '{id}', 'view')
    redirect('character/{id}', 'characters', '{id}', 'view')
    redirect('journal/{id}', 'journals', '{id}', 'view')
