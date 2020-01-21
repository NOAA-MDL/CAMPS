#!/usr/bin/env python
"""
    NAME: update_registry.py

    REQUIREMENTS: requests
                  campsregistry

    PURPOSE: To update code registry

    USEAGE:
    python update_registry.py [no input for interactive]
    python update_registry.py mode=[new, edit, container, collection, or patch] username=[username] pass=[password] ...
                              filename=[ttl file with register input](optional) filepath=[path to file](optional) ...
                              registry=[base registry uri] subregister=[subregister path](optional) 
                              itemname=[entity name to patch](used in "patch" and "replace" mode)
                              
    HISTORY:
    2019/07/24 - Stearns - first version started by Cassie.Stearns
    2019/07/26 - Stearns - first stable version tested and works for ttl input file (1 item)
	                       variable inputs 2 ways: by command line entry var=value or interactive
    2019/08/23 - Stearns - added in modes for new, collection, and patch 
    2019/08/26 - Stearns - added new mode: container (empty collection)
    2019/08/28 - Stearns - added new mode: edit
                           made changes to reading functions
    2019/08/29 - Stearns - updated logging statements and removed print statements
    2019/08/30 - Stearns - added first attempt at error handling
    2019/09/04 - Stearns - removed default registry; now error if not put in
    2019/09/06 - Stearns - added option to create nested collections and moved some functions to campsregistry.py
    2019/09/17 - Stearns - added loop options for new,edit,container,collection (USE: list of names with ,)
    2019/09/19 - Stearns - added edit-status option ("status")
    2019/09/23 - Stearns - changed order of interactive input
    2019/09/25 - Stearns - added edit options for containers/collections (edit_collection) and nested collections (edit_nested_container)
    2019/09/27 - Stearns - added option to retire an entry and replace it with another
                         - removed "container" option, as its function is better covered elsewhere
    2019/10/01 - Stearns - added (back) check if uri exists function and authenticate here instead of import from campsregistry.py
    2019/10/16 - Stearns - updated error handling, cleaned up code a little  

"""
import os
import sys
import requests
import logging

from datetime import datetime

from campsregistry import check_file_for_str
from campsregistry import checkmake_output_path
from campsregistry import check_datafile

from campsregistry import MissingInput
#from campsregistry import MissingInputFile

from campsregistry import FILEPATH_DEFAULT
from campsregistry import DATA_FILEPATH_DEFAULT

##
## INFO SET
##

## TIMESTAMP
nowd = datetime.now().strftime('%Y%m%d%H%M%S')

## SET LOG FILE
logdir = os.path.join(FILEPATH_DEFAULT,"logs")
checkmake_output_path(logdir)

logfile = os.path.join(logdir,''.join(['update_registry_',nowd,'.log']))
logging.basicConfig(filename=logfile,level=logging.DEBUG)

##
## FUNCTIONS 
##

## LOG IN
def authenticate(session, base, userid, pss):
    auth = session.post('{}/system/security/apilogin'.format(base),
                        data={'userid':userid,
                                'password':pss})	

    if not auth.status_code == 200:
        logging.critical("ERROR: Authorization Failed.")
        raise ValueError('auth failed')

    return session

# CHECK IF A URI EXISTS ALREADY. RETURNS 1=EXISTS AND IS GOOD; 0=NOT FOUND OR BAD RETURN 
def check_uri_exists(uri):
    uri_exists = 0 
 
    rtest=requests.get(uri)
    
    if rtest.status_code == 200:
        try: rtest.text
        except:    
	        logging.error("ERROR: No text retrieved. URI {0:s} cannot be read. Bad return.".format(uri))
	        uri_exists = 0
        else:
            rtest_str = str(rtest.text.encode("utf-8"))
            if "Not found (404)" in rtest_str:
                logging.debug("URI RETURNED TEXT=".format(rtest_str))
                logging.info("URI {0:s} Contains 404 NOT FOUND. Bad return.".format(uri))
                uri_exists = 0
            else:
	            logging.info("URI {0:s} exists! Good return.".format(uri))
	            uri_exists = 1
    else:
        logging.info("URI {0:s} NOT FOUND.".format(uri))
        uri_exists = 0

    return uri_exists 
  
