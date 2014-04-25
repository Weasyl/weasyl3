from jinja2 import Markup

from libweasyl.text import markdown


def markdown_filter(target):
    return Markup(markdown(target))


def relative_date(d):
    # DON’T use kwargs here. MarkupSafe won’t escape them.
    # What’s that, you say? There are no angle brackets in formatted dates?
    return Markup('<time datetime="{}" title="{} at {} UTC">{}</time>').format(
        d.isoformat(),
        d.format('MMMM D, YYYY'),
        d.format('h:mm:ss A'),
        d.humanize(),
    )
