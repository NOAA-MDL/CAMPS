#!/usr/bin/env python
"""
    makestationtbl.py

    HISTORY:
	2018/06/28 - first version created Cassie.Stearns

    PURPOSE: 
	read in a csv of station information and format it into a station table usable by MOS-suite software
    
    USAGE:
      INPUTS: input-delimited-textfile delmiter column-data-type-list* OPTIONAL:output-file-name
      EXAMPLE: "DevList_2018_NBMtext.csv , ID,name,state,lat,lon,elev,time_zone,obs,taf,info,info,info" 
      
      column-data-type-list is a comma-delimited list describing the type of data in each column as they appear in the INPUT file. 
        
      The following data types MUST be present for good output: 
        ID 
        name 
        elev 
        lat 
        lon

      The data types correlate to the following columns numbers and data in a mos2000 station table (for more information see section 10 of OFFICENOTE 00-1 
        https://www.weather.gov/media/mdl/TDL_OfficeNote00-1.pdf). 

      columns with a data type not corresponding to a MOS2000 table column (i.e. are not listed below - like "taf" and "obs" in Example above) will be treated as comments and appended
        to the information in the final column 

       ID 		= 1 = station identification number/call sign (CCALL)
       old_ID 		= 2 = old identification number (CCALLS)
       name 		= 3 = long name/location of the station (NAME)
       state 		= 4 = 2-character state or country code for station location (NAME)
       wmo_block 	= 5 = WMO block/station number plus ID used by U.S. Air Force and NCEP. (NBLOCK)
       elev 		= 6 = station elevation (NELEV)
       lat 		= 7 = station latitude (SLAT)
       lon 		= 8 = station longitude (SLON)
       time_zone 	= 9 = station time zone (from UTC - no daylight times)(ITIMEZ)
       station_type 	= 10 = type of observations (ITYPE)
       closed_status 	= 11 = whether station has been closed and its ID reused (OPEN)
       old_ID1 		= 12 = call letters or ICAO identifiers used to link the station with past reporting stations (CCALLK1)
       old_ID2 		= 13 = additional call letters or ICAO IDs (CCALLK2)
       old_ID3 		= 14 = additional call letters or ICAO IDs (CCALLK3)
       old_ID4 		= 15 = additional call letters or ICAO IDs (CCALLK4)
       first_date 	= 16 = date of first data (if known) YYYYMMDDHH (IDATE)
       WBAN_number 	= 17 = The 5-digit WBAN number (IWBAN)
       reserved 	= 18 = This is left blank (IBLANK)
       info 		= 19 = Notes and comments about the station. Data from any column with a data type not listed here will be added to this (COMENT)
      
"""
import os, sys
import csv
import pytz
import datetime 

# SET TIMESTAMP
datestamp = datetime.datetime.today().strftime('%m/%Y') 
filestamp = os.path.basename(__file__)
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# DEFINE FUNCTIONS 
def getdata(lookname,d,le):
  err = 0
  if len(d[lookname]) == 1:
    outdat = row[d[lookname][0]]
  elif len(d[lookname])> 1:
    outstr = ''
    for x in range(0,len(d[lookname])-1):
      if (outstr.strip() != ''):
        outstr = outstr + ';' + row[d[lookname][x]].strip()
      else:
        outstr = outstr + row[d[lookname][x]].strip()
    outdat = outstr  
  else: 
    outdat = ''
  if lookname == 'time_zone':
    outdat,err = checktimezone(outdat)
  outdat = outdat.upper()
  if isinstance(le,int):
    if len(outdat) > le:
      outdat = outdat[:le] 
  else: 
    if len(outdat) > le[lookname]:
      outdat = outdat[:le[lookname]]  
  return outdat,err

def makeprintlist(inlist,inform):
  printerstr = ''
  for i in inlist:
    if len(inform) == 1:
      printlen = '{' + i + ':' + inform + '}:'
    else:
      printlen = '{' + i + ':' + str(inform[i]) + '}:'
    printerstr = printerstr + printlen 
  printerstr = printerstr + '\n'
  return printerstr 

def checklat(inlat):
  err = 0
  if isinstance(inlat,str) == True:
     try:
       inlatN = float(inlat)
     except ValueError:
       dirz=inlat[:1]
       if dirz == 'N':
         inlatNx = inlat[1:]
       elif dirz == 'S':
         inlatNx = '-'+inlat[1:]
       else:
         err = 1
         print("ERROR: invalid latitude input=" + inlat)
         outlat = inlat
         return outlat, err
       try:
         inlatN = float(inlatNx)
       except ValueError:
         err = 1
         print("ERROR: invalid latitude input=" + inlat)
         outlat = inlat
         return outlat, err
  elif isinstance(inlat,int) == True:
     inlatN = float(inlat)
  elif isinstance(inlat,float) == True:
     inlatN = inlat
  if inlatN >= 0 and inlatN <= 90:
     outlat = "N{0:07.4f}".format(inlatN)
  if inlatN < 0 and inlatN >= -90:
     inlatN = inlatN * -1.
     outlat = "S{0:07.4f}".format(inlatN)
  return outlat,err