## GET ARGUMENTS INTERACTIVELY 
def get_regargs_inter(update_modex):
      if update_modex == "patch" or update_modex == "replace":
          listK = ['update_mode','username','passwd','registry','subregister','filename','filepath','itemname']
      elif update_modex == "status":
          listK = ['update_mode','username','passwd','registry','subregister','itemname']
      else:
          listK = ['update_mode','username','passwd','registry','subregister','filename','filepath']

      listV = []
      listV.append([])
      listV[0].append(update_modex)
      listV[0].append(raw_input("user name:"))
      listV[0].append(raw_input("password:"))
      listV[0].append(raw_input("registry url (no sub-paths):"))
      listV[0].append(raw_input("registry subregister path (optional):"))    
      
      if update_modex != "status":
          if update_modex == "collection" or update_modex == "edit_collection":
              listV[0].append(raw_input("collection name:"))
          elif update_modex == "nested_collection" or update_modex == "edit_nested_collection":
    	      listV[0].append(raw_input("nested collection names (namea/nameb/namec):"))    
          else: 
              listV[0].append(raw_input("registry data file name (no path):"))
              
          listV[0].append(raw_input("path to data files (leave blank for default):")) 
      
      if update_modex == "patch" or update_modex == "status":
	      listV[0].append(raw_input("registry entry name:"))
    ##Note = in python 3 use input instead of raw_input
      
      logging.debug("listK={0:s}".format(listK))
      logging.debug("listV={0:s}".format(listV))

      inputz_dict=dict(zip(listK,listV[0]))
      return inputz_dict

## READ IN DATA FROM COMMAND LINE
def get_regargs_cmd(argvin):
      listK = []
      listV = []
      listV.append([])
    
      logging.debug("arguments read={0:s}".format(argvin))
      for ar in argvin:
    	  arsplit = ar.split("=")
          ## CORRECT INPUTS
          if arsplit[0] == "mode":
              arsplit[0] = "update_mode"
    	  elif arsplit[0] == "user":
    	      arsplit[0] = "username"
    	  elif arsplit[0] == "password":
    	      arsplit[0] = "passwd"
          elif arsplit[0] == "pass":
              arsplit[0] = "passwd"
          elif arsplit[0] == "item":
    	      arsplit[0] = "itemname"
          elif arsplit[0] == "data":
              arsplit[0] = "filename"
          elif arsplit[0] == "filedir":
              arsplit[0] = "filepath"

          ## MAKE LISTS
    	  listK.append(arsplit[0])
    	  listV[0].append(arsplit[1])

      logging.debug("listK={0:s}".format(listK))
      logging.debug("listV={0:s}".format(listV))
      
      inputz_dict=dict(zip(listK,listV[0]))
      logging.debug("inputz_dict={0:s}".format(inputz_dict))
      return inputz_dict

## CHECK THE ARGUMENTS DICTIONARY CONTENT 
def check_reg_args(input_dict):
    ## CHECK MODE (REQUIRED)
    if 'update_mode' not in input_dict.keys():
        logging.critical("ERROR: update_mode is required input! EXITING.")
        raise MissingInput('mode')
    else:
        update_mode = input_dict['update_mode']
    ## USER NAME (REQIURED)
    if 'username' not in input_dict.keys():
        logging.critical("ERROR: username is required input! EXITING.")
        raise MissingInput('user')
    else:
        usernamex = input_dict['username']
    ## PASSWORD (REQUIRED)
    if 'passwd' not in input_dict.keys():
        logging.critical("ERROR: password (pass=) is required input. EXITING.")
        raise MissingInput('passwd')
    else:
        userpassx = input_dict['passwd']
    ## REGISTRY PATH (REQUIRED)
    if 'registry' not in input_dict.keys():
        logging.critical("ERROR: Registry not set. This is needed information. EXITING")
        raise MissingInput('registry')
    else:    
        regbase = input_dict['registry']
        if 'subregister' in input_dict.keys():
            testsubreg = input_dict['subregister'].replace("'","")
            testsubreg = testsubreg.replace('"','')
            if testsubreg [-1] == "/":
                testsubreg = testsubreg[:-1]

            if testsubreg.isspace() or not testsubreg:
                regname = ''.join([regbase,'/'])
            else:	
	            regname = ''.join([regbase,'/',testsubreg,'/'])
        else:
	        regname = ''.join([regbase,'/'])
            
    ## DATA FILE OR COLLECTION NAME (REQUIRED FOR ALL BUT STATUS)
    if input_dict['update_mode'] == "status":
        data_list = ''
        file_path = ''
    elif input_dict['update_mode'] == "replace":
        if 'filename' not in input_dict.keys():
            data_list = []
            file_path = ''
    else:    
        if 'filename' not in input_dict.keys():
            if 'collection' not in input_dict.keys():
                logging.critical("ERROR: filename or collection (mode=collection or nested_collection) is required input! EXITING.")
                raise MissingInput('"filename" or "collection"')
            else:
                data_file_input = input_dict['collection']
        else: 
           	data_file_input = input_dict['filename'] 	

        ## READ data_file and transform into list
        data_list = data_file_input.split(",")

    ## DATA DIRECTORY (REQURIED, HAS DEFAULT)
    if 'filepath' not in input_dict.keys():
        logging.warning("File path for data not input. Checking default directory {0:s}".format(DATA_FILEPATH_DEFAULT))
        file_path = DATA_FILEPATH_DEFAULT
    elif input_dict['filepath'].isspace() or not input_dict['filepath']:
        logging.warning("File path for data not input. Checking default directory {0:s}".format(DATA_FILEPATH_DEFAULT))
        file_path = DATA_FILEPATH_DEFAULT
    else:    
        file_path = input_dict['filepath']
        
    return (update_mode, usernamex, userpassx, data_list, file_path, regbase, regname)

