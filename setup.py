"""setup.py for core library"""

from setuptools import setup

__version__ = '1.0.0'

setup(
    name='robinhood-python',
    author='Matt Strum',
    url='https://github.com/mstrum/robinhood-python',
    version=__version__,
    license='Apache',
    keywords='Trade API for Robinhood',
    packages=['robinhood'],
    package_data={
        'robinhood': ['certs/*']
    },
    install_requires=[
        'requests >= 2.18.4',
        'python-dateutil >= 2.6.1',
        'pytz >= 2018.3'
    ],
    extras_require={
        'dev': [
            'flake8 >= 3.5.0'
        ]
    }
)
