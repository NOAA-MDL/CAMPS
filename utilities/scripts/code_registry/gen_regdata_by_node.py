#!/usr/bin/env python

"""
NAME: gen_regdata_by_node.py

REQUIREMENTS: campsregistry

PURPOSE:
    
THIS CREATES PATH-GROUPED COLLECTION AND CONCEPT DATA FILES FOR USE WITH REGISTRY API,
AS WELL AS CSV FILES SPLIT BY GROUP, AND AN INFORMATION OUTPUT FILE ON CREATED
DATA FILES AND PATH INFORMATION (TO BE USED FOR ORDERING SUBMISSION INTO API)

THIS CODE USES FOR INPUT DATA FILES BEING COLLECTED FROM NODES (CREATED BY ZHAN ZHANG'S JAVA CODES), WITH ONE FILE
FOR ALL COLLECTIONS IN NODE ({node}NodeCollections.csv) AND ONE FILE FOR ALL CONCEPTS IN NODE ({node}NodeConcepts.csv)
(NOTE: THE CURRENT CODE DOES NOT BACKUP INFO ON THE TOP-LEVEL REGIGISTRY COLLECTION/SUBREGISTERS
THESE WILL NEED TO BE MADE) 
 
USAGE:
gen_regdata_by_node.py [NO INPUTS FOR INTERACTIVE]
gen_regdata_by_node.py [node name] [dir containing node-data csv files] uri_replace=[old uri string],[new uri string](optional) ...
                            outdir_base=[directory to create dir with node-gen files](optional; default is code dir) ...
                            status=[status](optional)

HISTORY:
2019/09/16 - Stearns - First working version completed (still needs cleanup and write out of info file)
2019/09/18 - Stearns - Added more info about what is made and changed where info file written
                     - Reworked how collection files were generated to fix bug where collections with
                     no concepts were not being generated
2019/09/25 - Stearns - major reworking of how objects are created and used, changed csv_split_and_group
                     - updated report file with info on directory structure and outputs
2019/10/09 - Stearns - added fix to check call strings to deal with errant spaces (function check_call_input_str)
2019/10/10 - Stearns - added fix to have error if no concept file is present (concept file can be blank)
2019/10/15 - Stearns - changed call to use 'python' in the call, and changed to list input instead of string (as this is supposed
                        to be safer cross-platform. The list call is kept in a comment just in case.)
2019/10/16 - Stearns - updated code to be able to handle nodes that have either missing collection or concepts csv file
                       updated default path base, cleaned up code some                     

"""
import os
import sys
import logging

from subprocess import call

from datetime import datetime

from campsregistry import read_elements
from campsregistry import checkmake_output_path
from campsregistry import check_elements_startline
from campsregistry import split_csv_bypath
from campsregistry import checkdict_keynames
from campsregistry import get_data_paths
from campsregistry import check_call_input_str
from campsregistry import check_datafile

from campsregistry import FILEPATH_DEFAULT
from campsregistry import DATA_FILEPATH_DEFAULT

#from campsregistry import MissingInput
#from campsregistry import MissingInputFile

##
## CLASSES
##

class MixedCollectionObj(object):
    def __init__(self, name, depth=0, parent_dir='', members='', dir_path='', has_items='', item_members='', fileDataOut='', fileCreated=0):
        self.name = name
        self.depth = depth
        self.dir_path = dir_path
        self.parent_dir = parent_dir
        self.members = members
        self.has_items = has_items
        self.item_members = item_members
        self.fileDataOut = fileDataOut
        self.fileCreated = fileCreated

##
## DEFINE FUNCTIONS
##
  