##
## RUN CODE
##

## READ INPUTS 

le = len(sys.argv)
if le < 2:
    logging.info("Getting inputs interactively")
    update_mode = raw_input("update mode:")	
    inputzd = get_regargs_inter(update_mode)   
elif le > 1:
    logging.info("using command-line inputs")
    inputzd = get_regargs_cmd(sys.argv[1:])
    
logging.debug("inputzd={0:s}".format(inputzd))    
    
(update_mode, usernamex, userpassx, data_list, file_path, regbase, regname) = check_reg_args(inputzd)

## PRINT OUT INPUT INFORMATION FOR LOGS 
logging.info("PARAMETERS USED:")
logging.info("mode(update_mode)={0:s}".format(update_mode))
logging.info("username={0:s}".format(usernamex))
logging.info("data (data_list)={0:s}".format(data_list))
logging.info("data path(file_path)={0:s}".format(file_path))
logging.info("register base (regbase)={0:s}".format(regbase))
logging.info("registry full path(regname)={0:s}".format(regname))

if 'itemname' in inputzd.keys():
    logging.info("item(s)={0:s}".format(inputzd['itemname']))

## START SESSION AND LOGIN
s = requests.Session()
s = authenticate(s, regbase, usernamex, userpassx) 

## CREATE NEW ITEMS FOR EXISTING REGISTRY
if update_mode == "new" or update_mode == "add":
    
    for data_file in data_list:
        
        logging.info("Adding new item(s) to registry {0:s} from file {1:s}".format(regname,data_file))
        data_file_full = os.path.join(file_path,data_file)
        err = check_datafile(data_file_full, failcmd='continue')
        
        if err == 0:            
            with open(data_file_full,'rb') as payload:
                headers = {'content-type': 'text/turtle'}
                r = s.post(regname, auth=(usernamex, userpassx),
                              data=payload, verify=False, headers=headers)
                
                print("{0:s} {1:d}".format(data_file, r.status_code))
        
            if r.status_code == 201:
            	logging.info("{0:s}: Success!".format(str(r.status_code)))
            else:
                if not check_file_for_str(data_file,regname):
            	    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regname))
                try: 
            	    r.text
                except: 
            	    logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r.status_code)))
                else:	
            	    logging.error("ERROR: {0:s}: {1:s}".format(str(r.status_code), r.text))
                    
        else:
            logging.error("ERROR: File not found. NO ENTRY FOR data_file={0:s} CREATED.".format(data_file))

## EDIT ITEMS IN EXISTING REGISTRY
elif update_mode == "edit":
    
    for data_file in data_list:
       
        logging.info("Editing item(s) in registry {0:s} from file {1:s}".format(regname,data_file))
        regeditname = ''.join([regname,'?edit'])
        data_file_full = os.path.join(file_path,data_file)
        err = check_datafile(data_file_full, failcmd='continue')
        
        if err == 0:            
            with open(data_file_full,'rb') as payload:
                headers = {'content-type': 'text/turtle'}
                r = s.post(regeditname, auth=(usernamex, userpassx),
                              data=payload, verify=False, headers=headers)
                
                print("{0:s} {1:d}".format(data_file, r.status_code))
        
            if r.status_code == 204:
        	    logging.info("{0:s}: Success!".format(str(r.status_code)))
            else:
                if not check_file_for_str(data_file,regname):
            	    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regname))
                try: 
            	    r.text
                except: 
            	    logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r.status_code)))
                else:	
            	    logging.error("ERROR: {0:s}: {1:s}".format(str(r.status_code), r.text))
                
        else:
            logging.error("ERROR: File not found. NO ENTRY FOR data_file={0:s} CREATED.".format(data_file))

