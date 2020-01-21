#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NAME: campsregistry.py

@author: Cassie.Stearns

REQUIREMENTS: NONE

PUROSE AND USAGE:
This file contains the functions needed for the creation of files and collection containers
used to update the CAMPS code registry. This is needed for the following python codes:
    formatcollection.py 
    formatregentry.py
    update_registry.py
    gen_regdata_by_node.py

HISTORY:
2019/08/26 - Stearns - Created on Mon Aug 26 10:34:47 2019
2019/08/29 - Stearns - removed print statements (mostly) and added logging instead
                     - MAJOR FIX: fixed a bug that was allowing blank IDs through into the data dictionary,
		       also updated other checks on the data dictionary function and changed how vardict_all 
		       was built (somewhat)
2019/08/30 - Stearns - Added first attempt at error handling
2019/09/03 - Stearns - Added function to check line in CSV that has variable keys and updated check on key names
2019/09/04 - Stearns - Tweaked how file reading works to get variables - changed read_elements to use QUOTE_MINIMAL 
                       instead of QUOTE_NOTE to deal with commas in fields and added checks on field numbers, and
                       cleaned quotes from printed data
                     - Added option for adding dct:references into output entry files
2019/09/05 - Stearns - Changed codes to be able to handle multiple Collections at once
2019/09/06 - Stearns - Added some codes originally in update_registry.py
2019/09/10 - Stearns - Updated how CSV data files read in to deal with missing columns 
2019/09/11 - Stearns - Added function to split CSV files by path if multiple paths
2019/09/12 - Stearns - Adjusted how Collection variables are checked and file written
                     - added skos:notation to Collections 
2019/09/13 - Stearns - Added function to replace values in a dictionary for specific keys (used for uri replace)
                     - Added function to cacluate path depth (use to determine order of builds)
2019/09/25 - Stearns - reworked path data and csv split functions - took out path functions to csv split
2019/09/27 - Stearns - Added append option to writing csv and ttl container/collection files, added function to check if
                       uri exists
2019/10/01 - Stearns - removed authenticate and uri_exists as both rely on web requests and I want these
                       in a seperate file (for now, update_registry.py)
2019/10/08 - Stearns - Added in capability to write multiple references out for both collections and concepts
2019/10/09 - Stearns - Added function to remove errant spaces from strings used to call other scripts
                     - fixed bug where if start line for file read < 0, error occurrs 
2019/10/10 - Stearns - fixed bug in get_data_paths when get_path_depth returns a depth < 2
2019/10/16 - Stearns - updated custom error classes and calls, updated check_elements_startline to not raise if missing file
2019/10/17 - Stearns - added function to split and re-nest nested dictionary by keyword                       

