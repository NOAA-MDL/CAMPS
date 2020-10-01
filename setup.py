from setuptools import find_packages, setup
import urllib.request, urllib.error, urllib.parse

# Pygrib is a dependency of CAMPS and should be installed prior to installing CAMPS
try:
    import pygrib
except(ImportError):
    raise ImportError('Pygrib is a dependency for CAMPS, please install Pygrib before attempting to install CAMPS')


# Set information about CAMPS
NAME = 'camps'
VERSION = '1.1.0'

# List required packages
required_packages = ['numpy>=1.17.3',
                     'scipy>=1.3.1',
                     'pandas>=0.23.4',
                     'seaborn>=0.9.0',
                     'PyYAML>=3.13',
                     'netCDF4>=1.4.2',
                     'pyproj>=1.9.6',
                     'metpy>=0.12.0',
                     'pygrib>=2.0.4',
                     'matplotlib>=3.1.1']

# Define console scripts
setuptools_extra_kwargs = {
    'entry_points': {
        'console_scripts': [
            'camps_mospred = camps.scripts.mospred_driver:main',
            'camps_grib2_to_nc = camps.scripts.grib2_to_nc_driver:main',
            'camps_metar_to_nc = camps.scripts.metar_driver:main',
            'camps_marine_to_nc = camps.scripts.marine_driver:main',
            'camps_equations = camps.scripts.equations_driver:main',
            'camps_forecast = camps.scripts.forecast_driver:main',
            'camps_graphs = camps.gui.graphs:main'
        ]
    },
}

# Function to check for internet connectivity
def check_for_internet():
    try:
        urllib.request.urlopen('https://www.pypi.org',timeout=1)
        return True
    except urllib.error.URLError as err:
        return False

# Function to write version.py at the top-level camps/
def write_version_py(filename='camps/version.py'):
    cnt = """
# THIS FILE IS GENERATED FROM CAMPS SETUP.PY
version = '%(version)s'
"""
    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': VERSION})
    finally:
        a.close()

# Check for internet connectivity
if check_for_internet():
    setuptools_extra_kwargs['install_requires'] = required_packages
else:
    setuptools_extra_kwargs['install_requires'] = []

# Write version py
write_version_py()

# Run the setup function
setup(
    name = NAME,
    version = VERSION,
    description = 'Python package for Statistical Postprocessing of Meteorlogical Data',
    long_description = 'Community Atmospheric Modeling Post-processing System (CAMPS)',
    maintainer = 'CAMPS Development Team',
    license = 'BSD',
    keywords = ['numpy', 'netcdf', 'data', 'science', 'network', 'oceanography',
              'meteorology', 'climate'],
    classifiers = ['Development Status :: 3 - Alpha',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Topic :: System :: Archiving :: Compression',
                 'Operating System :: OS Independent'],
    packages = ['camps'],
    package_data = {'camps': ['registry/*.yaml']},
    platforms = ['darwin','linux'],
    python_requires = '>=3.6',
    include_package_data = True,
    zip_safe = False,
    **setuptools_extra_kwargs)