## MANIPULATE STATUS OF CURRENT ENTRIES
elif update_mode == "status":    
    if 'status' not in inputzd.keys():
        logging.critical("ERROR: status not specified. Cannot set status of files. EXITING.")
        raise MissingInput('status')
        
    if 'itemname' in inputzd.keys():
       item_list = inputzd['itemname'].split(",")
   
    try: item_list
    except:
        logging.warning("WARNING: No item list input. Changing all immidiate members of {0:s} to status={1:s}".format(regname[:-1],inputzd['status']))
        regstatname = ''.join([regname[:-1],'?update&status=',inputzd['status']])        
        r = s.post(regstatname, auth=(usernamex, userpassx))            
        print("{0:s} {1:d}".format("status return=", r.status_code))         
    else:
        for item in item_list:  
            logging.info("Changing {0:s} in {1:s} to status={2:s}".format(item,regname[:-1],inputzd['status']))
            regstatname = ''.join([regname[:-1],'/_',item,'?update&status=',inputzd['status']])            
            r = s.post(regstatname, auth=(usernamex, userpassx))                
            print("{0:s} {1:d}".format(item, r.status_code))

## REPLACE ONE ENTRY WITH ANOTHER (RETIRE THE EXISTING ENTRY)
## NOTE: Itemname must have the format old1:new1,old2:new2
## All items in the list must be in the same level 
elif update_mode == "replace":

    if 'itemname' in inputzd.keys():
        item_list = inputzd['itemname'].split(",")
    else:
        logging.critical("ERROR: 'item=old_item:new_item' must be input for a registry entry replacement!")
    	raise MissingInput('item') 
    
    # Loop through items/replacements
    cnt = -1
    for item in item_list:
        cnt += 1
        itemsplit = item.split(":")
        old_item = itemsplit[0]
        new_item = itemsplit[1]
        logging.info("old entry={0:s}, new entry={1:s}".format(old_item, new_item))
        
        urlname = ''.join([regname,new_item])
        logging.debug("urlname={0:s}".format(urlname))
        uri_exists = check_uri_exists(urlname)
        logging.debug("uri_exists={0:d}".format(uri_exists))
        	
        # IF NEW ENTRY EXISTS, MAKE REPLACEMENT. OTHERWISE, LOAD FILE WITH DATA FIRST THEN CHECK AGAIN
        if uri_exists == 1:
            logging.info("retiring entry {0:s} and replacing with {1:s}".format(old_item, new_item))
            replacecode = ''.join([regname,'_',old_item,'?update&status=superseded&successor=',urlname])
            logging.debug("command={0:s}".format(replacecode))
            r = s.post(replacecode, auth=(usernamex, userpassx))
            print("{0:s} {1:d}".format(data_file, r.status_code))
                        
    	else:    
    	    logging.warning("WARNING: Entry {0:s} does not exist. It must be made before {1:s} can be replaced! Attempting now.".format(new_item, old_item))
            try: data_list[cnt]
            except: 
                logging.error("No data file input. NO ITEM REPLACEMENT MADE FOR {0:s}".format(old_item))
                continue
    	    data_file = data_list[cnt]
    	    data_file_full = os.path.join(file_path,data_file)
    	    logging.info("Adding entry for {0:s} data frome file={1:s}".format(new_item, data_file_full))
    	    err = check_datafile(data_file_full, failcmd='continue')
    	    if err == 0:
                logging.info("Adding new item(s) to registry {0:s} from file {1:s}".format(regname,data_file_full))
                
                with open(data_file_full,'rb') as payload:
                    headers = {'content-type': 'text/turtle'}
                    r1 = s.post(regname, auth=(usernamex, userpassx),
        				  data=payload, verify=False, headers=headers)
                    print("{0:s} {1:d}".format(data_file, r1.status_code))
                    
                if r1.status_code == 201:
                    logging.info("{0:d}: Upload Success!".format(r1.status_code))
                    uri_exist2 = check_uri_exists(urlname)
                    
                    if uri_exist2 == 1:
                        logging.info("retiring entry {0:s} and replacing with {1:s}".format(old_item, new_item))
                        replacecode = ''.join([regname,'_',old_item,'?update&status=superseded&successor=',urlname])
                        logging.debug("command={0:s}".format(replacecode))
                        r2 = s.post(replacecode, auth=(usernamex, userpassx))
                        print("{0:s} {1:d}".format(old_item, r2.status_code))
                    else:
                        logging.error("ERROR: Something went wrong with entry upload for {0:s}. Check datafile={1:s}. NO ITEM REPLACEMENT MADE FOR {2:s}".format(new_item, data_file, old_item))

                else:
                    print("ERROR: Something went wrong with entry upload for {0:s}. NO ITEM REPLACEMENT MADE FOR {1:s}".format(new_item, old_item))
                    xc = check_file_for_str(data_file_full,regname)
                    if xc is None:
                        logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regname))
                        try: 
            			    r1.text
                        except: 
            			    logging.error("ERROR: return code {0:d}. No readable error text.".format(r1.status_code))
                        else:	
            			    logging.error("ERROR: {0:s}: {1:s}".format(str(r1.status_code), r1.text))
            else:
                logging.error("ERROR: file {0:s} Cannot be read. NO REPLACEMENT MDADE FOR {1:s}".format(data_file_full, old_item))

