from setuptools import setup
import os

__version__ = '1.1.9'

markdown_contents = open(os.path.join(os.path.dirname(__file__),
                                      'README.md')).read()

console_scripts = ['deploy-agent = deployd.agent:main',
                   'deploy-downloader = deployd.download.downloader:main',
                   'deploy-stager = deployd.staging.stager:main']

install_requires = [
    "requests>=2.5.1",
    "gevent==1.0.2",
    "lockfile==0.12.2",
    "boto>=2.13.3",
    "python-daemon>=2.1"
]

# Pinterest specific settings
if os.getenv("IS_PINTEREST", "false") == "true":
    extra_requires = [
        "pinlogger>=0.11.0",
        "pinstatsd==1.0.55",
    ]
    install_requires += extra_requires

setup(
    name='deploy-agent',
    version=__version__,
    scripts=['bin/{}'.format(p) for p in os.listdir('bin')],
    long_description=markdown_contents,
    entry_points={
        'console_scripts': console_scripts,
    },
    install_requires=install_requires,
    author="Pinterest",
    packages=[
        'deployd',
        'deployd.download',
        'deployd.common',
        'deployd.staging',
        'deployd.client',
        'deployd.types',
    ],
    include_package_data=True,
    package_data={'deployd/conf': ['*.conf']}
)
