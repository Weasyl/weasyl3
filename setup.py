from distutils.command.build import build as _build
from distutils.core import Command
import subprocess

from setuptools import setup
from pip.req import parse_requirements


reqs = [str(ir.req) for ir in parse_requirements('etc/requirements.txt')]


class build_assets(Command):
    description = 'build static assets'

    user_options = []
    boolean_options = []
    help_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        subprocess.check_call(['make', 'assets'])


class build(_build):
    sub_commands = [
        ('build_assets', lambda self: True),
    ] + _build.sub_commands


setup(
    name='weasyl',
    packages=[
        'weasyl', 'weasyl.panels', 'weasyl.views',
    ],
    package_data={
        'weasyl': [
            'static/*/*', 'templates/*.jinja2', 'templates/*/*.jinja2',
            'widgets/*.jinja2', 'assets.json',
        ],
    },
    setup_requires=['vcversioner'],
    vcversioner={
        'version_module_paths': ['weasyl/_version.py'],
    },
    install_requires=reqs,
    extras_require={
        'development': [
            'coverage',
            'flake8',
            'pytest',
            'sphinxcontrib-httpdomain',
            'sphinxcontrib-zopeext',
            'sphinx',
            'testfixtures',
            'vcversioner',
            'webtest',
        ],
    },
    entry_points={
        'paste.app_factory': [
            'main=weasyl.wsgi:make_app',
        ],
        'paste.filter_app_factory': [
            'sentry=weasyl.middleware:SentryMiddleware',
        ],
    },
    cmdclass={'build': build, 'build_assets': build_assets},
)