## CREATE NEW NESTED COLLECTIONS AND POPULATE IF INDICATED
elif update_mode == "nested_collection" or update_mode == "edit_nested_collection":
    
    data_file = str(data_list[0])
    collection_set = data_file.split("/")
    logging.debug("collection_set={0:s}".format(collection_set))

    for lvl, collectname in enumerate(collection_set):
           
        regcollect = ''.join([regname,collectname,'/'])   
        logging.debug("regcollect= {0:s}".format(regcollect))
    
        collection_file_name = ''.join([collectname,'_container.ttl'])
        contents_file_name = ''.join([collectname,'_entries.ttl'])
        collection_file = os.path.join(file_path,collection_file_name)
        contents_file = os.path.join(file_path,contents_file_name)
        
        if update_mode == "nested_collection":
            command_collect = regname
            command_concept = regcollect
        elif update_mode == "edit_nested_collection":
            command_collect = ''.join([regname,'?edit'])
            command_concept = ''.join([regcollect,'?edit'])
    	
        ## OPEN DATA FILE AND SEND TO REGISTRY
        logging.info("Adding new container (subregister) {0:s} from data in {1:s}".format(collectname,collection_file))
    
        check_datafile(collection_file)
        with open(collection_file,'rb') as payload:
            headers = {'content-type': 'text/turtle'}
            r = s.post(command_collect, auth=(usernamex, userpassx),
                          data=payload, verify=False, headers=headers)
            print("{0:s} {1:d}".format(collectname, r.status_code))
            
        if r.status_code == 201 or r.status_code == 204:
            logging.info("Collection container created! Adding entries to collection {0:s} from file {1:s}".format(collectname,contents_file))    
            errchk = check_datafile(contents_file, failcmd='continue')
            
            if errchk == 0:
                with open(contents_file, 'rb') as payload2:
                    r2 = s.post(command_concept, auth=(usernamex, userpassx),
                              data=payload2, verify=False, headers=headers)
                    print("{0:s}_items {1:d}".format(collectname, r2.status_code))
            else:
                logging.error("ERROR: Could not find or open file {0:s}. NOT ADDING ENTRIES TO COLLECTION {1:s}".format(contents_file, collectname))    
                logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                regname = ''.join([regname,collectname,'/'])
                continue     
    
            if r2.status_code == 201 or r2.status_code == 204:
                logging.info("{0:s}: Sucess! Entries added.".format(str(r2.status_code)))                
            elif r2.status_code == 404:
                logging.error("{0:s}: Error finding registry {1:s}".format(str(r2.status_code),regcollect))    
                if not check_file_for_str(contents_file,regcollect):
                    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))
                
                logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                regname = ''.join([regname,collectname,'/'])
                continue     
            else:
                if not check_file_for_str(contents_file,regcollect):
                    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))    
                try:
                    r2.text
                except:
                    logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r2.status_code)))
                    logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                    regname = ''.join([regname,collectname,'/'])
                    continue 
                else:
                    logging.error("ERROR: {0:s}: {1:s}".format(str(r2.status_code), r2.text))  
                    logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                    regname = ''.join([regname,collectname,'/'])
                    continue 
      
        elif r.status_code == 403:
            logging.warning("Collection container already exists! Adding entries to collection {0:s} from file {1:s}".format(collectname,contents_file))
            ## OPEN DATA FILE AND SEND TO REGISTRY
            errchk = check_datafile(contents_file, failcmd='continue')
            if errchk == 0:
                with open(contents_file, 'rb') as payload2:
                    r2 = s.post(command_concept, auth=(usernamex, userpassx),
                              data=payload2, verify=False, headers=headers)
                    print("{0:s}_items {1:d}".format(collectname, r2.status_code))
            else:
                logging.error("ERROR: Could not find or open file {0:s}. NOT ADDING ENTRIES TO COLLECTION {1:s}".format(contents_file, collectname))    
                logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                regname = ''.join([regname,collectname,'/'])
                continue 
           
            if r2.status_code == 201 or r2.status_code == 204:
                logging.info("{0:s}: Sucess! Entries added.".format(str(r2.status_code)))                    
            elif r2.status_code == 404:
                logging.error("{0:s}: Error finding registry {1:s}".format(str(r2.status_code),regcollect))    
                if not check_file_for_str(contents_file,regcollect):
                    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))    
                logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                regname = ''.join([regname,collectname,'/'])
                continue                     
            else:
                if not check_file_for_str(contents_file,regcollect):
                    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))
     
                try:
                    r2.text
                except:
                    logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r2.status_code)))
                    logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                    regname = ''.join([regname,collectname,'/'])
                    continue
                else:
                    logging.error("ERROR: {0:s}: {1:s}".format(str(r2.status_code), r2.text))  
                    logging.warning("WARNING: Entries not added. Continuing with code anyway.")    
                    regname = ''.join([regname,collectname,'/'])
                    continue 
    
        else:
            if not check_file_for_str(collection_file,regname):
                logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regname))
    
            try:
                r.text
            except:
                logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r.status_code)))
            else:
                logging.error("ERROR: {0:s}: {1:s}".format(str(r.status_code), r.text))  
      
    	# UPDATE CODES      
    	regname = ''.join([regname,collectname,'/'])

