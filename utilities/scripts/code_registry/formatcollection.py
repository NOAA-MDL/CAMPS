#!/usr/bin/env python
"""
NAME: formatcollection.py

REQUIREMENTS: campsregistry

PURPOSE: To format registry entires for collection readable by https://codes.nws.noaa.gov/assist/

USAGE: This script takes in information about the collection/container either from a control file
       from a command line set of arguments, or interactively
 
       formatcollection.py 
       formatcollection.py [control file] [output directory for files (optional)]
       formatcollection.py collection=[collection name (ID)] registry=[full path of registry to add collection to] label=[human-readable label(name)] text=[description of the collection] status=[collection status](optional) datafile=[file with information about members to create])(optional) outdir=[output dir](optional)

       - Any entries to be included in the new collection must have 
	   variable information from a csv in the same format as that read in by formatregentry.py

       - A control text-format file for a collection has the following format:
	   line 1 = collection name (ID) (required)
	   line 2 = url of registry to contain the collection (full path) (required)
	   line 3 = label for collection (recommended; line can be left blank)
	   line 4 = human readable description of the collection (recommended; line can be left blank)
	   line 5 = status (experimental, stable, etc.) (optional; line can be left blank)
	   line 6+(optional) = file to read for initial entries OR information about any entries 
	          to be put into the collection at creation (same format as input file used for formatregentry.py)
          
       - A control csv has same format as text, only data is by column instead of by line
         and the first line is header of data: 

HISTORY:
	2019/07/31 - Stearns - first version started by Cassie.Stearns from formatregentry.py
	                     - added information read in
    2019/08/23 - Stearns - this script works for creating a subregistry that is used to contain a 
                             collection but does not populate the collection
    2019/08/26 - Stearns - EXTENSIVE CHANGES. Pulled functions into new file: campsregistry.py
                           Added call to create files for entries in collection if present
    2019/08/29 - Stearns - Added check on inputs 
	                     - Removed print statments and added logging calls		     
    2019/08/30 - Stearns - Addeed read in variables from command line
                         - Added first attempt at error handling
    2019/09/04 - Stearns - Made variable check and file write-out into functions (put in campsregistry.py)
    2019/09/05 - Stearns - Changed code to be able to handle multiple Collections at once 
    2019/09/11 - Stearns - Changed code to read control file from either text format or CSV                    
    2019/09/12 - Stearns - Changed for data are checked and added skos:notation as a possible variable
    2019/09/13 - Stearns - Added option "uri_replace=" to replace parts of uri (string replace)
    2019/09/16 - Stearns - Updated command line read name options to better be compatible with read_elements
    2019/09/18 - Stearns - Addded change members status to match collection, and forces set status if set with file-read option
    2019/09/23 - Stearns - Added CSV output and fixed bugs
    2019/10/08 - Stearns - Added references to outputs 

"""
import os
import sys
import logging

from datetime import datetime

from campsregistry import read_control_file
from campsregistry import read_elements
from campsregistry import check_collect_url
from campsregistry import set_entry_dict
from campsregistry import checkmake_output_path
from campsregistry import write_entry_ttl
from campsregistry import check_elements_startline
from campsregistry import check_collection_inputs
from campsregistry import write_collection_ttl
from campsregistry import write_collection_csv
from campsregistry import write_entry_csv
from campsregistry import check_datafile 
from campsregistry import checkdict_keynames

from campsregistry import FILEPATH_DEFAULT
from campsregistry import DATA_FILEPATH_DEFAULT

#from campsregistry import MissingInput
#from campsregistry import MissingInputFile

from campsregistry import prefix_dict_default
##
## SET PRE-DEFINED VALUES
##
## SET THE NUMBER OF LINES EXPECTED PER ENTRY FOR TEXT CONTROL FILE 
NLINEZ_CONTROL = 6

## TIMESTAMP
nowd = datetime.now().strftime('%Y%m%d%H%M%S')

## SET LOG FILE 
logdir = os.path.join(FILEPATH_DEFAULT,"logs")
checkmake_output_path(logdir)

logfile = os.path.join(logdir,''.join(['formatcollection_',nowd,'.log']))
logging.basicConfig(filename=logfile,level=logging.DEBUG)

##
## START CODE RUN
##

logging.info("STARTING RUN OF PYTHON SCRIPT formatcollection.py at {0:s}".format(nowd)) 
##
## READ IN CONTROLS AND CREATE VARIABLE LISTS FOR INCLUDED ELEMENTS
##

## INTERACTIVE 
if len(sys.argv) < 2:
    logging.info("USING INTERACTIVE MODE.") 
    collectname = raw_input("Collection name (id):")
    setRegistry = raw_input("URI of Registry to add to (full path):")
    collectlabel = raw_input("Collection label (human-readable name):")
    collectdesc = raw_input("Collection description:")
    setStatus = raw_input("Collection Status (optional):")
    collectfilez = raw_input("File of elements to start Collection with (optional):")

    out_path = raw_input("Output directory for files (optional):")    
    ##Note = in python 3 use input instead of raw_input

    logging.debug("collectname input={0:s}".format(collectname))
    logging.debug("setRegistry inout={0:s}".format(setRegistry))
    logging.debug("collectlabel input={0:s}".format(collectlabel))
    logging.debug("collectdesc input={0:s}".format(collectdesc))
    logging.debug("setStatus input={0:s}".format(setStatus))
    logging.debug("collectfilez input={0:s}".format(collectfilez))
    logging.debug("out_path input={0:s}".format(out_path))

    Controlz_all=[[collectname, setRegistry, collectlabel, collectdesc, setStatus, collectfilez]]
    controlkeyz=['collectname', 'setRegistry', 'collectlabel', 'collectdesc', 'setStatus', 'collectfilez']

