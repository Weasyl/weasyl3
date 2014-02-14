from html.parser import locatestarttagend
import re

from jinja2 import Markup
import misaka


def slug_for(title):
    title = title.replace("&", " and ")
    return "-".join(m.group(0) for m in re.finditer(r"[a-z0-9]+", title.lower()))


def relative_date(d):
    # DON’T use kwargs here. MarkupSafe won’t escape them.
    # What’s that, you say? There are no angle brackets in formatted dates?
    return Markup('<time datetime="{}" title="{} at {} UTC">{}</time>').format(
        d.isoformat(),
        d.format('MMMM D, YYYY'),
        d.format('h:mm:ss A'),
        d.humanize(),
    )


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