## READ CSV SPLIT INTO FILES OF COLLECTIONS AND CREATE DATA OBJ OF COLLECTIONS GROUP INFO    
def csv_split_and_group(testfile0, **kwargs):  
    logging.debug("Input testfile0={0:s}".format(testfile0))
    err = check_datafile(testfile0, failcmd='continue')
    
    if err == 0:
        if 'outdir_set' not in kwargs.keys():
            outdir_set = FILEPATH_DEFAULT
        else:
            outdir_set = kwargs['outdir_set']    
        logging.debug("Input output dir={0:s}".format(outdir_set))
    
        ## SPLIT THE FILES INTO GROUPS-FILES
        datafilez, listKX = split_csv_bypath(testfile0,0,outdir=outdir_set)
        logging.debug("DATA FILES GENERATED FROM {0:s}={1:s}".format(testfile0,datafilez))
        
        ## GET PATH INFO
        group_objs, item_objs = get_data_paths(testfile0, 0)

    else:
        logging.warning("NO GOOD FILE {0:s} FOUND. SETTING group_objs=None AND item_objs=None".format(testfile0))
        datafilez = testfile0
        group_objs = None
        item_objs = None
                 
    return datafilez, group_objs, item_objs       

###


## 
## SET VARIABLES AND LOG 
##    
nowd = datetime.now().strftime('%Y%m%d%H%M%S')

## SET LOG FILE 
logdir = os.path.join(FILEPATH_DEFAULT,"logs")
checkmake_output_path(logdir)

logfile = os.path.join(logdir,''.join(['run_code_test_',nowd,'.log']))
logging.basicConfig(filename=logfile,level=logging.DEBUG)

##
## READ INPUTS
## 

if len(sys.argv) < 2:
    node = raw_input("node name:")
    node_datadir = raw_input("node csv file directory:")
    uri_replace_q = raw_input("over-write URI? (yes/no)")
    if uri_replace_q.lower() == "yes" or uri_replace_q.lower() == "y":
        uri_repl_old = raw_input("old uri string:")
        uri_repl_new = raw_input("new uri string:")
        uri_replace = ''.join([uri_repl_old,",",uri_repl_new])
    outdir_base = raw_input("output directory (leave blank for default):")
    set_status = raw_input("set status (leave blank for data-file setting):")
else:
    for arg in sys.argv[1:]:
        argy = arg.split("=")
        if argy[0] == 'node':
            node = argy[1]
        elif argy[0] == 'name':
            node = argy[1]
        elif argy[0] == 'datadir':
            node_datadir = argy[1]
        elif argy[0] == 'uri_replace':
	        uri_replace = argy[1]
        elif argy[0] == 'outdir_base' or argy[0] == 'outdir':    
            outdir_base = argy[1]
        elif argy[0] == 'status':
            set_status = argy[1]
	    
logging.debug("Inputs:{0:s}".format(sys.argv))

## SET IF OVERRIDING STATUS IN DATA FILES 
try: set_status
except: 
    force_status = 0
else:
    if not set_status:
        force_status = 0
    else:
        force_status = 1

logging.debug("force_status={0:s}".format(str(force_status)))
        
##
## RUN
##
 
## BUILD INPUT NAMES TO LOOK FOR
node_collections_filename = ''.join([node.lower(),'NodeCollections.csv'])
node_concepts_filename = ''.join([node.lower(),'NodeConcepts.csv'])

node_collections_file = os.path.join(node_datadir, node_collections_filename)
node_concepts_file = os.path.join(node_datadir, node_concepts_filename)

## BUILD OUTPUT FILE PATH
node_outdir_name = ''.join(['Node_datafiles_',node])
try: outdir_base
except: 
    outdir_base = DATA_FILEPATH_DEFAULT
else:
    if not outdir_base:
        outdir_base = DATA_FILEPATH_DEFAULT
        
node_outdir = os.path.join(outdir_base,node_outdir_name)
checkmake_output_path(node_outdir)

## SET THE DATA INFO FILE
infofilename = ''.join([node.upper(),'_NODE_REGISTRY_COLLECTIONS_REPORT.txt'])
infofilefull = os.path.join(node_outdir,infofilename)
if os.path.isfile(infofilefull):
    infofilename = ''.join([node.upper(),'_NODE_REGISTRY_COLLECTIONS_REPORT_',nowd,'.txt'])
    infofilefull = os.path.join(node_outdir,infofilename)