"""

import os
#import sys
import csv
import logging

from datetime import datetime
from itertools import islice

##
## SET MASTER VARIABLES
##
FILEPATH_DEFAULT = os.getcwd()
DATA_FILEPATH_DEFAULT = os.path.join(FILEPATH_DEFAULT,'data_gen') 

## TOP URL FOR OUR REGISTRY
OUR_REGISTRY = 'https://codes.nws.noaa.gov/assist'

## SET LIST OF ACCEPTABLE STATUS
ACCEPTED_STATUS_DEFAULT = ["None","Submitted","Stable","Experimental"]

## SETUP DICTIONARY OF PREFIXES FOR DEFAULT
prefix_dict_default = {
     "owl" : "http://www.w3.org/2002/07/owl#",
     "ssd" : "http://www.w3.org/ns/sparql-service-description#",
     "xsd" : "http://www.w3.org/2001/XMLSchema#",
     "skos" : "http://www.w3.org/2004/02/skos/core#",
     "rdfs" : "http://www.w3.org/2000/01/rdf-schema#",
     "qb" : "http://purl.org/linked-data/cube#",
     "dgu" : "http://reference.data.gov.uk/def/reference/",
     "dct" : "http://purl.org/dc/terms/",
     "ui" : "http://purl.org/linked-data/registry-ui#",
     "reg" : "http://purl.org/linked-data/registry#",
     "api" : "http://purl.org/linked-data/api/vocab#",
     "vann" : "http://purl.org/vocab/vann/",
     "prov" : "http://www.w3.org/ns/prov#",
     "foaf" : "http://xmlns.com/foaf/0.1/",
     "cc" : "http://creativecommons.org/ns#",
     "void" : "http://rdfs.org/ns/void#",
     "odrs" : "http://schema.theodi.org/odrs#",
     "org" : "http://www.w3.org/ns/org#",
     "env-ui" : "http://environment.data.gov.uk/registry/structure/ui/",
     "version" : "http://purl.org/linked-data/version#",
     "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
     "ldp" : "http://www.w3.org/ns/ldp#",
     "time" : "http://www.w3.org/2006/time#",
     "vs" : "http://www.w3.org/2003/06/sw-vocab-status/ns#",
     "dc" : "http://purl.org/dc/elements/1.1/"
}

## TIMESTAMP
nowd = datetime.now().strftime('%Y%m%d%H%M%S')

##
## SET CLASSES
##
class MissingInput(Exception):
    """Use this when there is input data needed but missing."""
    def __init__(self,miss_input=''):
        self.miss_input = miss_input
        
    def __str__(self):
        return "REQUIRED INPUT {self.miss_input} IS MISSING. EXITING.".format(self=self)

class MissingInputFile(MissingInput):
    """Use this when there is input data file needed but missing."""
    def __init__(self,miss_input=''):
        self.miss_input = miss_input
        
    def __str__(self):
        return "REQUIRED FILE {self.miss_input} IS MISSING OR UNREADABLE. EXITING.".format(self=self)    

class ItemPathObj(object):
    def __init__(self, name, depth=0, dir_path='', parent_dir='', full_path='', src_file='', src_line=-1):
        self.name = name
        self.depth = depth
        self.dir_path = dir_path
        self.full_path = full_path
        self.parent_dir = parent_dir
        self.src_file = src_file
        self.src_line = src_line
 
class CollectionObj(object):
    def __init__(self, name, depth=0, parent_dir='', dir_path='', members=[], member_rows=[], fileIn='', full_path='', fileDataOut=''):
        self.name = name
        self.depth = depth
        self.parent_dir = parent_dir
        self.dir_path = dir_path
        self.members = members
        self.member_rows = member_rows
        self.fileIn = fileIn
        self.full_path = full_path
        self.fileDataOut = fileDataOut     
        
##
## SET FUNCTIONS
##

## CHECK IF DATA FILE EXISTS AND CAN BE OPENED
def check_datafile(datafile, failcmd='raise'):
    exists = os.path.isfile(datafile)
    err = 0
    if exists:
        try:
            open(datafile,'rb')
        except:
    	    if failcmd == 'continue':
    	        err = 1
                logging.warning("WARNING: Unable to open data file {0:s}. CONTINUING.".format(datafile))
                return err
            else:
                logging.critical("ERROR: Unable to open data file {0:s}. EXITING PROGRAM.".format(datafile))
                raise MissingInputFile(datafile)
    	else:
    	    return err	    		
    else:
    	if failcmd == 'continue':
            err = 1
            logging.warning("WARNING: Unable to open data file {0:s}. CONTINUING.".format(datafile))
    	    return err
        else:
            logging.critical("ERROR: data file {0:s} does not exist. EXITING PROGRAM.".format(datafile))
            raise MissingInputFile(datafile) 
    

## CHECK IF OUTPUT PATH EXISTS, IF NOT THEN TRY TO MAKE IT 
def checkmake_output_path(output_path):
    if not os.path.exists(output_path):
        try:
            os.makedirs(output_path)
        except OSError:
	        logging.error("ERROR: Creation of the directory {0:s} failed".format(output_path))
        else:
	        logging.info("Successfully created the directory {0:s}".format(output_path))

## CHECK FILE FOR STRING AND RETURN LIST OF LINES PRESENT OR 'None' IF NOT THERE
def check_file_for_str(filein,chkstr):
    line_out_list = []
    with open(filein,'r') as f1:
        line_num = 1
        for line in f1:
            line_num += 1
            if chkstr in line:
                line_out_list.append(line_num)
    if not line_out_list:
        line_out_list = None    
    return line_out_list

## GET DUPLICATES IN LIST AND THE INDICES THEY APPEAR
## OUTPUT IS DICTIONARY OF DUPLICATE:[INDICES]
def getDuplicates(inlist):
    seen = []
    dupli = []
    dupliout = {}
    for ix,x in enumerate(inlist):
        if x in seen:
            dupli.append(x)
        else:
            seen.append(x)
    if len(dupli) > 0:
        for iy,y in enumerate(dupli):
            indices = [i for i, x in enumerate(inlist) if x == y]
            dupliout[y] = indices
    return dupliout

## READ CONTROL FILE FOR COLLECTION CREATION
## nlinezc = number of lines with expected information per entry
## break_char = special characters which will break input and go to next entry
## OUTPUTS CONTROL DATA AS ARRAY     
def read_control_file(infile, nlinezc=6, break_char='##NEW##'):
    existsC = os.path.isfile(infile)
    if existsC:
        
        collectvar_all =[]
        collectvar = []
    
        with open(infile) as fp:
            line = fp.readline()
    	    cnt = 0
            nv = -1
    	    while line:
                linex = line.strip('\n')
                logging.debug("Line {}: {}".format(cnt, linex))
                if linex == break_char or cnt == nlinezc:
                    nv = nv + 1
                    cnt = 0
                    collectvar_all.append([])
                    for item in collectvar:
                         collectvar_all[nv].append(item)
                    collectvar = []                    
                else:
                    collectvar.append(linex)
                    cnt += 1                                
                line = fp.readline()    
            
            if cnt != 0:
                collectvar_all.append([])
                nv = nv + 1
                for item in collectvar:
                    collectvar_all[nv].append(item)

        return collectvar_all
    
    else:
        logging.critical("ERROR: File for input not found! Exiting.")
        raise MissingInputFile(infile)

## FUNCTION TO TAKE A FULL-PATH ID AND EXTRACT ID/NAME AND PATH
def split_fullid(fullidset):
   fullid = fullidset.strip('<>')
   fullid = fullid.strip('"')
   fullid = fullid.strip("'")
   path_out = os.path.dirname(fullid) 
   name_out = os.path.basename(fullid)
   return (path_out, name_out)

## CHECK COLLECTION INFORMATION INPUTS 
def check_collection_inputs(ControlzDict, accepted_status=ACCEPTED_STATUS_DEFAULT):
    err = 0
    
    if ( 'collectname' not in ControlzDict.keys() ) or ( not ControlzDict['collectname'] ) :
        if ( 'fullidset' not in ControlzDict.keys() ) or ( not ControlzDict['fullidset'] ) :
            logging.error("ERROR. No Collection name (ID) input.")
            err = 1
            collectname = None
        else:
            logging.warning("WARNING: registry ID not explicitly set. Reading from full URI.")
            logging.debug('fullidset={0:s}'.format(ControlzDict['fullidset']))
            (setRegistry, collectname) = split_fullid(ControlzDict['fullidset'])
    else:
        collectname = ControlzDict['collectname']
    
    try: setRegistry
    except NameError:
    	if ( 'setRegistry' not in ControlzDict.keys() ) or ( not ControlzDict['setRegistry'] ) :
    	    logging.error("ERROR. No Registry for collection selected.")
    	    err = 2
    	    setRegistry = None
    	else:
    	    setRegistry = ControlzDict['setRegistry']
    	    if setRegistry[-1] == "/":
    		    setRegistry = setRegistry[:-1]
        
    if ( 'collectlabel' not in ControlzDict.keys() ) or ( not ControlzDict['collectlabel'] ) :
        if ( 'huread' not in ControlzDict.keys() ) or ( not ControlzDict['huread'] ) :
            logging.warning("WARNING: No Collection label input. Creating from Collection name (ID).")
            collectlabel = ControlzDict['collectname']
    	else:
    	    collectlabel = ControlzDict['huread']
    else:
        collectlabel = ControlzDict['collectlabel']
    
    if ( 'collectdesc' not in ControlzDict.keys() ) or ( not ControlzDict['collectdesc'] ) :
        if ( 'desctxt' not in ControlzDict.keys() ) or ( not ControlzDict['desctxt'] ) :
            logging.warning("WARNING: No Collection description provided. Leaving blank.")
            collectdesc = ''
	else:
	    collectdesc = ControlzDict['desctxt']
    else:
        collectdesc = ControlzDict['collectdesc']

    if ('skosnote' not in ControlzDict.keys()) or ( not ControlzDict['skosnote'] ):
        skosNote = "None"
    else:
        skosNote = ControlzDict['skosnote']

    if ('setStatus' not in ControlzDict.keys()) or ( not ControlzDict['setStatus'] ) or ( ControlzDict['setStatus'] not in ACCEPTED_STATUS_DEFAULT):
        setStatus = "None"
    else:
        setStatus = ControlzDict['setStatus']
        
    if ('refs' not in ControlzDict.keys()) or ( not ControlzDict['refs']):
        collectRefs = "None"
    else:
        collectRefs = ControlzDict['refs']

    return (collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNote, collectRefs, err)


## CHECK A FILE TO FIND THE VARIABLE ID LINE NUMBER (USED FOR KEYS IN DATA DICT)
## THIS ALLOWS FOR FILES WITH HEADER LINES TO BE USED AS CSV INPUTS
## RETURNS LINE NUMBER (FIRST LINE IN FILE=1) IF ID FOUND
## RETURNS -1 IF IDENTIFIER LINE NOT FOUND 
def check_elements_startline(infile, goodids=['id','ID','@id','@ID','idset','collection','name'], delim_set=","):

    exists = os.path.isfile(infile)
    
    if exists:      
        with open(infile, 'r') as f:
            i_good = -1            
            i = 0
            for row in islice(csv.reader(f, delimiter=delim_set, quoting=csv.QUOTE_NONE),i,None):
                i = i + 1
                itemz = []
                for item in row:
                    itemz.append(item)
                
                for idid in goodids:
                    if idid in itemz:
                        logging.info("Keys line for variables found at line= {0:s}".format(str(i)))
                        i_good = i 
                        break
                    else:
                        continue    
                
                if i_good >= 0:
                    break
                
            if i_good >= 0:
                return i_good
            else:
                logging.error("ERROR: No acceptable ID variable name found in {0:s}. returning -1.".format(infile))
                return -1
            
    else:
        logging.error("ERROR: File for input ( {0:s} ) not found! Returning -1.".format(infile))
        return -1 
        
## READ INPUT FILE FOR REGISTRY ENTRY INFORMATION FOR ENTITIES AND
## RETURN A LIST OF INFORMATION KEYS (listK) AND
## RETURN A ARRAY OF INFORMATION VALUES PER REGISTRY ENTRY (listV)         
def read_elements(infile, delim_set=",", firstline=1):
    
    exists = os.path.isfile(infile)
    
    if exists:
        with open(infile, 'r') as f:
            i = firstline - 1
            logging.info("Reading in data file {0:s} starting at line {1:s}".format(infile, str(firstline)))
            iv = -1
            listK = []
            listV = []
            for row in islice(csv.reader(f, delimiter=delim_set, quoting=csv.QUOTE_MINIMAL),i,None):
                logging.debug("row={0:s}".format(row))
                i = i + 1 
                if i == firstline:
                    catnum = -1
                    goodcolz = []
                    for item in row:
                        logging.debug("col={0:s}".format(item))
                        catnum += 1
                        item = item.strip('"')
                        item = item.strip("'")
                        if item:
                            goodcolz.append(catnum)
                            listK.append(item)
                    logging.info("Number of variables(columns) expected={0:s}".format(str(len(goodcolz))))
                    logging.debug("goodcolz={0:s}".format(goodcolz))
                elif i > firstline:
                    logging.debug("row length={0:s}".format(str((len(row)))))
                    if len(row) == len(goodcolz):
                        iv = iv + 1
                        listV.append([])
                        for item in row:
                            item = item.strip('"')
                            item = item.strip("'")
                            listV[iv].append(item)
                    elif len(row) > len(goodcolz):
                        iv = iv + 1
                        listV.append([])
                        for ncol in goodcolz:
                            logging.debug("row[{0:s}]={1:s}".format(str(ncol),row[ncol]))
                            item = row[ncol]                            
                            item = item.strip('"')
                            item = item.strip("'")
                            listV[iv].append(item)
                    else:
                        logging.error("ERROR: Number of columns in row={0:s} does not match expected number of variables. Check data source. ENTRY NOT ADDED.".format(str(i)))

        logging.info("Number of data lines in file read={0:s}".format(str(i - firstline)))
        logging.info("Number of good entries ={0:s}".format(str(len(listV))))
        return (listK, listV) 
    
    else:    	
        logging.error("ERROR: File for input ( {0:s} ) not found!".format(infile))
        raise MissingInputFile(infile)

## CHECK THE BASE URL IN ENTRY DICTONARY AND MATCH TO COLLECTION IF DIFFERENT 
def check_collect_url(dictIn,collecturl):
    dictOut = dictIn
    if 'fullidset' in dictIn.keys():
    	dict_fullid = dictIn['fullidset'].strip('<>')
    	dict_path = os.path.dirname(dict_fullid)
    	logging.debug("dict_path={0:s}".format(dict_path))
    	logging.debug("collecturl={0:s}".format(collecturl))
        if dict_path != collecturl:
            dict_name = os.path.basename(dict_fullid)
            logging.warning("Input path for entry {0:s} does not match collection path. Correcting to {1:s}".format(dict_name, collecturl))
            new_fullid = '/'.join([collecturl,dict_name])
            dictOut['fullidset'] = str('{0:s}{1:s}{2:s}'.format('<',new_fullid,'>'))
	    
    if 'reg_base' in dictIn.keys():
        if dictIn['reg_base'] != collecturl :
            logging.debug("reg_base = {0:s}".format(dictIn['reg_base']))		
            logging.warning("Input registry base path does not match collection path. Correcting to {0:s}".format(collecturl))
            dictOut['reg_base'] = collecturl
   
    if collecturl.isspace():
        collecturl_path = collecturl
    else:    
        collecturl_path = ''.join([collecturl,'/'])
    logging.debug("collecturl_path = {0:s}".format(collecturl_path))	

    if 'reg_base_path' in dictIn.keys():
        if dictIn['reg_base_path'] != collecturl_path :
            logging.warning("Correcting reg_base_path from {0:s} to {1:s}".format(dictIn['reg_base_path'],collecturl_path))	
            dictOut['reg_base_path'] = collecturl_path

    return dictOut 

## RENAME ANY STANARD NAMES WITH ONES I AM USING FOR VARIABLES FOR ENTRY DICTIONARY
def checkdict_keynames(dictIn):
    logging.debug("Checking the variable keys for data dictionary.")	
    renamevar={'@id':'fullidset','reg:notation':'idset','@notation':'idset','reg_notation':'idset','id':'idset','fullid':'fullidset','label':'huread','skos_notation':'skosnote','skos:notation':'skosnote','description':'desctxt','dct:description':'desctxt','text':'desctxt','rdfs:label':'huread','@status':'substatus','status':'substatus','dct:references':'refs','references':'refs'}
    logging.debug("dictIn = {0:s}".format(dictIn))

    ## IF LIST
    if isinstance(dictIn, list):
        logging.debug("Input dictIn is a list")
    	dictOut = []
    	for pos, item in enumerate(dictIn):
                if item in renamevar.keys():
                    logging.debug("Replacing item {0:s} with {1:s}".format(item,renamevar[item]))	
                    dictOut.append(renamevar[item])
                elif item.lower() in renamevar.keys():
                    logging.debug("Replacing item {0:s} with {1:s}".format(item,renamevar[item.lower()]))
                    dictOut.append(renamevar[item.lower()])
                else:
                    dictOut.append(item)    

    elif isinstance(dictIn, dict):
    ## IF DICTIONARY 
        logging.debug("Input dictIn is a dictionary")
        dictOut = dictIn
        for key1 in dictOut.keys():
            if key1 in renamevar.keys():
                logging.debug("Replacing key {0:s} with {1:s}".format(key1,renamevar[key1]))	
                dictOut[renamevar[key1]] = dictOut.pop(key1)
            elif key1.lower() in renamevar.keys():
                logging.debug("Replacing key {0:s} with {1:s}".format(key1,renamevar[key1.lower()]))
                dictOut[renamevar[key1.lower()]] = dictOut.pop(key1)
    
    logging.debug("dictOut = {0:s}".format(dictIn))
    return dictOut

## CREATE DICTIONARY FOR WRITING OUT REGISTRY ENTRY FILES 
## USING INPUT LIST OF ENTRY KEYS (listK) AND ARRAY OF ENTRY VALUES (listV)
## OPTIONAL INPUTS FOR DEFAULT REGISTRY URI BASE AND ACCEPTABLE STATUS VALS    
def set_entry_dict(listK, listV, regbase_default='', accepted_status=ACCEPTED_STATUS_DEFAULT):	
    logging.info("BUILDING DICTIONARY FOR DATA ENTRIES....")
    vardict_all = []
    entriout = 0
    for entri, listVx in enumerate(listV): 
	logging.debug("BEGIN building data dictionary from entry={0:s}...".format(str(entri)))    
        vardict0 = dict(zip(listK,listVx))
        vardict = checkdict_keynames(vardict0)

        ## CHECK NEEDED ARGUMENTS AND EXIT IF ANY ARE MISSING
        ## CHECK ID (REQUIRED)
        if 'idset' not in vardict.keys() or not vardict['idset']:
            logging.warning("No ID found for entry={0:s}. Checking for full path ID.".format(str(entri)))
            if 'fullidset' in vardict.keys():
                if not vardict['fullidset'].strip('<>') or not vardict['fullidset']:
                    logging.error("ERROR: Needed variable ID(reg:notation) is missing from entry {0:s}. NO ENTRY FOR DICTIONARY BUILT.".format(str(entri)))
                    continue 
                else:	
                    ## BREAK DOWN FULL ID (URI) TO GET ID AND BASE URI
                    logging.warning("WARNING: registry ID not explicitly set. Reading from full URI.")
                    logging.debug('fullidset={0:s}'.format(vardict['fullidset']))
                    fullid = vardict['fullidset'].strip('<>')
                    vardict['reg_base'] = os.path.dirname(fullid)
                    vardict['idset'] = os.path.basename(fullid)
            else:
                logging.error("ERROR: Needed variable ID(reg:notation) is missing from entry {0:s}. NO ENTRY FOR DICTIONARY BUILT.".format(str(entri)))
                continue 
        ## CHECK HUMAN-READABLE LABEL(NAME) (REQUIRED - MAKE FROM ID IF MISSING)      
        if 'huread' not in vardict.keys() or not vardict['huread']:
            vardict['huread'] = vardict['idset']
            logging.warning("No human-readable label (name) input. Building label from ID.")
        ## CHECK DESCRIPTION (HAS DEFAULT)
        if 'desctxt' not in vardict.keys() or not vardict['desctxt']:
            logging.warning("No description provided for id={0:s}. Building placeholder text.".format(vardict['idset']))		
            vardict['desctxt'] = "Registry entry for " + vardict['huread'] + "(registry ID " + vardict['idset'] + "). Please update this description."
        ## CHECK SKOS-NOTATION (HAS DEFAULT)
        if 'skosnote' not in vardict.keys() or not vardict['skosnote']:
            logging.warning("Notice: Skos nottation for Entry is missing. Generating from ID.")
            vardict['skosnote'] = vardict['idset']
        ## SET THE URI BASE FOR THE REGISTRY (HAS DEFAULT; OPTIONAL READ-IN)
        if 'reg_base' not in vardict.keys():
            if 'fullidset' in vardict.keys():
                fullidp = vardict['fullidset']
                stripidp = fullidp.strip('<>')
                vardict['reg_base'] = os.path.dirname(stripidp)
            else:
                vardict['reg_base'] = regbase_default
                logging.warning("WARNING: No register base found. Leaving blank (entry uri will be local)")
        ## SET THE URI BASE PATH (ENDS WITH /) FROM reg_base         
        id_reg_base = vardict['reg_base']
        if(not (id_reg_base and not id_reg_base.isspace())):
            vardict['reg_base_path'] = id_reg_base
        else:
            uristripchk = id_reg_base.strip('/')
            if(uristripchk.isspace() or not uristripchk):
                vardict['reg_base_path'] = ''
            else:
                if id_reg_base[-1] != "/":
                    vardict['reg_base_path'] = id_reg_base + "/"
                else:
                    vardict['reg_base_path'] = id_reg_base
        ## SET SUBMISSION STATUS (OPTIONAL. HAS DEFAULT=None)
        if 'substatus' not in vardict.keys():
          vardict['substatus'] = "None"
        else:
          vardict['substatus'] = vardict['substatus'].title()
          if vardict['substatus'] not in accepted_status:
            logging.warning("WARNING: Submission Status Not Valid. Default status will be assigned.")
            vardict['substatus'] = "None"
                    
        ## SET DICTIONARY INTO ARRAY (WILL NOT MAKE IT HERE IF VITAL DATA MISSING)
        logging.debug("entri={0:s} entriout={1:s}".format(str(entri),str(entriout)))
        logging.debug("vardict_all[{0:s}]={1:s}".format(str(entriout),vardict))
        vardict_all.append([])
        vardict_all[entriout] = vardict
	entriout = entriout + 1

    logging.debug("vardict_all={0:s}".format(vardict_all))
    logging.info("DATA DICTIONARY BUILD COMPLETE.")
    return (vardict_all)

## WRITE COLLECTION/CONTAINER FILE IN TTL FORMAT 
def write_collection_ttl(outfilettl, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNotation, collectRefs, member_vardict=None, prefix_dict=prefix_dict_default, mode='new'):
    
    logging.debug("mode={0:s}".format(mode))
    
    if setRegistry[-1] == "/":
        setRegistry = setRegistry[:-1]
        
    collect_fullpath = '/'.join([setRegistry,collectname])
    logging.debug("collect_fullpath={0:s}".format(collect_fullpath))
    
    if mode == 'append':
        writemode = 'a+'
    else:
        writemode = 'w+'
    
    ##CREATE LIST OF REFS    
    if collectRefs != 'None' and collectRefs:
        collectRefsWrite = 1
        collectRefs_list = collectRefs.split(",")
        allrefi = []
        for refi in collectRefs_list:
           refi2 = ''.join(['<',refi,'>']) 
           allrefi.append(refi2)
        collectRefs_fullstr = ','.join(allrefi)
    else:
        collectRefsWrite = 0
    
    with open(outfilettl,writemode) as outfile_ttl:
        ## PREFIXES - ONLY ADD ONCE
        if mode == 'new':
            for x, y in prefix_dict.items():
                outfile_ttl.write('{0:s} {1:s}{2:s} {3:s}{4:s}{5:s} {6:s}\n'.format("@prefix",x,":","<",y,">","."))
        ## SET COLLECTION DATA 
        outfile_ttl.write('{0:s}\n'.format(''))
        outfile_ttl.write('{0:1s}{1:s}{2:1s}\n'.format('<',collect_fullpath,'>'))
        outfile_ttl.write('{0:8s}{1:16s} {2:s}\n'.format('','a','ldp:Container , skos:Collection , reg:Register ;'))
        outfile_ttl.write('{0:8s}{1:16s} "{2:s}" ;\n'.format('','rdfs:label',collectlabel))
        if collectRefsWrite == 1:
            outfile_ttl.write('{0:8s}{1:18s} {2:s} {3:1s}\n'.format('','dct:references',collectRefs_fullstr,';'))
        if skosNotation != 'None' and skosNotation:
	        outfile_ttl.write('{0:8s}{1:16s} "{2:s}" ;\n'.format('','skos:notation',skosNotation))	
            
        if member_vardict:
            memberlist = []
            for entri,vardictx in enumerate(member_vardict):
                memberlist.append(str('{0:1s}{1:s}{2:s}{3:s}{4:1s}'.format('<',vardictx['reg_base'],'/',vardictx['idset'],'>')))
            memberliststr = ' , '.join(memberlist)
            outfile_ttl.write('{0:8s}{1:16s} {2:s} {3:1s}\n'.format('','rdfs:member',memberliststr,';'))
                    
        outfile_ttl.write('{0:8s}{1:16s} "{2:s}" .\n'.format('','dct:description',collectdesc))
        ## SET COLLECTION ITEM DATA
        outfile_ttl.write('{0:1s}\n'.format(''))
        outfile_ttl.write('{0:1s}{1:s}{2:2s}{3:s}{4:1s}\n'.format('<',setRegistry,'/_',collectname,'>'))
        outfile_ttl.write('{0:8s}{1:18s} {2:s} {3:1s}\n'.format('','a','reg:RegisterItem',';'))
        outfile_ttl.write('{0:8s}{1:18s} {2:1s}\n'.format('','reg:definition','['))
        outfile_ttl.write('{0:12s}{1:16s} {2:1s}{3:s}{4:1s} {5:1s}\n'.format('','reg:entity','<',collect_fullpath,'>',';'))
        outfile_ttl.write('{0:8s}{1:1s} {2:1s}\n'.format('',']',';'))
        if setStatus != 'None' and setStatus:
            outfile_ttl.write('{0:8s}{1:18s} {2:1s}{3:s} {4:1s}\n'.format('','reg:status','reg:status',setStatus,';'))
        outfile_ttl.write('{0:8s}{1:1s}\n'.format('','.'))
        
        ## FINISH AND CLOSE
        outfile_ttl.write('{0:s}'.format(''))
        outfile_ttl.close()
    
    logging.info("COMPLETED CONTAINER FILE: {0:s}".format(outfilettl))

## WRITE COLLECTION IN CSV
## THIS SHOULD BECOME MORE SOPHISTICATED
def write_collection_csv(out_filename_csv, collectname, setRegistry, collectlabel, collectdesc, setStatus, skosNotation, collectRefs, member_vardict=None, prefix_dict=prefix_dict_default, mode='new'):

    if setRegistry[-1] == "/":
        setRegistry = setRegistry[:-1]
        
    collect_fullpath = '/'.join([setRegistry,collectname])
    logging.debug("collect_fullpath={0:s}".format(collect_fullpath))

    if mode == 'append':
        writemode = 'a+'
    else:
        writemode = 'w+'
        
    ## CREATE LIST OF REFS    
    if collectRefs != 'None' and collectRefs:
        collectRefs_list = collectRefs.split(",")
        allrefi = []
        for refi in collectRefs_list:
           refi2 = ''.join(['<',refi,'>']) 
           allrefi.append(refi2)
        collectRefs_fullstr = '|'.join(allrefi)
    else:
        collectRefs_fullstr = ''        
       
    with open(out_filename_csv,writemode) as outfile_csv:
        if mode == 'new':
            outfile_csv.write('{0:s}\n'.format('@id,dct:description,rdf:type,rdfs:label,skos:notation,@status,dct:references'))
        outfile_csv.write('{0:1s}{1:s}{2:1s},"{3:s}",{4:s},{5:s},{6:s},{7:s}\n'.format('<',collect_fullpath,'>',collectdesc,'ldp:Container|reg:Register|skos:Collection',collectlabel,skosNotation,collectRefs_fullstr,setStatus.lower()))
        outfile_csv.close()     
        
## WRITE REGISTRY ENTRY IN TTL FORMAT
def write_entry_ttl(var_dict, prefix_dict=prefix_dict_default, out_filename_ttl='testout.ttl', **kwargs):
    
    logging.debug("WRITING TTL OUTPUT FILE {0:s}".format(out_filename_ttl))
    
    if 'force_status' in kwargs.keys():
        force_status = kwargs['force_status']
        
    with open(out_filename_ttl,'w') as outfile_ttl:
        ## PREFIXES - ONLY ADD ONCE  
        for x, y in prefix_dict.items():
            outfile_ttl.write('{0:s} {1:s}{2:s} {3:s}{4:s}{5:s} {6:s}\n'.format("@prefix",x,":","<",y,">","."))
        ## SET DATA - REPEAT FOR EVERY ENTRY
        for entri,vardictx in enumerate(var_dict):
            
            ## CORRECT INNER QUOTES
            for ent in vardictx.keys():
                vardictx[ent] = replace_inner_quotes(vardictx[ent],'ttl')
            
            ## SET STATUS
            try: force_status
            except:
                pass
            else:
                vardictx['substatus'] = force_status
                
            ## CREATE LIST OF REFS    
            if 'refs' in vardictx.keys() and vardictx['refs']:
                collectRefsWrite = 1
                collectRefs_list = vardictx['refs'].split(",")
                allrefi = []
                for refi in collectRefs_list:
                   refi2 = ''.join(['<',refi,'>']) 
                   allrefi.append(refi2)
                collectRefs_fullstr = ','.join(allrefi)
            else:
                collectRefsWrite = 0    
                
            ## SET REGISTRY ENTITY
            outfile_ttl.write('{0:1s}\n'.format(''))
            outfile_ttl.write('{0:1s}{1:s}{2:s}{3:1s}\n'.format('<',vardictx['reg_base_path'],vardictx['idset'],'>'))
            outfile_ttl.write('{0:8s}{1:18s} {2:s} {3:1s}\n'.format('','a','skos:Concept',';'))
            outfile_ttl.write('{0:8s}{1:18s} {2:1s}{3:s}{4:1s} {5:1s}\n'.format('','rdfs:label','"',vardictx['huread'],'"',';'))
            outfile_ttl.write('{0:8s}{1:18s} {2:1s}{3:s}{4:1s} {5:1s}\n'.format('','dct:description','"',vardictx['desctxt'],'"',';'))
            if collectRefsWrite == 1:
                outfile_ttl.write('{0:8s}{1:18s} {2:s} {3:1s}\n'.format('','dct:references',collectRefs_fullstr,';'))
            if 'skosnote' in vardictx.keys():
                outfile_ttl.write('{0:8s}{1:18s} {2:1s}{3:s}{4:1s} {5:1s}\n'.format('','skos:notation','"',vardictx['skosnote'],'"',';'))
            outfile_ttl.write('{0:8s}{1:1s}\n'.format('','.'))
            ## SET REGISTRY ITEM
            outfile_ttl.write('{0:1s}\n'.format(''))
            outfile_ttl.write('{0:1s}{1:s}{2:1s}{3:s}{4:1s}\n'.format('<',vardictx['reg_base_path'],'_',vardictx['idset'],'>'))
            outfile_ttl.write('{0:8s}{1:18s} {2:s} {3:1s}\n'.format('','a','reg:RegisterItem',';'))
            outfile_ttl.write('{0:8s}{1:18s} {2:1s}\n'.format('','reg:definition','['))
            outfile_ttl.write('{0:12s}{1:16s} {2:1s}{3:s}{4:s}{5:1s} {6:1s}\n'.format('','reg:entity','<',vardictx['reg_base_path'],vardictx['idset'],'>',';'))
            outfile_ttl.write('{0:8s}{1:1s} {2:1s}\n'.format('',']',';'))
            if vardictx['substatus'] != 'None':
                outfile_ttl.write('{0:8s}{1:18s} {2:1s}{3:s} {4:1s}\n'.format('','reg:status','reg:status',vardictx['substatus'],';'))
            outfile_ttl.write('{0:8s}{1:1s}\n'.format('','.'))
        outfile_ttl.close()

## WRITE REGISTRY ENTRY IN CSV FORMAT
## NOTE: THIS FORMAT DOES NOT CONTAIN AS MUCH INFO AS TTL OR JSON (RIGHT NOW)         
def write_entry_csv(var_dict, prefix_dict=prefix_dict_default, out_filename_csv='testout.csv', **kwargs):

    logging.debug("WRITING CSV CONCEPT OUTPUT FILE {0:s}".format(out_filename_csv))
    
    if 'force_status' in kwargs.keys():
        force_status = kwargs['force_status']      
          
    with open(out_filename_csv,'w') as outfile_csv:
        outfile_csv.write('{0:s}\n'.format('@id,dct:description,rdf:type,rdfs:label,skos:notation,dct:references,@status'))
        for entri,vardictx in enumerate(var_dict):
            
            ## CORRECT INNER QUOTES
            for ent in vardictx.keys():
                vardictx[ent] = replace_inner_quotes(vardictx[ent],'csv')
            
            ## SET STATUS
            try: force_status
            except: pass
            else:
                vardictx['substatus'] = force_status
            if 'substatus' not in vardictx.keys():
                vardictx['substatus'] = None 
                                
            ## CREATE LIST OF REFS    
            if 'refs' in vardictx.keys() and vardictx['refs']:
                collectRefs_list = vardictx['refs'].split(",")
                allrefi = []
                for refi in collectRefs_list:
                   refi2 = ''.join(['<',refi,'>']) 
                   allrefi.append(refi2)
                collectRefs_fullstr = '|'.join(allrefi)
            else:
                collectRefs_fullstr = ''    

            outfile_csv.write('{0:1s}{1:s}{2:s}{3:1s},"{4:s}",{5:s},"{6:s}",{7:s},{8:s},{9:s}\n'.format('<',vardictx['reg_base_path'],vardictx['idset'],'>',vardictx['desctxt'],'skos:Concept',vardictx['huread'],vardictx['skosnote'],collectRefs_fullstr,vardictx['substatus'].lower()))

        outfile_csv.close()     

## WRITE REGISTRY ENTRY IN JSON FORMAT
        ## THIS NEEDS WORK FOR MULTIPLE REFERENCES STILL
def write_entry_json(var_dict, prefix_dict=prefix_dict_default, out_filename_json='testout.json', **kwargs):
    
    logging.debug("WRITING JSON CONCEPT OUTPUT FILE {0:s}".format(out_filename_json))
    
    if 'force_status' in kwargs.keys():
        force_status = kwargs['force_status']
    
    nentri = len(map(len,var_dict))
    with open(out_filename_json,'w') as outfile_json:
        outfile_json.write('{0:1s}\n'.format('{'))
        ## PUT IN DATA (LOOP)
        outfile_json.write('{0:s}\n'.format('"@graph" : ['))
        en = 0
        for entri,vardict in enumerate(var_dict):
            en = en + 1
            ## set registry info
            outfile_json.write('{0:s}\n'.format('{'))
            outfile_json.write('"{0:s}" : "_:t{1:s}",\n'.format('@id',str(en)))
            outfile_json.write('"{0:s}" : {1:1s}\n'.format('reg:entity','{'))
            outfile_json.write('"{0:s}" : "{1:s}{2:s}"\n'.format('@id',vardict['reg_base_path'],vardict['idset']))
            outfile_json.write('{0:s}\n'.format('},'))
            outfile_json.write('"{0:s}" : {1:1s}\n'.format('reg:sourceGraph','{'))
            outfile_json.write('"{0:s}" : "{1:s}_{2:s}:{3:s}{4:s}"\n'.format('@id',vardict['reg_base_path'],vardict['idset'],str(en),'#graph'))
            outfile_json.write('{0:s}\n'.format('}'))
            outfile_json.write('{0:s}\n'.format('},'))
        
        en = 0
        for entri,vardict in enumerate(var_dict):
            
            try: force_status
            except:
                pass
            else:
                vardict['substatus'] = force_status            
            
            en = en + 1
            ## set register item inputs
            outfile_json.write('{0:s}\n'.format('{'))
            outfile_json.write('"{0:s}" : "{1:s}_{2:s}",\n'.format('@id',vardict['reg_base_path'],vardict['idset']))
            outfile_json.write('"{0:s}" : "{1:s}",\n'.format('@type','reg:RegisterItem'))
            outfile_json.write('"{0:s}" : "{1:s}",\n'.format('dct:description',vardict['desctxt']))
            outfile_json.write('"{0:s}" : {1:1s}\n'.format('reg:definition','{'))
            outfile_json.write('"{0:s}" : "_:t{1:s}"\n'.format('@id',str(en)))
            outfile_json.write('{0:s}\n'.format('},'))
            outfile_json.write('"{0:s}" : {1:1s}\n'.format('reg:itemClass','{'))
            outfile_json.write('"{0:s}" : "{1:s}"\n'.format('@id','skos:Concept'))
            outfile_json.write('{0:s}\n'.format('},'))
            outfile_json.write('"{0:s}" : {1:1s}\n'.format('reg:register','{'))
            outfile_json.write('"{0:s}" : "{1:s}"\n'.format('@id',vardict['reg_base']))
            outfile_json.write('{0:s}\n'.format('},'))
            outfile_json.write('"{0:s}" : {1:1s}\n'.format('reg:status','{'))
            outfile_json.write('"{0:s}" : "reg:status{1:s}"\n'.format('@id',vardict['substatus']))
            outfile_json.write('{0:s}\n'.format('},'))
            outfile_json.write('"{0:s}" : "{1:s}"\n'.format('rdfs:label',vardict['huread']))
            outfile_json.write('{0:s}\n'.format('},'))
            ## set entity inputs
            outfile_json.write('{0:s}\n'.format('{'))
            outfile_json.write('"{0:s}" : "{1:s}{2:s}",\n'.format('@id',vardict['reg_base_path'],vardict['idset']))
            outfile_json.write('"{0:s}" : "{1:s}",\n'.format('@type','skos:Concept'))
            outfile_json.write('"{0:s}" : "{1:s}",\n'.format('dct:description',vardict['desctxt']))
            if 'refs' in vardict.keys():
                outfile_json.write('"{0:s}" : "{1:s}",\n'.format('dct:references',vardict['refs']))
            outfile_json.write('"{0:s}" : "{1:s}",\n'.format('rdfs:label',vardict['huread']))
            if 'skosnote' in vardict.keys():
                outfile_json.write('"{0:s}" : "{1:s}"\n'.format('skos:notation',vardict['skosnote']))
            if en == nentri:
                outfile_json.write('{0:s}\n'.format('}'))
            else:
                outfile_json.write('{0:s}\n'.format('},'))
        
        outfile_json.write('{0:1s}\n'.format('],'))
        ## PUT IN THE PREFIXES
        outfile_json.write('{0:s} {1:1s} {2:1s}\n'.format('"@context"',':','{'))
        nprefix = len(prefix_dict.keys());
        ip = 0
        for x, y in prefix_dict.items():
            ip = ip + 1
            if ip == nprefix:
                outfile_json.write('{0:2s}{1:1s}{2:s}{3:1s} {4:1s} {5:1s}{6:s}{7:1s}\n'.format('','"',x,'"',':','"',y,'"'))
            else:
                outfile_json.write('{0:2s}{1:1s}{2:s}{3:1s} {4:1s} {5:1s}{6:s}{7:1s}{8:1s}\n'.format('','"',x,'"',':','"',y,'"',","))
        outfile_json.write('{0:1s}\n'.format('}'))
        outfile_json.write('{0:1s}\n'.format('}'))
        outfile_json.close()

## CREATE A DICTIONARY OF THE PATHS OF DATA IN A FILE 
## THIS IS USED WITH FUNCTION split_csv_bypath
def get_data_paths(datafile, *args, **kwargs):
    
    if 'registry_base' in kwargs.keys():
        registry_base = kwargs['registry_base']
    else:
        registry_base = OUR_REGISTRY
    
    check_datafile(datafile)
    startli = check_elements_startline(datafile)
    
    if startli < 0:
        logging.error("ERROR: No good start line found for {0:s}".format(datafile))
        return None, None
    
    (listK, listV) = read_elements(datafile, firstline=startli)
    
    logging.debug("listK={0:s}".format(listK))
    logging.debug("listV={0:s}".format(listV))
    
    ## IF PATH COLUMN NOT SET, FIND IT FROM DATA FIRST LINE
    if len(args) > 0:
        pathcol = args[0]
        
    try: 
	    pathcol
    except:
        logging.warning("WARNING: No path field number set. Searching data.")
        for pcol, val in enumerate(listV[0]):
    	    logging.debug("pcol={0:s}, val={1:s}".format(str(pcol),val))	
    	    x = val.find('http:')
    	    if x > -1:
                pathcol = pcol
                break
    	    else:
    		    x2 = val.find('https:')
    		    if x2 > -1:
    		        pathcol = pcol
    		        break
                
        if pathcol > -1:
            logging.debug("URL structure found at column {0:s}".format(str(pcol)))
        else:
            logging.error("ERROR: No path field set and URL structure not found in data. ")
            return None, None
    
    logging.info("Using input path column={0:s}".format(str(pathcol)))

    paths_dict = {}
    item_obj_list = []
    
    for row, data in enumerate(listV):
        path_in0 = data[pathcol]
        logging.debug("raw data at row {0:s} = {1:s}".format(str(row), path_in0))
        path_in0 = path_in0.strip('<>')
        path_in0 = path_in0.strip('"')
        
        path_in = os.path.dirname(path_in0)
        member_in = os.path.basename(path_in0)

        path_depth, parent_path_list = get_path_depth(path_in0, registry_base)
    
        x = ItemPathObj(member_in, depth=path_depth, dir_path=path_in, parent_dir=parent_path_list[1], full_path=path_in0, src_file=datafile, src_line=row)
        item_obj_list.append(x)
        
        if path_in not in paths_dict.keys():
            paths_dict[path_in] = []
            paths_dict[path_in].append(row)
        else:
            paths_dict[path_in].append(row)

    collect_obj_list = []
        
    for pathnum, pathname in enumerate (paths_dict.keys()):
        groupname = os.path.basename(pathname)
        if not groupname:
            groupname = "_"       
        logging.debug("groupname={0:s}".format(groupname))

        memberz = []
        rowz = []
        grouprow = -1
        for obj in item_obj_list:
            if obj.parent_dir == groupname:
                memberz.append(obj.name)
                rowz.append(obj.src_line)    
            if obj.name == groupname:
                grouprow = obj.src_line
                depthx = obj.depth
                parent_dirx=obj.parent_dir
                fullpathInx=obj.full_path
                dir_pathx = obj.dir_path
                
        if grouprow < 0:  
            logging.info("WARNING: No matching object from file={0:s} found for group name={1:s}. Calculating.".format(datafile, groupname))
            path_depth_miss, parent_path_list_miss = get_path_depth(pathname, registry_base)
            depthx = path_depth_miss
            if len(parent_path_list_miss) < 2:
                parent_dirx = '[Top level]'
            else:
                parent_dirx=parent_path_list_miss[1]
            fullpathInx = pathname
            dir_pathx = os.path.dirname(pathname)

        logging.info("Collection properties: name={0:s} depth={1:d} parent_dir={2:s} memberz={3:s} member_rows={4:s} fileIn={5:s} full_path={6:s}".format(groupname, depthx, parent_dirx, memberz, rowz, datafile, fullpathInx))  
        x1 = CollectionObj(groupname, depth=depthx, parent_dir=parent_dirx, dir_path=dir_pathx, members=memberz, member_rows=rowz, fileIn=datafile, full_path=fullpathInx, fileDataOut='')
        collect_obj_list.append(x1)
      
    return collect_obj_list, item_obj_list


## FUNCTION TAKES CSV FILE WITH DATA INCLUDING PATHS AND SPLITS INTO NEW FILES
## WHICH ALL SHARE MATCHING PATHS 
## PATHCOL = NUMBER COLUMN (1st=0) WHERE PATH DATA IS INCLUDED 
def split_csv_bypath(datafile, *args, **kwargs):
    outfilelist = []

    ## SET FILE BASE AND TIMESTAMP
    if 'outdir' in kwargs.keys():
        out_path = kwargs['outdir']
    else:
	    out_path = os.path.dirname(datafile)
    
    logging.debug("out_path={0:s}".format(out_path))

    datafile_base = os.path.splitext(os.path.basename(datafile))[0]
    nowdx = datetime.now().strftime('%Y%m%d%H%M%S')
    
    check_datafile(datafile)
    startli = check_elements_startline(datafile)
    
    if startli < 0:
        logging.error("ERROR: No good start line found for {0:s}".format(datafile))
        return outfilelist, ''
    
    (listK, listV) = read_elements(datafile, firstline=startli)
    
    logging.debug("listK={0:s}".format(listK))
    logging.debug("listV={0:s}".format(listV))
    
    ## IF PATH COLUMN NOT SET, FIND IT FROM DATA FIRST LINE
    if len(args) > 0:
        pathcol = args[0]
    
    try: pathcol
    except:
        groupobjs, objectlist = get_data_paths(datafile)
    else:    
        groupobjs, objectlist = get_data_paths(datafile, pathcol)
    
    if groupobjs is None or groupobjs == None:
        logging.error("ERROR: No path field set and URL structure not found in data. NOT SPLITTING FILES.")
        outfilelist.append(datafile)
        return outfilelist, listK
    
    paths_dict = {}
    for collectx in groupobjs:
        paths_dict[collectx.name] = collectx.member_rows
        
    if len(paths_dict) > 1:
        logging.warning("WARNING: Mutliple paths detected in same file. Splitting into new files.")
        for pathnum, groupname in enumerate (paths_dict.keys()):
               
            filename = ''.join([datafile_base,'_',str(groupname),'.csv'])
            outfilename = os.path.join(out_path,filename)
            
            ## IF FILE EXISTS GIVE FILENAME DATESTAMP
            if os.path.isfile(outfilename):
                filenamebase = os.path.splitext(os.path.basename(outfilename))[0]
                filename = ''.join([filenamebase,'_',nowdx,'.csv'])
                outfilename = os.path.join(out_path,filename)
                
            logging.warning("Writing file out={0:s}".format(outfilename))
            outfilelist.append(outfilename)
                     
            with open(outfilename,'wb') as fileout:
                writer = csv.writer(fileout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(listK)
                for rowx in paths_dict[groupname]:
                    writer.writerow(listV[rowx])
                             
        return outfilelist, listK

    else:            
        outfilelist.append(datafile)

        return outfilelist, listK

## DIVIDE NESTED DICTIONARIES BY A KEYWORD VALUE AND RE-NEST BY VALUE GROUP
def divide_nestdict_by_key(vardict_all0, keyvar):
    paths_dict = {}
    for row, vardict in enumerate(vardict_all0):    
        path_in = vardict[keyvar]
        if path_in not in paths_dict.keys():
            paths_dict[path_in] = []
            paths_dict[path_in].append(row)
        else:
            paths_dict[path_in].append(row)
    
    num_paths = len(paths_dict) 
    if num_paths == 1:
        vardict_all_out = vardict_all0
    else:
        vardict_all_out = []
        for pathnum, pathname in enumerate (paths_dict.keys()):
            rowz = paths_dict[pathname]
            vardict_set = []
            for ent in rowz:
                vardict_set.append(vardict_all0[ent])
            vardict_all_out.append(vardict_set)
    
    return num_paths, vardict_all_out


## CORRECT THE VALUES OF A DICTIONARY FOR GIVEN KEYS
def correct_dict(dictIn, keyz, old_string, new_string):
    if isinstance(dictIn, list):
	dictOut = []
        for nestdict in dictIn:
            for keyi in keyz:
		nestdict[keyi] = nestdict[keyi].replace(old_string, new_string)
            dictOut.append(nestdict)
    else:
	dictOut = dictIn
	for keyi in dictOut:
	    dictOut[keyi] = dictOut[keyi].replace(old_string, new_string)

    return dictOut 

## FUNCTION TO GET DEPTH OF PATH
def get_path_depth(path, known_top_level='', max_depth_check=20):

    parent_path_list = []
    
    if known_top_level and known_top_level[-1] == "/":
        known_top_level = known_top_level[:-1]
    logging.debug("known_top_level={0:s}".format(known_top_level))

    depth = 0
    while depth < max_depth_check:
	if path == known_top_level:
	    return depth, parent_path_list
        else:
            (pathx, filex) = os.path.split(path)
            if not pathx:
	            return depth, parent_path_list
            else:
    	        if not filex:
    	            path = pathx
                else:
    	            depth += 1
    	            path = pathx
                    if depth > 0:
                        parent_path_list.append(filex)
                    
## MAKE SURE INPUT STRINGS FOR FUNCTION CALLS DO NOT HAVE ERRANT SPACES
def check_call_input_str(in_str):
    logging.debug('INPUT STRING=<<{0:s}>>'.format(in_str))
    rep0 = in_str.replace("= ","=")
    rep1 = rep0.replace(" =","=")
    rep2 = rep1.replace(" ,",",")
    output_str = rep2.replace(", ",",")
    logging.debug('OUTPUT STRING=<<{0:s}>>'.format(output_str))
    return output_str

## CHECK FOR INNER QUOTES IN TEXT AND REPLACE WITH APPROPRIATE CHAR FOR FILE FORMAT
def replace_inner_quotes(in_str,filetype):    
    x0 = in_str.find('"')   
    if x0 > -1:
        logging.debug("in_str ={0:s}".format(in_str))
        in_str0 = in_str.strip('"')
        x = in_str0.find('"')
        if x > -1:
            logging.debug("INNER QUOTES FOUND. MAKING REPLACEMENT.")
            logging.debug("in_str0={0:s}".format(in_str0))
            if filetype == 'csv' or filetype == '.csv':
                out_str0 = in_str0.replace('"','""')
                if x0 == 0:
                    out_str = ''.join(['"',out_str0,'"'])
                else:
                    out_str = out_str0
                logging.debug("out_str={0:s}".format(out_str))
                return out_str
            elif filetype == 'ttl' or filetype == '.ttl':
                out_str0 = in_str0.replace('"','\\"')
                if x0 == 0:
                    out_str = ''.join(['"',out_str0,'"'])
                else:
                    out_str = out_str0
                logging.debug("out_str={0:s}".format(out_str))
                return out_str
            else:
                logging.error("ERROR: file type not specified. No replacement made.")
                return in_str
        else:
            return in_str
    else:
        return in_str