## READ FROM CONTROL FILE
else:
    infilecollection = sys.argv[1]
    goodf = check_datafile(infilecollection, failcmd='continue')
    ## NOTE: 0 is a good file.
    if goodf == 0:
        controllerfile = infilecollection
        logging.info('USING COLLECTION CONTROL FILE: {0:s}'.format(infilecollection))

        startline = check_elements_startline(infilecollection)
        if startline > -1:
            (listK, Controlz_all) = read_elements(infilecollection, firstline=startline)
            logging.debug("listK={0:s}".format(listK))
            controlkeyz = checkdict_keynames(listK) 
            logging.debug("controlkeyz={0:s}".format(controlkeyz))
        else: 
            ## TEXT CN FILE READ    
            Controlz_all = read_control_file(infilecollection, nlinezc=NLINEZ_CONTROL)
            controlkeyz=['collectname', 'setRegistry', 'collectlabel', 'collectdesc', 'setStatus', 'collectfilez']
            
        if len(sys.argv) > 2:
            argvin = sys.argv[1:]
            for ar in argvin:
                arsplit = ar.split("=")      
                if arsplit[0] == "outdir" or arsplit[0] == "out_dir":
                    out_path = arsplit[1]
                elif arsplit[0] == "uri_replace":
        		    uriz = arsplit[1].split(",")
        		    uri_old = uriz[0]
          		    uri_new = uriz[1]
                elif arsplit[0] == "log":
		            masterlog = arsplit[1]
                elif arsplit[0] == "status":
                    force_status = arsplit[1].title()

## GET FROM COMMAND LINE
    else:
        logging.info("READING FROM COMMAND LINE")
        listK = []
        listV = []
        listV.append([])
        argvin = sys.argv[1:]
        for ar in argvin:
            arsplit = ar.split("=")
            listK.append(arsplit[0])
            listV[0].append(arsplit[1])
        argz = dict(zip(listK,listV[0]))
    
        logging.debug("argz={0:s}".format(argz))
    
        if 'collection' in argz.keys():
            collectname = argz['collection']
        elif 'idset' in argz.keys():
            collectname = argz['id']
        else:
            collectname = ''
            
        if 'registry' in argz.keys():
        	setRegistry = argz['registry']
        else:
            setRegistry = ''
            
        if 'label' in argz.keys():	
            collectlabel = argz['label']
        elif 'huread' in argz.keys():
            collectlabel = argz['huread']
        else:
    	    collectlabel = ''
            
        if 'text' in argz.keys():
            collectdesc = argz['text']
        elif 'desctxt' in argz.keys():
            collectdesc = argz['desctxt']
        else:
    	    collectdesc = ''
            
        if 'status' in argz.keys():
            setStatus = argz['status'].title()
        else: 
    	    setStatus = ''
            
        if 'refs' in argz.keys():
            collectRefs = argz['refs']
        else:
            collectRefs = ''
            
        if 'datafile' in argz.keys():
            collectfilez = argz['datafile']
        else:
            collectfilez = ''
    
        if 'outdir' in argz.keys():
            out_path = argz['outdir']

        if 'uri_replace' in argz.keys():
            uriz = argz['uri_replace'].split(",")
            uri_old = uriz[0]
            uri_new = uriz[1]

    	if 'log' in argz.keys():
    	    masterlog = argz['log']

        if 'skosnote' in argz.keys():
            skosnote = argz['skosnote']
        else:
            skosnote = ''

            
        Controlz_all=[[collectname, setRegistry, collectlabel, collectdesc, setStatus, skosnote, collectRefs, collectfilez]]
        controlkeyz=['collectname', 'setRegistry', 'collectlabel', 'collectdesc', 'setStatus', 'skosnote','refs','collectfilez']

logging.info("COLLECTION INFORMATION READ.")

## CHECK THE COLLECTION INPUTS
logging.debug("Controlz_all={0:s}".format(Controlz_all))

## SET THE OUTPUT DIRECTORY
try:
    out_path
except:
    output_path =  DATA_FILEPATH_DEFAULT
else:    
    if not out_path:
        output_path = DATA_FILEPATH_DEFAULT
    else:	
	    output_path = out_path
        
logging.info("Setting data output path to: {0:s}".format(output_path))
checkmake_output_path(output_path)        
        