## SPLIT THE RAW CSV FILES AND GET COLLECTION GROUP INFORMATION
logging.debug("RUN COLLECTIONS CSV")
datafilezC, objectzC, itemzC = csv_split_and_group(node_collections_file, outdir_set=node_outdir)
logging.debug("datafilezC={0:s}".format(datafilezC))

logging.debug("RUN CONCEPTS CSV")
datafilez, objectz, itemz = csv_split_and_group(node_concepts_file, outdir_set=node_outdir)
logging.debug("datafilez={0:s}".format(datafilez))

## CREATE OBJECT LIST WITH INFORMATION ON THE COLLECTION GROUPS GLEANED FROM COLLECTIONS AND CONCEPTS
all_obj = []
Cname_list = []
## CHECK COLLECTIONS OBJECTS AND GROUPS
if objectzC is None:
    logging.warning("No objectzC object found. Not adding into all_obj")    
else:
    for C in objectzC:
        if C.name not in Cname_list:
            Cname_list.append(C.name)
            all_obj.append(MixedCollectionObj(C.name, depth=C.depth, parent_dir=C.parent_dir, dir_path=C.dir_path, members=C.members))
    for C in itemzC:
        if C.name not in Cname_list:
            Cname_list.append(C.name)
            all_obj.append(MixedCollectionObj(C.name, depth=C.depth, parent_dir=C.parent_dir, dir_path=C.dir_path, members=None))
## CHECK CONCEPT OBJECTS FOR COLLECTIONS
if objectz is None:
    logging.warning("No objectz object found. Not adding into all_obj")
else:        
    for C in objectz:
        if C.name not in Cname_list:
            Cname_list.append(C.name)
            all_obj.append(MixedCollectionObj(C.name, depth=C.depth, parent_dir=C.parent_dir, dir_path=C.dir_path, members=None))
     
## SET CONCEPT MEMBERS FOR COLLECTION                 
for C2 in all_obj:
    fileDatax = ''.join([node,'NodeConcepts_',C2.name,'.csv'])
    if os.path.isfile(os.path.join(node_outdir,fileDatax)):
        C2.fileDataOut = os.path.join(node_outdir,fileDatax)
        C2.has_items = 1
        for cname in objectz:
            if cname.name == C2.name:
                C2.item_members = cname.members
    else:
        fileDatax = ''.join([node,'NodeConcepts_',C2.name,nowd,'.csv'])
        if os.path.isfile(os.path.join(node_outdir,fileDatax)):
            C2.fileDataOut = os.path.join(node_outdir,fileDatax)
            C2.has_items = 1
            for cname in objectz:
                if cname.name == C2.name:
                    C2.item_members = cname.members
        else:
            C2.fileDataOut = ''
            C2.has_items = 0
            C2.item_members = None
    logging.debug("COLLECTION {0:s} CONCEPTS={1:s}".format(C2.name, C2.item_members))

## SET THE INPUT BASE FOR RUNNING formatcollection.py AND formatregentry.py
syscodex_list = []    
try: uri_replace
except:
    #syscodex = ''.join(['outdir=',node_outdir,' log=',logfile])
    syscodex_list.append(''.join(['outdir=',node_outdir]))
    syscodex_list.append(''.join(['log=',logfile]))
else:
    logging.debug("uri_replace ={0:s}".format(uri_replace))
    if not uri_replace :
       #syscodex = ''.join(['outdir=',node_outdir,' log=',logfile])
        syscodex_list.append(''.join(['outdir=',node_outdir]))
        syscodex_list.append(''.join(['log=',logfile]))
    else:
        logging.warning("WARNING: Replacing URI using: {0:s}".format(uri_replace))
        #syscodex = ''.join(['outdir=',node_outdir,' uri_replace=',uri_replace,' log=',logfile])
        syscodex_list.append(''.join(['outdir=',node_outdir]))
        syscodex_list.append(''.join(['log=',logfile]))
        syscodex_list.append(''.join(['uri_replace=',uri_replace]))

