#!/usr/bin/env python
"""
    NAME: formatregentry.py
    
    REQUIREMENTS: campsregistry

    PURPOSE: To format registry entires into .ttl, .csv, or .json readable by
    https://codes.nws.noaa.gov/assist/

    USAGE (3 ways):
    formatregentry.py  
    formatregentry.py [file with entry data] [ADDITIONAL VARIABLES]
    formatregentry.py outname=[output file name] out_path=[output path] ID=[reg entry id/name] label=[human-readable label/name] ... etc.

    HISTORY:
	2019/06/26 - Stearns - first version started by Cassie.Stearns
        2019/07/08 - Stearns - removed unneeded entries per advice of Alex Coley (Epimorphics) and Mark Hedley (UK Met Office)
                             - updated so that base uri is optional: if it is left intentionally blank registry will have relative url; if base uri is missing, it will be set to default.
                             - addded optional submission status with check to accept only Submitted,Stable, or Experimental; made sure format is correct for entry no matter input format (ie, uppercase etc.)
                             - changed order of read in arguments to check for mode: blank=read in; single arg=file; two plus args=read from command line
                             - updated read in from command line to assign from the format key=value (where = is a splitting character)
        2019/07/10 - Stearns - updated code to be able to handle muliple entries
                             - added check for duplicate keys in data dictionary : fatal error if found
                             - added output .csv file
        2019/08/23 - Stearns - added in entry for output file name, and added ouput directory
        2019/08/26 - Stearns - EXTENSIVE CHANGES. Made output file writing, and dictionary creation into functions and moved the functions to new file: campsregistry.py
        2019/08/28 - Stearns - added outoput path to inputs (optional), and cleaned up code 
        2019/08/29 - Stearns - removed print statements and added logs
	                     - fixed a bug with setting output dir
        2019/08/30 - Stearns - added first attempt at error handling
        2019/09/03 - Stearns - changed how file input for data is handled
        2019/09/12 - Stearns - updated default output name of file to either id (for command line/interactive) or the base file name (for file read)
                             - commented out the .csv and .json outputs because we use .ttl elsewhere (want to keep for option because formats still do work)
        2019/09/13 - Stearns - Added option "uri_replace=" to replace part of uri (string replace)
        2019/09/18 - Stearns - Added forcing of status if status is set as extra in file-read mode 
        2019/09/23 - Stearns - Re-added CSV and JSON output and fixed bugs, updated default output file path
        2019/10/17 - Stearns - Made output split into multiple files if input file has multiple dir paths in it
    
"""
import os
import sys
import logging

from datetime import datetime

from campsregistry import set_entry_dict
from campsregistry import checkmake_output_path
from campsregistry import write_entry_ttl
from campsregistry import write_entry_csv
from campsregistry import write_entry_json
from campsregistry import check_elements_startline
from campsregistry import read_elements
from campsregistry import correct_dict
from campsregistry import check_datafile
from campsregistry import divide_nestdict_by_key
#from campsregistry import get_path_depth

from campsregistry import FILEPATH_DEFAULT
from campsregistry import DATA_FILEPATH_DEFAULT
#from campsregistry import OUR_REGISTRY

from campsregistry import MissingInput
#from campsregistry import MissingInputFile

from campsregistry import prefix_dict_default
##
## SET PRE-DEFINED VALUES

## TIMESTAMP
nowd = datetime.now().strftime('%Y%m%d%H%M%S')

## SET LOG FILE
logdir = os.path.join(FILEPATH_DEFAULT,"logs")
checkmake_output_path(logdir)

logfile = os.path.join(logdir,''.join(['formatregentry_',nowd,'.log']))
logging.basicConfig(filename=logfile,level=logging.DEBUG)

##
## START CODE RUN
##

logging.info("STARTING RUN OF PYTHON SCRIPT formatregentry.py at {0:s}".format(nowd)) 

##
## GET THE NEEDED VARIABLES AND PRINT BACK INFO
##
le = len(sys.argv)

if le < 2:
## READ FROM COMMAND LINE IF NO ARGS
  logging.info("Getting inputs interactively....")
  listK = ['idset','huread','desctxt','reg_base']
  listV = []
  listV.append([])
  outname = raw_input("output file name (no extension):")
  out_path = raw_input("output path (optional):")
  idname = raw_input("entry ID:")
  listV[0].append(idname)
  listV[0].append(raw_input("human-readable label (entry name):"))
  listV[0].append(raw_input("description text:"))
  listV[0].append(raw_input("registry path (optional):"))
  
  force_statusxin = raw_input("set status:")
  if not force_statusxin:
      pass
  else:
      force_statusx = force_statusxin.title()
      
##Note = in python 3 use input instead of raw_input

