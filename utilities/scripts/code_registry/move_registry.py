#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import requests

def authenticate(session, base, userid, pss):
    auth = session.post('{}/system/security/apilogin'.format(base),
                        data={'userid':userid,
                                'password':pss})
    #print auth.status_code
    if not auth.status_code == 200:
        raise ValueError('auth failed')

    return session

## THESE WILL BE REPLACED WITH READABLE DATA BUT USE FOR TESTING ----
regbase = 'https://codes.nws.noaa.gov/assist'
usernamex = 'admin'
userpassx = 'registry111'

regpath_old = 'https://codes.nws.noaa.gov/assist/StatPP/Data'
regpath_new = 'https://codes.nws.noaa.gov/assist'
reg_name = 'Time'
## ------------------------------------------------------------------

current_path = os.getcwd()
backup_filename = ''.join(['reg_backup_',reg_name,'.ttl'])
new_filename = ''.join(['reg_new_',reg_name,'.ttl'])
backup_file = os.path.join(current_path,backup_filename)
new_file = os.path.join(current_path,new_filename)

print "backup=",backup_file
print "new=",new_file

s = requests.Session()
s = authenticate(s, regbase, usernamex, userpassx)

headers = {'content-type': 'text/turtle'}

#registry_export = ''.join([regpath_old,'/_',reg_name,'?export']) 
registry_export = ''.join([regpath_old,'/',reg_name,'?export'])
registry_get = ''.join([regpath_old,'/',reg_name])

print "command=",registry_export

r = s.get(registry_export, auth=(usernamex, userpassx),
	      verify=False, headers=headers)

r2 = s.get(registry_get, auth=(usernamex, userpassx),
	      verify=False, headers=headers)

print("response={0:d}".format(r.status_code))
print("response2={0:d}".format(r2.status_code))

print r2.text.encode("utf-8")

if r.status_code == 200:
    print "GOT EXPORT"
      
    with open(backup_file, 'w+') as f1:
        f1.write(r.text.encode("utf-8"))
    print "BACKUP FILE WRITTEN"
else:
    "ERROR: EXPORT FAILED."
    print r.text

exit()

# =============================================================================
# ##
# ## OLD CODE USING IMPORT/EXPORT - DO NOT USE!!! 
# ##
# 
# registry_get = ''.join([regpath_old,'/_',reg_name,'?export']) 
# registry_put = ''.join([regpath_new,'/_',reg_name,'?import']) 
# 
# ## START SESSION AND LOGIN
# print "exporting registry command: " + registry_get
# print "importing registry command: " + registry_put
# 
# s = requests.Session()
# s = authenticate(s, regbase, usernamex, userpassx)
# 
# headers = {'content-type': 'text/turtle'}
# 
# r = s.get(registry_get, auth=(usernamex, userpassx),
# 	      verify=False, headers=headers)
# 
# print r.status_code
# 
# if r.status_code == 200:
#     print "GOT EXPORT"
# ##    print r.text	
#     newr = r.text.replace(regpath_old, regpath_new)
# ##    print newr
#     print "REPLACEMENT MADE" 
#     
#     with open(backup_file, 'w+') as f1:
#         f1.write(r.text)
#     print "BACKUP FILE WRITTEN"
# 
#     with open(new_file, 'w') as f2:
# 	f2.write(newr)
# 	
#     print "NEW FILE WRITTEN"
# 
# exit()
# 
# rnew = s.put(registry_put, auth=(usernamex, userpassx),
# 	    data=backup_file, verify=False, headers=headers)
# print rnew.status_code
# 
# =============================================================================