logging.debug("syscodex_list={0:s}".format(syscodex_list))

## CREATE MULTI-CONTAINER FILES BY COLLECTION LEVEL
syscodeC_list = []
if datafilezC == node_collections_file:
    logging.warning("WARNING: Only one file produced by container split. No multi-container will be made.")
else:
    for collectf in datafilezC:
        if force_status == 1:            
            #syscodeC = ''.join([collectf,' ',syscodex,' status=',set_status])
            syscodeC_list.append(collectf)
            for item in syscodex_list:
                syscodeC_list.append(item)    
            syscodeC_list.append(''.join(['status=',set_status]))            
        else:
            #syscodeC = ''.join([collectf,' ',syscodex])
            syscodeC_list.append(collectf)
            for item in syscodex_list:
                syscodeC_list.append(item)
            
        syscode_listC = []
        syscode_listC.append('python')
        syscode_listC.append('formatcollection.py')
        for item in syscodeC_list:
            syscode_listC.append(item)
            
        logging.debug("syscode_listC={0:s}".format(syscode_listC))    
        #logging.debug("command={0:s}".format(syscodeC))
        
        try:
            #retcodeC = call(''.join(['python ','formatcollection.py ',syscodeC]), shell=True)
            retcodeC = call(syscode_listC, shell=True)
            if retcodeC == 0:
                 logging.debug("Child returned 0.")
            elif retcodeC < 0:
     	     logging.error("Child was terminated by signal {0:s}".format(str(retcodeC)))
            else:
     	     logging.error("Child returned {0:s}".format(str(retcodeC)))    
        except OSError as e:
     		logging.error("Execution failed: {0:s}".format(e))


depths_list = []
for C in all_obj:
    path_depth = C.depth
    if path_depth not in depths_list:
        depths_list.append(path_depth)    

## CREATE THE COLLECTION FILES FROM THE ORIGINAL SOURCE, CROSS-CHECKING INFORMATION FROM GROUPS
made_entries = []

