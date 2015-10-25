import subprocess

from pyramid.events import BeforeRender
from pyramid.events import subscriber

CURRENT_SHA = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()


@subscriber(BeforeRender)
def add_global(event):
    """
    Hooks the before-render event to inject
    application-global variables into all
    templates before they are rendered
    """	
    event['SHA'] = CURRENT_SHA