## CREATE NEW COLLECTION SUBREGISTER AND POPULATE WITH ITEMS    
elif update_mode == "collection" or update_mode == "edit_collection":
    
    for data_file in data_list: 
            
        logging.info("Adding new collection of item(s) to registry {0:s}".format(regname)) 
        collectname = data_file
        logging.debug("collectname={0:s}".format(collectname))

        regcollect = ''.join([regname,collectname,'/'])   
        logging.debug("regcollect= {0:s}".format(regcollect))
    
        collection_file_name = ''.join([collectname,'_container.ttl'])
        contents_file_name = ''.join([collectname,'_entries.ttl'])
        collection_file = os.path.join(file_path,collection_file_name)
        contents_file = os.path.join(file_path,contents_file_name)
        
        if update_mode == "collection":
            command_collect = regname
            command_concept = regcollect
        elif update_mode == "edit_collection":
            command_collect = ''.join([regname,'?edit'])
            command_concept = ''.join([regcollect,'?edit'])
    
        logging.info("Adding new container (subregister) {0:s} from data in {1:s}".format(collectname,collection_file))    
        err = check_datafile(collection_file, failcmd='continue')
        if err == 0:
            
            with open(collection_file,'rb') as payload:
                headers = {'content-type': 'text/turtle'}
                r = s.post(command_collect, auth=(usernamex, userpassx),
                              data=payload, verify=False, headers=headers)                
                print("{0:s} {1:d}".format(collectname, r.status_code))
                
            if r.status_code == 201 or r.status_code == 204:                
                logging.info("Collection container created! Adding entries to collection {0:s} from file {1:s}".format(collectname,contents_file))
                err2 = check_datafile(contents_file, failcmd='continue')
                
                if err2 == 0:
                    with open(contents_file, 'rb') as payload2:
                        r2 = s.post(command_concept, auth=(usernamex, userpassx),
                                  data=payload2, verify=False, headers=headers)
                        print("{0:s}_items {1:d}".format(collectname, r2.status_code))
                        
                        if r2.status_code == 201 or r2.status_code == 204:
                    	    logging.info("{0:s}: Sucess! Entries added.".format(str(r2.status_code)))                            
                        elif r2.status_code == 404:
                            logging.error("{0:s}: Error finding registry {1:s}".format(str(r2.status_code),regcollect))
                            if not check_file_for_str(contents_file,regcollect):
                                logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))                
                        else:
                            if not check_file_for_str(contents_file,regcollect):
                                logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))
                            try:
                                r2.text
                            except:
                                logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r2.status_code)))
                            else:
                                logging.error("ERROR: {0:s}: {1:s}".format(str(r2.status_code), r2.text))
                else:
                    logging.error("ERROR: File not found. NO ENTRY FOR data_file={0:s} CREATED.".format(contents_file))
        	           
            elif r.status_code == 403:                
                logging.warning("Collection container already exists! Adding entries to collection {0:s} from file {1:s}".format(collectname,contents_file))
                err2 = check_datafile(contents_file, failcmd='continue')
                
                if err2 == 0:                    
                    with open(contents_file, 'rb') as payload2:
                        r2 = s.post(command_concept, auth=(usernamex, userpassx),
                                  data=payload2, verify=False, headers=headers)
                        print("{0:s}_items {1:d}".format(collectname, r2.status_code))
                        
                        if r2.status_code == 201 or r2.status_code == 204:
                    	    logging.info("{0:s}: Sucess! Entries added.".format(str(r2.status_code)))                            
                        elif r2.status_code == 404:
                            logging.error("{0:s}: Error finding registry {1:s}".format(str(r2.status_code),regcollect))
                            if not check_file_for_str(contents_file,regcollect):
                                logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))                                
                        else:
                            if not check_file_for_str(contents_file,regcollect):
                                logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regcollect))
                            try:
                                r2.text
                            except:
                                logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r2.status_code)))
                            else:
                                logging.error("ERROR: {0:s}: {1:s}".format(str(r2.status_code), r2.text))  
                                
                else:
                    logging.error("ERROR: File not found. NO ENTRY FOR data_file={0:s} CREATED.".format(contents_file))
        
            else:
                if not check_file_for_str(collection_file,regname):
                    logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regname))
                try:
                    r.text
                except:
                    logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r.status_code)))
                else:
                    logging.error("ERROR: {0:s}: {1:s}".format(str(r.status_code), r.text))  

