from setuptools import setup, find_packages
from pip.req import parse_requirements


reqs = [str(ir.req) for ir in parse_requirements('etc/requirements.txt')]


setup(
    name='weasyl',
    packages=find_packages(),
    package_data={
        'weasyl': [
            'static/*/*', 'templates/*.jinja2', 'templates/*/*.jinja2',
            'widgets/*.jinja2',
        ],
    },
    setup_requires=['vcversioner'],
    vcversioner={
        'version_module_paths': ['weasyl/_version.py'],
    },
    install_requires=reqs,
    entry_points={
        'paste.app_factory': [
            'main=weasyl.wsgi:make_app',
        ],
        'paste.filter_app_factory': [
            'sentry=weasyl.middleware:SentryMiddleware',
        ],
    },
)
