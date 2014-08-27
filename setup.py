from setuptools import setup

setup(
    name='weasyl',
    setup_requires=['vcversioner'],
    vcversioner={
        'version_module_paths': ['weasyl/_version.py'],
    },
    entry_points={
        'paste.app_factory': [
            'main=weasyl.wsgi:make_app',
        ],
        'paste.filter_app_factory': [
            'sentry=weasyl.middleware:SentryMiddleware',
        ],
    },
)
