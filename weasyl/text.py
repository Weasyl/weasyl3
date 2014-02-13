from html.parser import locatestarttagend
import re

from jinja2 import Markup
import misaka

from . import dates


def slug_for(title):
    title = title.replace("&", " and ")
    return "-".join(m.group(0) for m in re.finditer(r"[a-z0-9]+", title.lower()))


def relative_date(dt):
    diff = dates.now() - dt

    if diff.days:
        if diff.days >= 365:
            relative = (int(diff.days / 365.25), 'year')
        elif diff.days >= 30:
            relative = (diff.days // 30, 'month')
        else:
            relative = (diff.days, 'day')
    elif diff.seconds:
        if diff.seconds >= 3600:
            relative = (diff.seconds // 3600, 'hour')
        elif diff.seconds >= 60:
            relative = (diff.seconds // 60, 'minute')
        else:
            relative = (diff.seconds, 'second')
    else:
        return 'just now'

    (count, unit) = relative
    return Markup(
        '<time datetime="{iso}">{count} {unit}{s} {direction}</time>'.format(
            iso=dt.isoformat(),
            count=abs(count),
            unit=unit,
            s='' if count in (-1, 1) else 's',
            direction='from now' if count < 0 else 'ago'
        ))


MISAKA_EXT = (
    misaka.EXT_TABLES
    | misaka.EXT_FENCED_CODE
    | misaka.EXT_AUTOLINK
    | misaka.EXT_STRIKETHROUGH
    | misaka.EXT_LAX_SPACING)

MISAKA_FORMAT = (
    misaka.HTML_HARD_WRAP)


def strip_outer_tag(html):
    match = locatestarttagend.match(html)
    start_tag_end = match.end()
    end_tag_start = html.rindex('<')
    return html[:start_tag_end + 1], html[start_tag_end + 1:end_tag_start], html[end_tag_start:]


class MarkdownInHTMLRenderer(misaka.HtmlRenderer):
    def block_html(self, raw_html):
        if raw_html.startswith('<!--'):
            return raw_html
        start, stripped, end = strip_outer_tag(raw_html)
        return ''.join([start, _markdown(stripped), end])


def _markdown(target):
    renderer = MarkdownInHTMLRenderer(MISAKA_FORMAT)
    markdown = misaka.Markdown(renderer, MISAKA_EXT)
    return markdown.render(target)


def markdown_filter(target):
    return Markup(_markdown(target))
