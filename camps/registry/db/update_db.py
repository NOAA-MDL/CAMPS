"""
Update_db.py

Reads files and adds the variables to your database

Usage:
    update_db.py [list of netcdf filenames]
"""
import logging
import sys
import os
import glob
from netCDF4 import Dataset

from ...core.reader import read
from ...core.fetch import get_id
from ...registry.db.db import get_file_info
from ...registry.db.db import insert_file_info

def update(filepath):
    """
    loops over specified netcdf files and populates the variable
    table in the database
    """

    # Loop over all provided filepaths
    file_id = get_id(filepath) #get the file_id
    if not file_id: #If there is no file_id then the file is not CAMPS compliant 
        raise ValueError('%s not CAMPS compliant, please provide a CAMPS compliant netCDF file' %(filepath))

    #query the db table "file_info" to see if file data is already in the variable table
    file_info = get_file_info(filepath,file_id) 
    if len(file_info) > 0: #if it is, return
        logging.info('file already used to populate db, skipping update_db')
        return file_id
    if len(file_info) == 0: #if it is not, add variable info to variable table
        logging.info('updating the database with netcdf file')
        insert_file_info(filepath,file_id) #add file info to file_info table
        objs = read(filepath)
        for obj in objs:
            obj.add_to_database(filepath, file_id)
        return file_id
