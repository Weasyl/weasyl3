import logging

from pyramid.threadlocal import get_current_request

from libweasyl.text import slug_for


log = logging.getLogger(__name__)


def format_media_link(media, link):
    request = get_current_request()
    if link.link_type == 'submission':
        login_name = link.submission.owner.login_name
        return request.resource_path(
            None, '~' + login_name, 'submissions', str(link.submitid),
            '%s-%s-%s.%s' % (
                login_name, slug_for(link.submission.title), media.mediaid,
                media.file_type))
    else:
        return None