startline = check_elements_startline(node_collections_file)
if startline > -1:
    (listK, Controlz_all) = read_elements(node_collections_file, firstline=startline)
    logging.debug("listK={0:s}".format(listK))
    controlkeyz = checkdict_keynames(listK) 
    logging.debug("controlkeyz={0:s}".format(controlkeyz))

    for nu, item in enumerate(Controlz_all):
        datadict = dict(zip(controlkeyz, item))
    
        iname = datadict['fullidset']    
        fpath = iname.strip('<>')      
        sname = os.path.basename(iname.strip("<>"))    
        bname = os.path.dirname(iname.strip("<>"))
        
        logging.debug("fpath={0:s}".format(fpath))
        logging.debug("sname={0:s}".format(sname))
        logging.debug("sname={0:s}".format(sname))
        logging.debug("bname={0:s}".format(bname))
    
        groupfound = 0
        syscode_list = []
        for C in all_obj:
            if sname == C.name and C.fileDataOut:
                groupfound = 1
                
                for item in syscodex_list:
                    syscode_list.append(item)
                syscode_list.append(''.join(['collection=',sname]))
                syscode_list.append(''.join(['registry=',bname]))
                syscode_list.append(''.join(['datafile=',C.fileDataOut]))
                if force_status == 1:
                    #syscode = ''.join([syscodex,' collection=',sname,' registry=',bname,' datafile=',C.fileDataOut,' status=',set_status])
                    syscode_list.append(''.join(['status=',set_status]))
                #else:    
                    #syscode = ''.join([syscodex,' collection=',sname,' registry=',bname,' datafile=',C.fileDataOut])
                    
                for k in controlkeyz:
                    if k == "desctxt" or k == "huread":
                        addy = ''.join([' ',k,'="',datadict[k],'"'])
                    elif k == "status":
                        if force_status == 0:
                            addy = ''.join([' ',k,"=",datadict[k]])
                    else:
                        addy = ''.join([' ',k,"=",datadict[k]])
                    syscode_list.append(addy)
                    #syscode = ''.join([syscode, addy])
                made_entries.append(sname)
                break        
        if groupfound == 0:    
            for item in syscodex_list:
                syscode_list.append(item)
            syscode_list.append(''.join(['collection=',sname]))
            syscode_list.append(''.join(['registry=',bname]))
            
            if force_status == 1:
                #syscode = ''.join([syscodex,' collection=',sname,' registry=',bname,' status=',set_status])
                syscode_list.append(''.join(['status=',set_status]))
            #else:    
                #syscode = ''.join([syscodex,' collection=',sname,' registry=',bname])
                
            for k in controlkeyz:
                if k == "desctxt" or k == "huread":
                    addy = ''.join([' ',k,'="',datadict[k],'"'])
                elif k == "status":
                    if force_status == 0:
                        addy = ''.join([' ',k,"=",datadict[k]])
                else:
                    addy = ''.join([' ',k,"=",datadict[k]])
                syscode_list.append(addy)    
                #syscode = ''.join([syscode, addy])
            made_entries.append(sname)
            logging.info("WARNING: no associated concept group found for collection={0:s}. Collection will not be assigned members.".format(sname))
            
        logging.debug("Writing item {0:s} in Control Dictionary={1:s}  for {2:s}".format(str(nu), sname, node_collections_file))        
        #logging.debug("command={0:s}".format(syscode))
        
        syscode_list_checked = []
        syscode_list_checked.append('python')
        syscode_list_checked.append('formatcollection.py')
        for item in syscode_list:
            itemx = check_call_input_str(item)
            syscode_list_checked.append(itemx)
            
       #syscode = check_call_input_str(syscode)        
        logging.debug("syscode_list_checked={0:s}".format(syscode_list_checked))
        
        try:
            #retcode = call(''.join(['python ','formatcollection.py ',syscode]), shell=True)
            retcode = call(syscode_list_checked, shell=True)
            if retcode == 0:
     		    logging.debug("Child returned 0.")
            elif retcode < 0:
     		    logging.error("Child was terminated by signal {0:s}".format(str(retcode)))
            else:
     		    logging.error("Child returned {0:s}".format(str(retcode)))    
        except OSError as e:
     		logging.error("Execution failed: {0:s}".format(e))

else:
    logging.warning("WARNING: NO GOOD POINT READING COLLECTIONS FILE. NOT CREATING COLLECTIONS.")

## CHECK THE ENTRIES MADE VS REQUESTED - AND MAKE ENTRIES FOR CONCEPTS IF THERE IS A CSV FILE BUT NO COLLECTION      
concepts_only = []
manual_entries = []
req_entries = []

for entry in all_obj:
    if entry.name not in req_entries:
        req_entries.append(entry.name)

for entry in req_entries:
    if entry not in made_entries:
        manual_entries.append(entry)
        
        conceptfilename = ''.join([node.lower(),'NodeConcepts_',entry,'.csv'])
        conceptfile = os.path.join(node_outdir,conceptfilename)
        
        if os.path.isfile(conceptfile):
            
            syscode_list_r = []
            syscode_list_r.append(conceptfile)
            syscode_list_r.append(''.join(['outname=',entry,'_entries']))
            for item in syscodex_list:
                syscode_list_r.append(item)
            
            if force_status == 1:            
                #syscode = ''.join([conceptfile,' outname=',entry,'_entries ',syscodex,' status=',set_status])
                syscode_list_r.append(''.join(['status=',set_status]))
            #else:
                #syscode = ''.join([conceptfile,' outname=',entry,'_entries ',syscodex])
            #logging.debug("command={0:s}".format(syscode))
            
            syscode_list_r_checked = []
            syscode_list_r_checked.append('python')
            syscode_list_r_checked.append('formatregentry.py')
            for item in syscode_list_r:
                syscode_list_r_checked.append(item)
                
            logging.debug("syscode_list_r_checked={0:s}".format(syscode_list_r_checked))    
                        
            try:
                #retcode = call(''.join(['python ','formatregentry.py ',syscode]), shell=True)
                retcode = call(syscode_list_r_checked, shell=True)
                if retcode == 0:
                     logging.debug("Child returned 0.")
                     concepts_only.append(entry) 
                elif retcode < 0:
         		     logging.error("Child was terminated by signal {0:s}".format(str(retcode)))
                else:
         		     logging.error("Child returned {0:s}".format(str(retcode)))    
            except OSError as e:
         		logging.error("Execution failed: {0:s}".format(e))
                
