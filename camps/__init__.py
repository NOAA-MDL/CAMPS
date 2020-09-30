import logging
import os
import shutil
import pkg_resources
import glob

from .version import version as __version__
from .core.reader import read

# Init a basic logger in case a module isn't run from a driver
logging.getLogger('').handlers = []
level = logging.getLevelName('INFO')
logging.basicConfig(level=level)

# Create .camps/ directory in user's home directory
user_home = os.path.expanduser('~')
camps_user_dir = user_home+'/.camps'
if not os.path.isdir(camps_user_dir):
    os.mkdir(camps_user_dir)

# Create directory in .camps to hold control file templates
camps_control_dir = camps_user_dir+'/control/'
if not os.path.isdir(camps_control_dir):
    os.mkdir(camps_control_dir)

# Put CAMPS controlfile templates into the .camps/control directory
#--------------------------------------------------------------------
resource_package = __name__
resource_path = pkg_resources.resource_filename(resource_package,'registry/')
file_list = glob.glob(resource_path+'*.yaml') + glob.glob(resource_path+'*.tbl') + glob.glob(resource_path+'*.lst')
[shutil.copy(f,camps_control_dir) for f in file_list if not os.path.isfile(camps_control_dir+os.path.basename(f))]

__all__ = ['__version__','read']