else:
## READ IN CONTROL FILE AND CREATE VARIABLE LISTS IF CONTROL FILE PRESENT IN FIRST ARG
  logging.info("Reading information from control file")
  infile = sys.argv[1]
  goodf = check_datafile(infile, failcmd='continue')
  
  if goodf == 0:

    idname = os.path.splitext(infile)[0] 

    if le > 2:
        argvin = sys.argv[1:] 
        for ar in argvin:
            arsplit = ar.split("=")
            if arsplit[0] == "outname":
                outname = arsplit[1]
            elif arsplit[0] == "out_dir" or arsplit[0] == "outdir" :
                out_path = arsplit[1]
            elif arsplit[0] == "uri_replace":
                uriz = arsplit[1].split(",")
                uri_old = uriz[0]
                uri_new = uriz[1]
            elif arsplit[0] == "log":
                masterlog = arsplit[1]
            elif arsplit[0] == "status":
                force_statusx = arsplit[1].title()
        
    startline = check_elements_startline(infile)
    if startline > -1:
        (listK, listV) = read_elements(infile, firstline=startline)
    else: 
        logging.error("ERROR: no good identifier line found in input file {0:s}".format(infile))
        raise MissingInput('startline')

  else:
  ## READ IN DATA FROM COMMAND LINE IF FIRST ARGUMENT NOT CONTROL FILE
    logging.info("using command-line inputs")
    listK = []
    listV = []
    listV.append([])
    argvin = sys.argv[1:]
    for ar in argvin:
        arsplit = ar.split("=")
        if arsplit[0] == "outname":
            outname = arsplit[1]
        elif arsplit[0] == "out_dir" or arsplit[0] == "outdir" :
            out_path = arsplit[1]
        elif arsplit[0] == "uri_replace":
            uriz = arsplit[1].split(",")
            uri_old = uriz[0]
            uri_new = uriz[1]
        elif arsplit[0] == "log":
            masterlog = arsplit[1]	    
        else:    
            listK.append(arsplit[0])
            listV[0].append(arsplit[1])

## SET OUPUT DIRECTORY 
try:
    out_path
except:    
    output_path = DATA_FILEPATH_DEFAULT
else:
    if not out_path:
        output_path = DATA_FILEPATH_DEFAULT
    else:
        output_path = out_path
    
checkmake_output_path(output_path)

##
## CREATE THE DATA DICTIONARY ARRAY
##

vardict_all0 = set_entry_dict(listK, listV)

## CORRECT THE URI IF THE OPTION IS SET
try: uri_new
except: pass
else:
    logging.info("Changing URI. Replacing path OLD={0:s} with NEW={1:s}".format(uri_old, uri_new))	
    vardict_all = correct_dict(vardict_all0, ['reg_base','fullidset','reg_base_path'], uri_old, uri_new)
    
## SET OUTPUT NAME TO DEFUALT IF NOT SET
try: outname
except NameError: 
    try: idname	
    except NameError:
        outname = ''.join([vardict_all0[0]['idset'],'_regdata'])	
    else:
        outname = ''.join([idname,'_regdata'])

outname_base = os.path.basename(outname)
logging.info("outname = {0:s}".format(outname))

# CHECK AND SPLIT BY PATH IF MULTIPLE PATHS PRESENT
num_paths, vardict_all_out = divide_nestdict_by_key(vardict_all0, 'reg_base')

##
## WRITE OUT FILES (MULTIPLE FORMATS)
##
for ncf, vardict_all in enumerate(vardict_all_out):
    
    if num_paths > 1:
        splitname = os.path.basename(vardict_all[0]['reg_base'])
        
        outnamettl = '.'.join([outname_base,splitname,'ttl']) 
        outfilettl = os.path.join(output_path,outnamettl)
        logging.info("outfilettl={0:s}".format(outfilettl)) 
        
        outnamecsv = '.'.join([outname_base,splitname,'csv'])
        outfilecsv = os.path.join(output_path,outnamecsv)
        logging.info("outfilecsv={0:s}".format(outfilecsv))
        
        outnamejson = '.'.join([outname_base,splitname,'json']) 
        outfilejson = os.path.join(output_path,outnamejson)
        logging.info("outfilejson={0:s}".format(outfilejson))
    else:
        outnamettl = '.'.join([outname_base,'ttl']) 
        outfilettl = os.path.join(output_path,outnamettl)
        logging.info("outfilettl={0:s}".format(outfilettl)) 
        
        outnamecsv = '.'.join([outname_base,'csv'])
        outfilecsv = os.path.join(output_path,outnamecsv)
        logging.info("outfilecsv={0:s}".format(outfilecsv))
        
        outnamejson = '.'.join([outname_base,'json']) 
        outfilejson = os.path.join(output_path,outnamejson)
        logging.info("outfilejson={0:s}".format(outfilejson))
       
    try: force_statusx
    except: 
        write_entry_ttl(vardict_all, prefix_dict_default, outfilettl)
        write_entry_csv(vardict_all, prefix_dict_default, outfilecsv)
        write_entry_json(vardict_all, prefix_dict_default, outfilejson)   
    else:
        write_entry_ttl(vardict_all, prefix_dict_default, outfilettl, force_status=force_statusx)
        write_entry_csv(vardict_all, prefix_dict_default, outfilecsv, force_status=force_statusx)
        write_entry_json(vardict_all, prefix_dict_default, outfilejson, force_status=force_statusx)
        
    logging.info("COMPLETED ENTRY FILE: {0:s}".format(outfilettl))
    
    ## FINISH AND CLOSE
    logging.info("CODE formatregentry.py COMPLETED.")

##
## COPY LOG TO MASTER LOG IF INDICATED
##    
try: masterlog
except: pass
else:
    fin = open(logfile, "r")  
    logdata = fin.read()
    fin.close()
    fout = open(masterlog, "a")
    fout.write(logdata)
    fout.close()

exit()