def checklon(inlon):
  err = 0
  if isinstance(inlon,str) == True:
     try:
       inlonN = float(inlon)
     except ValueError:
       dirz=inlon[:1]
       if dirz == 'E':
         inlonNx = inlon[1:]
       elif dirz == 'W':
         inlonNx = '-'+inlon[1:]
       else:
         err = 1
         print("ERROR: invalid longitude input=" + inlon)
         outlon = inlon
         return outlon, err
       try:
         inlonN = float(inlonNx)
       except ValueError:
         err = 1
         print("ERROR: invalid longitude input=" + inlon)
         outlon = inlon
         return outlon, err
  elif isinstance(inlon,int) == True:
     inlonN = float(inlon)
  elif isinstance(inlon,float) == True:
     inlonN = inlon
  if inlonN >= 0 and inlonN <= 180:
     outlon = "E{0:08.4f}".format(inlonN)
  if inlonN < 0 and inlonN >= -180:
     inlonN = inlonN * -1.
     outlon = "W{0:08.4f}".format(inlonN)
  return outlon,err

def checktimezone(intimez):
  ustimedict = {'AST':'Canada/Atlantic','EST':'US/Eastern','EDT':'US/Eastern','CST':'US/Central','CDT':'US/Central','MST':'US/Mountain','MDT':'US/Mountain','PST':'US/Pacific','PDT':'US/Pacific','AKST':'US/Alaska','AKDT':'US/Alaska','HST':'US/Hawaii','HDT':'US/Hawaii','HAST':'US/Aleutian','HADT':'US/Aleutian','SST':'US/Samoa','GST':'Pacific/Guam','CHST':'Pacific/Guam','WAKT':'Pacific/Wake'}
  ustimedict2 = {'Atlantic':'Canada/Atlantic','Eastern':'US/Eastern','Central':'US/Central','Mountain':'US/Mountain','Pacific':'US/Pacific','Alaska':'US/Alaska','Hawaii':'US/Hawaii','Aleutian':'US/Aleutian','Samoa':'US/Samoa','Guam':'Pacific/Guam','Chamorro':'Pacific/Guam','Wake':'Pacific/Wake'}
  err = 0
  if isinstance(intimez,str) == False:
    timezo0 = float(intimez)
  else:
    try:
      timezo0 = float(intimez)
    except ValueError:
       intimez = intimez.strip()
       if intimez == "":
         print("ERROR: Input time zone is blank! Need to Calculate the time zone from lat/lon!")
         timezo = " "
         err = 1
         return timezo,err
       else:
         chk0 = intimez in pytz.all_timezones
         if chk0 == True:
           timezonename = intimez
         else:
           intimezC = intimez.capitalize()
           chk1 = intimezC in pytz.all_timezones
           if chk1 == True:
             timezonename = intimezC
           else:
             try:
               name0 = ustimedict2[intimezC]
               chk2 = name0 in pytz.all_timezones
             except KeyError:
               chk2 = False             
             if chk2 == True:
               timezonename = name0
             else:
               try:
                 nameA = ustimedict[intimez.upper()]
                 chk3 = nameA in pytz.all_timezones
               except KeyError:
                 chk3 = False
                 pass
               if chk3 == True:
                 timezonename = nameA
               else:
                 print("ERROR: invalid time zone input=" + intimez)
                 err = 1
                 timezo = intimez
                 return timezo,err
         timezoX = pytz.timezone(timezonename).localize(datetime.datetime(2011,1,1)).strftime('%z')
         timezo0 = float(timezoX)/100.
    timezo = "{0:3.0f}".format(timezo0)
    tzchk = float(timezo)
    if tzchk > -12 and tzchk < 13:
      timezo = str(timezo)
      return timezo,err     
    else: 
      print("ERROR: invalid time zone input=" + intimez)
      timezo = intimez
      err = 1
      return timezo,err

# MAKE DICTIONARY OF MAX LENGTHS FOR EACH COLUMN
le={'ID':8,'old_ID':8,'name':20,'state':2,'wmo_block':6,'elev':5,'lat':8,'lon':9,'time_zone':3,'station_type':1,'closed_status':1,'old_ID1':8,'old_ID2':8,'old_ID3':8,'old_ID4':8,'first_date':10,'WBAN_number':5,'reserved':10,'info':70}
# DICTIONARY OF PRINT FORMATS 
colform={'ID':'8s','old_ID':'8s','name':'20s','state':'2s','wmo_block':'6s','elev':'5.0f','lat':'8s','lon':'9s','time_zone':'3.0f','station_type':'1s','closed_status':'1s','old_ID1':'8s','old_ID2':'8s','old_ID3':'8s','old_ID4':'8s','first_date':'10s','WBAN_number':'5s','reserved':'10s','info':'70s'}
# LIST OF THE OUTPUTS - ORDER WILL MATCH OUTPUT ORDER!
collist = ['ID','old_ID','name','state','wmo_block','elev','lat','lon','time_zone','station_type','closed_status','old_ID1','old_ID2','old_ID3','old_ID4','first_date','WBAN_number','reserved','info']
# LIST OF INPUTS THAT CANNOT BE LISTED MORE THAN ONCE AND CANNOT BE BLANK
collist_needed=['name','ID','elev','lat','lon']

