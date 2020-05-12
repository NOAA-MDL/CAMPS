"""Setup script for installing CAMPS"""

from setuptools import find_packages, setup
import urllib2

# ---------------------------------------------------------------------------------------- 
# Definitions
# ---------------------------------------------------------------------------------------- 
required_packages = ["python>=2.7","numpy","scipy","pandas","seaborn","PyYAML","netCDF4",
                     "pyproj","metpy","pygrib","matplotlib","basemap"]

setuptools_extra_kwargs = {
    "entry_points": {
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

# ---------------------------------------------------------------------------------------- 
# Print some information
# ---------------------------------------------------------------------------------------- 
print('Python2.7 is required to run CAMPS')
print('----------------------------------')
print('Anaconda2-5.3.1 is recommended for running CAMPS with the following additional Python packages:')
print('-- netCDF4')
print('-- pyproj')
print('-- metpy')
print('-- pygrib')
print('-- basemap')
print('-- basemap-data-hires')
print('If Anaconda2-5.3.1 is not used, the following packages are also required:')
print('-- numpy')
print('-- scipy')
print('-- pandas')
print('-- seaborn')
print('-- yaml')
print('-- matplotlib')

# ---------------------------------------------------------------------------------------- 
# Function to test internet connectivity
# ---------------------------------------------------------------------------------------- 
def check_for_internet():
    try:
        urllib2.urlopen('https://www.pypi.org',timeout=1)
        return True
    except urllib2.URLError as err:
        return False

# ---------------------------------------------------------------------------------------- 
# Try importing basemap and instantiating Basemap object that requires basemap-data-hires
# adding this to the "install requires" list does not work properly.
# ---------------------------------------------------------------------------------------- 
print("- Checking for basemap-data-hires package...")
try:
    from mpl_toolkits.basemap import Basemap
    Basemap(resolution='h')
except(ImportError):
    raise ImportError('CAMPS requires basemap-data-hires to be installed')

# ---------------------------------------------------------------------------------------- 
# Adjust the 'install_requires' key according to the status of internet connectivty. If
# there is no connectivity, then no need to try to communicate with pypi.org
# ---------------------------------------------------------------------------------------- 
if check_for_internet():
    setuptools_extra_kwargs['install_requires'] = required_packages
else:
    setuptools_extra_kwargs['install_requires'] = []

# ---------------------------------------------------------------------------------------- 
# Run the setup function
# ---------------------------------------------------------------------------------------- 
setup(
    name='camps',
    version='1.0.0',
    description='Python package for Statistical Postprocessing of Meteorlogical Data',
    long_description='Community Atmospheric Modeling Post-processing System (CAMPS)',
    maintainer='CAMPS Development Team',
    license='BSD',
    keywords=['numpy', 'netcdf', 'data', 'science', 'network', 'oceanography',
                'meteorology', 'climate'],
    classifiers=["Development Status :: 3 - Alpha",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.7",
                 "Intended Audience :: Science/Research",
                 "License :: OSI Approved",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Topic :: System :: Archiving :: Compression",
                 "Operating System :: OS Independent"],
    packages=['camps'],
    package_data={'camps': ['registry/*.yaml']},
    include_package_data=True,
    zip_safe=False,
    **setuptools_extra_kwargs)
