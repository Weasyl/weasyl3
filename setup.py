from setuptools import setup

setup(
    name='weasyl',
    version='3.0',
    entry_points={
        'paste.app_factory': [
            'main=weasyl.wsgi:make_app',
        ],
        'paste.filter_app_factory': [
            'sentry=weasyl.middleware:SentryMiddleware',
        ],
    },
)