logging.info("FILES FOR THE FOLLOWING COLLECTION WERE MADE: {0:s}".format(made_entries))  
logging.warning("THE FOLLOWING COLLECTIONS WERE NOT MADE. THEY NEED TO BE MANUALLY CREATED: {0:s}".format(manual_entries))
logging.warning("THE FOLLOWING COLLECTION-GROUP HAD CONCEPT ENTRIES BUT NO COLLECTION INFO: {0:s}".format(concepts_only))

## CREATE DATA INFO FILE WITH INFORMATION ON THE COLLECTIONS CREATED 
with open(infofilefull,'a+') as infofilex:
#    infofilex.write('{0:s}\n'.format('**** CREATION DATA ****'))
#    infofilex.write("FILES FOR THE FOLLOWING COLLECTION WERE MADE: {0:s}\n".format(made_entries))
#    infofilex.write("THE FOLLOWING COLLECTIONS WERE NOT MADE. THEY NEED TO BE MANUALLY CREATED: {0:s}\n".format(manual_entries))
#    infofilex.write("THE FOLLOWING COLLECTION-GROUP HAD CONCEPT ENTRIES BUT NO COLLECTION INFO: {0:s}\n".format(concepts_only))
    
    infofilex.write('{0:s}\n'.format('**** COLLECTION INFO ****'))
    infofilex.write("{0:20s},{1:4s},{2:5s},{3:20s},{4:8s},{5:s}\n".format("COLLECTION","MADE","DEPTH","PARENT COLLECTION","CONCEPTS","CHILD COLLECTIONS"))
    
    for depthlv in range(min(depths_list), max(depths_list)+1):
        indepth = []
        for C in all_obj:
            if C.depth == depthlv:
                if C.parent_dir not in indepth:
                    indepth.append(C.parent_dir)
        for parent in indepth:
            for C in all_obj:
                if C.depth == depthlv and C.parent_dir == parent:
                    if C.members is not None:
                        memberlisty = '; '.join(C.members)
                    else:
                        memberlisty = None
        
                    if C.has_items == 1:
                        has_items_yn = 'yes'
                        itemslisty = '; '.join(C.item_members)
                    elif C.has_items == 0:
                        has_items_yn = 'no'
                        itemslisty = None
                    else:
                        has_items_yn = 'error'
                        itemslisty = None
                        
                    if C.name in made_entries:
                        collection_made = 'YES'
                    else:
                        collection_made = 'NO'

                    infofilex.write("{0:20s},{1:4s},{2:5s},{3:20s},{4:8s},{5:s}\n".format(C.name, collection_made, str(C.depth), C.parent_dir, has_items_yn, memberlisty))

    infofilex.write('{0:s}\n'.format(''))
    infofilex.write('{0:s}\n'.format('**** CONCEPT INFO ****'))
    infofilex.write("{0:20s},{1:s}\n".format("COLLECTION","LISTED CONCEPTS"))
    
    for depthlv in range(min(depths_list), max(depths_list)+1):
        indepth = []
        for C in all_obj:
            if C.depth == depthlv:
                if C.parent_dir not in indepth:
                    indepth.append(C.parent_dir)
        for parent in indepth:
            for C in all_obj:
                if C.depth == depthlv and C.parent_dir == parent:
                    if C.has_items == 1:
                        itemslisty = '; '.join(C.item_members)
                        infofilex.write("{0:20s},{1:s}\n".format(C.name, itemslisty))
                
logging.info("CODE COMPLETE")	