## PATCH EXISTING ITEM IN EXISTING ENTRY (SINGLE ITEM, MUST BE SPECIFIED)
elif update_mode == "patch":
    
    data_file = data_list[0]
    data_file_full = os.path.join(file_path,data_file)
    if 'itemname' not in inputzd.keys():
	    logging.critical("ERROR: item to update not input. Exiting.")
	    raise MissingInput('item')
    
    regitem = '/'.join([regname,inputzd['itemname']]) 	    
    logging.info("Editing registry item {0:s}".format(regitem)) 

    ## OPEN DATA FILE AND SEND TO REGISTRY
    check_datafile(data_file_full)
    with open(data_file_full,'rb') as payload:
        headers = {'content-type': 'text/turtle'}
        r = s.patch(regitem, auth=(usernamex, userpassx),
                      data=payload, verify=False, headers=headers)
        print("status return= {1:d}".format(r.status_code))
	   
    if r.status_code == 204:
	    logging.info("{0:s}: Success!".format(str(r.status_code)))
    else:
	    if not check_file_for_str(data_file,regname):
	        logging.warning("Check url paths in data file in data file! ATTEMPTED PATH={0:s}".format(regname))
	    try: 
	        r.text
	    except: 
	        logging.error("ERROR: return code {0:s}. No readable error text.".format(str(r.status_code)))
	    else:	
	        logging.error("ERROR: {0:s}: {1:s}".format(str(r.status_code), r.text))

## IF UNKNOWN MODE - ERROR
else:
    logging.critical("ERROR: update mode not recognized! Input was: {0:s} . Acceptable inputs are: 'new', 'edit', 'collection', 'edit_collection', 'nested_collection', 'edit_nested_collection', 'replace', or 'patch'".format(update_mode))
    print("ERROR: update mode not recognized! Input was: {0:s} . Acceptable inputs are: 'new', 'edit', 'collection', 'edit_collection', 'nested_collection', 'edit_nested_collection', 'replace', or 'patch'".format(update_mode))

logging.info("CODE COMPLETE.")
exit()    
