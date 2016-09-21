from distutils.command.build import build as _build
from distutils.core import Command
import pip
import subprocess

from setuptools import setup
from pip.req import parse_requirements


requirements = parse_requirements('etc/requirements.txt',
                                  session=pip.download.PipSession())


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
    install_requires=[str(ir.req) for ir in requirements],
    extras_require={
        'development': [
            'coverage',
            'flake8',
            'pytest',
            'sphinxcontrib-httpdomain',
            'sphinxcontrib-zopeext',
            'sphinx',
            'testfixtures',
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
