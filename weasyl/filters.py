from jinja2 import Markup
from pyramid.threadlocal import get_current_request

from libweasyl.text import markdown


def asset_path_filter(asset):
    request = get_current_request()
    return request.asset_path(asset)


def markdown_filter(target):
    return Markup(markdown(target))


def relative_date(d):
    return Markup('<time datetime="{iso}" title="{date} at {time} UTC">{relative}</time>').format(
        iso=d.isoformat(),
        date=d.format('MMMM D, YYYY'),
        time=d.format('h:mm:ss A'),
        relative=d.humanize(),
    )
