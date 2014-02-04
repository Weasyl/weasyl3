import re


def slug_for(title):
    title = title.replace("&", " and ")
    return "-".join(m.group(0) for m in re.finditer(r"[a-z0-9]+", title.lower()))
