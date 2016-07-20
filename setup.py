try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Weather Information Statisitical Post-Processing System',
    'author': 'Meteorological Development Laboratory',
    'url': 'http://www.vlab.noaa.gov',
    'download_url': 'http://www.vlab.noaa.gov',
    'author_email': 'N/A',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['NAME'],
    'scripts': ['bin/wisps.py'],
    'name': 'WISPS'
}

setup(**config)