# GET THE FILE AND THE ORDER OF ARGUMENTS
infile = sys.argv[1]
indelim = sys.argv[2]
inlist = sys.argv[3]
if len(sys.argv) > 4:
  outfilein = sys.argv[4]
else:
  outfilein = 'outfile.txt'

outfileerrname = outfilein + '.err'
inlistarr = inlist.split(',')

# IF OUTPUT FILES EXIST, RENAME
if os.path.isfile(outfilein):
  print("ALERT: output file " + outfilein + " already exists! Renaming output file to " + outfilein + '.out_' + timestamp) 
  outfilein = outfilein + '.out_' + timestamp
if os.path.isfile(outfileerrname):
  print("ALERT: error file " + outfileerrname + " already exists! Renaming error file to " + outfileerrname + '.out_' + timestamp) 
  outfileerrname = outfileerrname + '.out_' + timestamp 

# FIND THE INPUT LOCATIONS FOR ALL WANTED OUTPUTS
d={}
for col in collist:
    index = [i for i,x in enumerate(inlistarr) if x == col]
    d[col] = index

# FIND ANY EXTRA ENTRIES AND ADD THEM TO INFO
inot = 0
extrastuff = [];
dx={};
for entri in inlistarr:
    idx = [j for j,y in enumerate(inlistarr) if y == entri]
    if entri not in collist:
       inot = inot + 1
       extrastuff.append(entri)
       dx[entri] = idx 

# CHECK TO MAKE SURE ALL NEEDED VARIABLES ARE PRESENT AND ONLY IN 1 INPUT COLUMN
for needed in collist_needed:
#    print(needed + 'len=' + str(len(d[needed])))
    if (len(d[needed])<1):
      print("ERROR: station table needs input for " + needed + "! Exiting.")
      sys.exit(1)
    elif (len(d[needed])>1):
      print("ERROR: station table requires 1 entry for " + needed + "! Exiting.")
      sys.exit(1)
          
# READ THE INPUT DATA BY ROW AND CREATE OUTPUT DATA LIST TO EITHER PRINT TO OUTPUT(IF GOOD) OR TO ERROR FILE (IF BAD)
with open(outfileerrname,'w') as outfileerr:
  with open(outfilein,'w') as outfile:
    with open(infile, 'r') as f:

      reader = csv.reader(f, delimiter=indelim, quoting=csv.QUOTE_NONE)
      i=0
      for row in reader:
        i= i + 1
        print("looking at row: " + str(i))
        out = {}
        err = 0
        for indatae in collist:
          out[indatae],err0 = getdata(indatae,d,le)
          err = err+err0
        out['lat'],err1 = checklat(out['lat'])
        err = err + err1
        out['lon'],err2 = checklon(out['lon'])
        err = err + err2

# WORK ON THIS LATER IF I CAN FIND CODES TO CONVERT LAT/LON TO TIMEZONE       
#        if out['time_zone'].strip() == "":
#          out['time_zone'],err3 = gettimezone(out['lat'],out['lon'])       
#          err = err + err3 
#######################################################################

# CHECK TO MAKE SURE ALL NEEDED COLUMNS ARE FILLED         
        for musthave in collist_needed:
          if out[musthave].strip() == "":
            print("ERROR: Needed input '" + musthave + "' is MISSING!")
            err = err + 1 
        
# CHANGE FORMATS OF OUTPUT
        try:  
          out['elev'] = int(float(out['elev']))
        except ValueError:
          err = err + 1
          print("ERROR: value for elev="+ str(out['elev']) +" not convertable to int")
          pass
        try:  
          out['time_zone'] = int(float(out['time_zone']))
        except ValueError:
          err = err + 1
          print("ERROR: value for time_zone="+ str(out['time_zone']) +" not convertable to int")
          pass   

# ADD DATA STAMP AND EXTRA INFO COLUMNS TO INFO 
        extra = {}
        allextra = ''
        for extry in extrastuff:
          extra[extry],errx = getdata(extry,dx,10)
          if extra[extry].strip() != "":
            allextra = allextra + extry.upper() + '=' +extra[extry] + ';'
        out['info'] = "SCRIPT ADD " + datestamp + "." + allextra + out['info']

# IF LINE IS GOOD, PRINT TO OUTPUT FILE.IF ERRORS, PRINT LINE TO ERROR FILE        
        print("row=" + str(i) + "; err="+str(err))
        if err == 0: 
          printform = makeprintlist(collist,colform)
          outfile.write(printform.format(**out))
        else:
          for it in out:
            out[it] = str(out[it])
          printform = makeprintlist(collist,'s')
          outfileerr.write(printform.format(**out)) 

sys.exit(0)