## SET FILENAME FOR MULTI-COLLECTION CONTAINTER DATA FILE (OPTIONAL)
try: controllerfile
except: pass
else:   
    intercollectname = os.path.basename(controllerfile)
    multicollect = os.path.splitext(intercollectname)[0]
    multi_container_ttl = os.path.join(output_path,''.join([multicollect,'_multi_container.ttl']))
    multi_container_csv = os.path.join(output_path,''.join([multicollect,'_multi_container.csv']))
    logging.info("multi_container_ttl={0:s}".format(multi_container_ttl))
    logging.info("multi_container_csv={0:s}".format(multi_container_csv))

## CREATE OUTPUT DATA FILES 
for ncf, Controlz in enumerate(Controlz_all):

    Controlz_dict = dict(zip(controlkeyz, Controlz))
    logging.debug('Controlz={0:s}'.format(Controlz))

    if ( 'collectfilez' not in Controlz_dict.keys() ) or ( not Controlz_dict['collectfilez'] ):
        has_members = False
    else:
        collectfilez = Controlz_dict['collectfilez']
        has_members = True
    
    (collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, err) = check_collection_inputs(Controlz_dict)
    if err != 0:
        logging.error("ERROR: Needed Input for collection name or registry not input. NO ENTRY CREATED")
        continue 
    
    ## SET STATUS IF OVERRIDE
    try: force_status
    except: 
        pass
    else:
        setStatus = force_status
        logging.info("Setting status={0:s}".format(setStatus))

    ## REPLACE URI IF OPTION IS SET 
    try: uri_new
    except: pass
    else:
        setRegistry = setRegistry.replace(uri_old, uri_new)
        logging.info("ATTENTION: replacing uri paths. OLD={0:s}, NEW={1:s}".format(uri_old, uri_new))
   
    logging.info("collectname={0:s}".format(collectname))
    logging.info("setRegistry={0:s}".format(setRegistry))
    logging.info("collectlabel={0:s}".format(collectlabel))
    logging.info("collectdesc={0:s}".format(collectdesc))
    logging.info("setStatus={0:s}".format(setStatus))
    logging.info("skosNote={0:s}".format(skosNote))
    logging.info("collectRefs={0:s}".format(collectRefs))
    if has_members:
        logging.info("collectfilez={0:s}".format(collectfilez))
    else:
        logging.info("No file for collection entries set.")

    
    ## SET ARRAY OF DICTIONARIES FOR COLLECTION MEMBERS AND SET MATCHING SUBDIR FOR MEMBERS IN COLLECTION 
    if has_members:
        collect_fullpath = '/'.join([setRegistry,collectname])
        startline = check_elements_startline(collectfilez)
        if startline > -1:
            (setK, setV) = read_elements(collectfilez, firstline=startline)
            vardict_all0 = set_entry_dict(setK, setV)
            vardict_all = []
            for entri,x in enumerate(vardict_all0):
    	        vardictx = check_collect_url(x,collect_fullpath)
    	        vardict_all.append(vardictx)
        else: 
            logging.error("ERROR: no good identifier line found in input file {0:s}".format(collectfilez))
            
    ##
    ## WRITE OUT .ttl FORMAT COLLECTION CONTAINER FILE
    ##
    outfilettl = os.path.join(output_path,''.join([collectname,'_container.ttl']))
    
    if has_members:
        write_collection_ttl(outfilettl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, member_vardict=vardict_all)
        logging.info("COMPLETED COLLECTION FILE: {0:s}".format(outfilettl))
        
        out_entries_file = os.path.join(output_path,''.join([collectname,'_entries.ttl']))       
        write_entry_ttl(vardict_all, prefix_dict_default, out_entries_file, force_status=setStatus)
        
        out_entries_file_csv = os.path.join(output_path,''.join([collectname,'_entries.csv']))        
        write_entry_csv(vardict_all, prefix_dict_default, out_entries_file_csv, force_status=setStatus)
                
        logging.info("COMPLETED ENTRIES FILE: {0:s}".format(out_entries_file))
        
        try: multi_container_ttl
        except: pass
        else:
            if ncf == 0:
                write_collection_ttl(multi_container_ttl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, member_vardict=vardict_all, mode='new')
            else:
                write_collection_ttl(multi_container_ttl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, member_vardict=vardict_all, mode='append')
        
    else:
        write_collection_ttl(outfilettl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs)
        logging.info("COMPLETED COLLECTION FILE: {0:s}".format(outfilettl))
        
        try: multi_container_ttl
        except: pass
        else:
            if ncf == 0:
                write_collection_ttl(multi_container_ttl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, mode='new')
            else:
                write_collection_ttl(multi_container_ttl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, mode='append')
        
        
    ## CSV DOESNT HAVE MEMBERS FOR NOW
    outfilecsv = os.path.join(output_path,''.join([collectname,'_container.csv']))
    write_collection_csv(outfilecsv, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs)
    
    try: multi_container_csv
    except: pass
    else:
        if ncf == 0:
            write_collection_csv(multi_container_csv, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, mode='new')
        else:
            write_collection_csv(multi_container_csv, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, mode='append')
            
    logging.info("RUN COMPLETE FOR CONTROL GROUP")
 
logging.info("CODE formatcollection.py COMPLETED.")

## IF MASTER LOG FILE INDICATED COPY CONTENTS OF LOG INTO MASTER FILE
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

