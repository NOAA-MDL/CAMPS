#!/usr/bin/env python

import ConfigParser as cp
import datetime as dt
import itertools
import math
import numpy as np
import pytdlpack
import sys

_dateformat="%Y%m%d%H"

# ---------------------------------------------------------------------------------------- 
# Class: Equation
# ---------------------------------------------------------------------------------------- 
class Equations(object):
    def __init__(self,**kwargs):
        """
   Create an Equation class instance. 
        """
        for k,v in kwargs.items():
            setattr(self,k,v)

# ---------------------------------------------------------------------------------------- 
# Class: StationGroup
# ---------------------------------------------------------------------------------------- 
class StationGroup(object):
    def __init__(self,**kwargs):
        """
  Create a StationGroup class instance.
        """
        for k,v in kwargs.items():
            setattr(self,k,v)

# ---------------------------------------------------------------------------------------- 
#
# ---------------------------------------------------------------------------------------- 
def prsid(list):

    # Input list has the following items per position
    #    [0] = typ
    #    [1] = id word 1
    #    [2] = id word 2
    #    [3] = id word 3
    #    [4] = isg
    #    [5] = threshold

    typ = int(list[0])
    id1 = int(list[1])
    id2 = int(list[2])
    id3 = int(list[3])
    isg = int(list[4])

    # Build id4
    if list[5][0] == "-":
        w = 1
        frac = int(list[5][2:6])
        sgn = list[5][7]
        exp = int(list[5][8:10])
    else:
        w = 0
        frac = int(list[5][1:5])
        sgn = list[5][6]
        exp = int(list[5][7:9])

    if sgn == "-":
        exp += 50

    wxxxxyy = (w * 1000000) + (frac * 100) + exp
    id4 = (wxxxxyy * 1000) + isg 
    
    return typ,[id1,id2,id3,id4]

# ---------------------------------------------------------------------------------------- 
# Read Date List
# ---------------------------------------------------------------------------------------- 
def readDateList(dateListFile):

    #_dateformat="%Y%m%d%H"
    dates = []

    # Open date list file; read lines; close.
    f = open(dateListFile,"r")
    lines = f.readlines()
    f.close()

    # List comprehension used here to remove spaces, '\n', and the terminator line.
    lines = [line.strip(' ')[:-1] for line in lines[:-1]]

    # Now we have a clean list of dates (represented as strings for now). Time to
    # create the date ranges
    for i,line in enumerate(lines):
       if i % 2 != 0: continue
       start = dt.datetime.strptime(line,_dateformat)
       end = dt.datetime.strptime(lines[i+1][1:],_dateformat)
       step = dt.timedelta(hours=24)
       while start <= end:
          dates.append(int(start.strftime(_dateformat)))
          start += step

    return dates

# ---------------------------------------------------------------------------------------- 
# Read ID List
# ---------------------------------------------------------------------------------------- 
def readIDList(idListFile):

    ids = []
    ntyp = []

    f = open(idListFile,"r")
    for line in f:
        line = line.split(" ")
        while '' in line:
           line.remove('')
        typ,id = prsid(line)
        ids.append(id)
        ntyp.append(typ)

    return ntyp,ids

# ---------------------------------------------------------------------------------------- 
# Read Station List
# ---------------------------------------------------------------------------------------- 
def readStationList(stationListFile):

    kwargs = {}

    ccall = []
    group = []
    groups = [] # This is a list of lists of station call letters
    kgp = 0     # Total number of groups
    ngp = []    # Total number of stations in each group
    nsta = 0    # Total number of stations

    f = open(stationListFile,"r")
    for line in f:
        if (line[:-1] == "99999999"):
            kgp += 1
            groups.append(group)
            ngp.append(len(group))
            group = []
            continue
        else:
            nsta += 1
            group.append(line[:-1])

    f.close()

    # Remove the last item in the lists ngp and groups as this item
    # is the "terminating" group.
    ngp = ngp[:-1]
    groups = groups[:-1]

    # Build a unique list of stations
    for g in groups:
        for sta in g:
            if sta not in ccall:
               ccall.append(sta)

    # Initializing
    kwargs['ccall'] = ccall
    kwargs['groups'] = groups
    kwargs['kgp'] = len(groups)
    kwargs['ngp'] = ngp
    kwargs['nsta'] = nsta

    return StationGroup(**kwargs)

# ---------------------------------------------------------------------------------------- 
# loadData
# ---------------------------------------------------------------------------------------- 
def loadData(predfile,tandfile,dates,ntype,ids,stations):

    ndates = len(dates)
    nvrbl = len(ids)
    nsta = len(stations)

    data = np.zeros((nvrbl,nsta,ndates),dtype='float32',order='F')
    data.fill(9999.0)

    predids = []
    tandids = []

    # Create separate ID lists for predictors and predictands. However,
    # we'll need to consider observed predictors as predictands here.
    # IMPORTANT: Need to use list() when appending so that we do not
    #            change the original ids[].
    npred = 0
    ntand = 0
    for typ,id in zip(ntype,ids):
        if typ == 1:
            sid1 = ("%.9d") % id[0]
            if sid1[0] == "7":
                tandids.append(list(id))
                ntand += 1
            else:
                predids.append(list(id))
                npred += 1
        if typ == 2:
            tandids.append(list(id))
            ntand += 1

    # Get predictor data
    nccall = 0
    nccall_prev = 0
    records = pytdlpack.TdlpackDecode(predfile,dates,predids)
    for nr,rec in enumerate(records):

        nccall_prev = nccall
        nccall = rec.nccall

        # Index all stations when needed.
        if nr == 0 or nccall > nccall_prev:
            staloc = []
            for s in stations:
                try:
                    loc = rec.ccall.index(s)
                except ValueError:
                    loc = -1
                staloc.append(loc)

        # Get index for date
        try:
            didx = dates.index(rec.date)
        except ValueError:
            continue

        # Get index for id
        try:
            iidx = ids.index(list(rec.id))
        except ValueError:
            continue

        # Unpack the data and store the values needed in data. Here 
        # we iterate over staloc list which contains the location
        # of the station int eh rec.values
        xdata = rec.values
        for n,loc in enumerate(staloc):
            if loc == -1:
                data[iidx,n,didx] = 9999.0
            else:
                data[iidx,n,didx] = xdata[loc]

    # Setup IDs and dates for predictands and observed predictors since
    # these are from the same input dataset(s) -- observations.
    taus = []
    tanddates = []
    for nt,t in enumerate(tandids):
        taus.append(t[2]-((t[2]/1000)*1000))
        t[2] = (t[2]/1000)*1000
        tdates = []
        for d in dates: tdates.append(updat(d,taus[nt]))
        tanddates.append(tdates)
    alltanddates = list(set(sum(tanddates,[])))
    alltanddates.sort()

    #for x in alltanddates: print x
    #exit()
    #for x1,x2 in zip(tanddates[0],tanddates[1]):print x1,x2
    #exit()

    # Get predictand data.
    nccall = 0
    nccall_prev = 0
    tands = pytdlpack.TdlpackDecode(tandfile,alltanddates,tandids)
    for nr,rec in enumerate(tands):

        nccall_prev = nccall
        nccall = rec.nccall

        # First record, index all stations.
        if nr == 0 or nccall > nccall_prev:
            staloc = []
            for s in stations:
                try:
                    staloc.append(rec.ccall.index(s))
                except ValueError:
                    staloc.append(-1)

        xdata = rec.values

        # Here we need to iterate over predictands... 
        for nt,tid in enumerate(tandids):
            
            # Get index of the record date in tanddates[]. This index
            # will not necessarily map to the correct date in dates[].
            try:
                didx = tanddates[nt].index(rec.date)
            except ValueError:
                continue
                #didx = -1
            
            # Get index for id
            xrec = list(rec.id)
            xrec[2] = xrec[2]+taus[nt]
            try:
                iidx = ids.index(xrec)
            except ValueError:
                continue
                #iidx = -1

            # Now we have index values for the date in tanddates and
            # record ID in the original ID list.  Next we need the index
            # of the tanddat shifted with -taus[nt] within dates[].
            if didx >= 0:
                datex = updat(tanddates[nt][didx],-taus[nt])
                try:
                    didx = dates.index(datex)
                except ValueError:
                    continue
                    #didx = -1
 
            for n,loc in enumerate(staloc):
                #if loc == -1 or didx == -1 or iidx == -1:
                if loc == -1:
                    data[iidx,n,didx] = 9999.0
                else:
                    data[iidx,n,didx] = xdata[loc]

    return data

# ---------------------------------------------------------------------------------------- 
# updat
# ---------------------------------------------------------------------------------------- 
def updat(indate,itau):
    
    dtdate = dt.datetime.strptime(str(indate),_dateformat)
    step = dt.timedelta(hours=itau)
    dtdate += step
    return int(dtdate.strftime(_dateformat))

# ---------------------------------------------------------------------------------------- 
# xprod
# ---------------------------------------------------------------------------------------- 
def xprod(aaa,dates,stagrp,ids):

    print " -- INSIDE FUNCTION XPROD"

    # Set some parameters for this function
    ndates = len(dates)
    nvrbl = len(ids)
    print "ndates = ",ndates
    print "nvrbl = ",nvrbl

    # Size arrays accordingly
    smpl = np.zeros((stagrp.kgp),dtype='float64',order='F')
    sums = np.zeros((stagrp.kgp,nvrbl),dtype='float64',order='F')
    sumx = np.zeros((stagrp.kgp,nvrbl+sum(range(nvrbl))),dtype='float64',order='F')

    print "Shape of smpl = ",smpl.shape
    print "Shape of sums = ",sums.shape
    print "Shape of sums = ",sumx.shape
    sys.stdout.flush()

    # Iterate over dates and groups.  For each date and group, we need to compute the sample
    # size, variable sums, and sums of cross products.  The group sample size count is 
    # incremented when all data (predictors and predictands) are not missing for a station
    # for a given date.  Non-missing variables are summed and stored in sums.  Finally, 
    # sums of cross procuts are computed and stored in sumx.  
    for ng,g in enumerate(stagrp.groups):
        for ns,s in enumerate(g):

            # Get location of station in ccall list.  This corresponds to the
            # location of the stations data in aaa. We do not need to use
            # try/except here.
            loc = stagrp.ccall.index(s)

            # Calc sample size and sums
            for nd,d in enumerate(dates):

                if list(aaa[:,loc,nd]).count(9999.0) == 0:
                    smpl[ng] += 1.0
                else:
                    continue

                # Calc sums of variables
                for nv in range(nvrbl):
                    if int(aaa[nv,loc,nd]) != 9999:
                        #print ng+1,ns+1,nv+1,d,s,aaa[nv,loc,nd]
                        sums[ng,nv] += aaa[nv,loc,nd]

                # Calc sums of cross products
                nrt = 0
                for nv in range(nvrbl):
                    for nvv in range(nv,nvrbl):
                        if int(aaa[nv,loc,nd]) != 9999 and int(aaa[nvv,loc,nd]) != 9999:
                            sumx[ng,nrt] += (aaa[nv,loc,nd]*aaa[nvv,loc,nd])
                        nrt += 1

    #for ng in range(stagrp.kgp):
    #    print " Group ",ng+1,":"
    #    print "        Sample Size: ",smpl[ng]
    #    print "               Sums: ",sums[ng,:]
    #    print " Sums of Cross Prod: ",sumx[ng,:]

    return [smpl,sums,sumx]

# ---------------------------------------------------------------------------------------- 
# regress - "the black box" :)
# ---------------------------------------------------------------------------------------- 
def regress(stagrp,typ,ids,aaa,q,cutoff=0.0):

    # Note the following:
    #
    #     q[0] = list of sample size per group (NumPy float64)
    #     q[1] = list of variable sums per group (NumPy float64)
    #     q[2] = list of sums of cross products per group (NumPy float64)

    print " -- INSIDE FUNCTION REGRESS"

    nvrbl = len(ids)
    npred = 0
    ntand = 0
    for t in typ:
        if t == 1: npred += 1
        if t == 2: ntand += 1
    print " nvrbl, npred, ntand = ",nvrbl,npred,ntand

    lp = np.zeros((5,nvrbl),dtype='int32',order='F')
    #slp = np,.zeros((5,nvrbl),dtype='float32',order='F')

    a = np.zeros((ntand),dtype='float64',order='F')    
    avg = np.zeros((nvrbl),dtype='float64',order='F')    
    const = np.zeros((ntand),dtype='float64',order='F')    
    corr = np.zeros((ntand),dtype='float64',order='F')    
    ess = np.zeros((ntand),dtype='float64',order='F')    
    p = np.zeros((nvrbl,nvrbl),dtype='float64',order='F')    
    rdvr = np.zeros((ntand),dtype='float64',order='F')    
    sig = np.zeros((nvrbl),dtype='float64',order='F')    
    stddev = np.zeros((nvrbl),dtype='float64',order='F')    
    vh = np.zeros((ntand),dtype='float64',order='F')    

    # Begin iteration over groups
    for ng,g in enumerate(stagrp.groups):

        if (q[0][ng] <= 200):
            print " EQUATION DEVELOPMENT FOR GROUP ",ng
            print " STATION NAME ", stagrp.groups[ng]
            print " NOT ENOUGH SAMPLES TO CALCULATE"
            print "\n %43s\n" % (43*"*")
            sys.stdout.flush()
            continue

        print " EQUATION DEVELOPMENT FOR GROUP ",ng
        print " STATION NAME ",stagrp.groups[ng]
        print " %6d TOTAL CASES FOR REGRESSION ANALYSIS\n" % (q[0][ng])
        sys.stdout.flush()
      

        # Initialize lp for each equation group, this assumes the ids
        # are listed first.
        for n in range(npred):
            lp[0,n] = n
            lp[1,n] = int(ids[n][0])
            lp[2,n] = int(ids[n][1])
            lp[3,n] = int(ids[n][2])
            lp[4,n] = int(ids[n][3])

        # Put cross products into p( , ). This replicates xfer.f. Use counter
        # nrt as index for sums of cross products (q[2]).
        nrt = 0
        #print " Cross products:"
        for n1 in range(nvrbl):
            for n2 in range(n1,nvrbl):
                p[n2,n1] = q[2][ng,nrt]
                p[n1,n2] = q[2][ng,nrt]
                #print "    %d %d %d %f %f" % (n1,n2,n3,p[n2,n1],p[n1,n2])
                nrt += 1

        # Compute means, variances, correlations for each variable in group
        for l in range(nvrbl):
            avg[l] = q[1][ng,l]/q[0][ng]       
            #print ng,l,q[1][ng,l],q[0][ng],avg[l]

        # Replicate Do 425/424 loops
        for l in range(nvrbl):
            tmp = q[1][ng,l]
            for m in range(l,nvrbl):
                #print l,m,p[m,l],tmp,avg[m],(tmp*avg[m])
                p[m,l] -= (tmp*avg[m])
                #print l,m,p[m,l],tmp,avg[m],(tmp*avg[m])
            if p[l,l] < 0.0: p[l,l] = 0.0
            stddev[l] = p[l,l]/q[0][ng]
        stddev = np.sqrt(stddev)

        # The following mimmics the u600.f DO 429, 430 Loops 
        # IMPORTANT: The loop for m, in Python, needs to have l+1.
        for l in range(1,nvrbl):
            for m in range(1,l+1):
                p[m-1,l] = p[l,m-1]

        # Compute the correlation of a predictor with each predictand.
        # This replicates u600.f DO 438, 440 Loops.
        for l in range(npred):
            for m in range(ntand):
                div = stddev[l]*stddev[npred+m]*q[0][ng]
                if div <= 0.0:
                    corr[m] = 0.0
                else:
                    corr[m] = p[npred+m,l]/div
                #print l,m,corr

        # Initially, set sig to stddev, then for predictors only, set sig
        # to p.
        sig = stddev
        for n in range(npred):
            sig[n] = p[n,n]

        # Deal with binary predictands...not yet. For now, just put some data
        # into const.
        for n in range(ntand):
            nn = npred+n
            const[n] = p[nn,nn]

        # Begin regression analysis. DEFAULT for now to select based on
        # single predictand RoV.
        coln = 0.10 # set here for now...later in regress call
        nst = 15 # number of predictors to select.
        nstx = min(npred,nst)

        # ----- REGRESSION SCREENING BEGINS HERE -----
        # The below while loop will run until a predictors reduction of
        # variance does not exceed cutoff -- which will then set k = -1.
        k = 0
        knt = 0
        while k >= 0 and k <= nstx:

            # Reset key and vht.  Explain!
            key = -1
            vht = 0.0

            # Loop over predictors.  Perform colinearity test.
            # range(k,npred) is OK here.
            for l in range(k,npred):
                #print l,p[l,l],sig[l],p[l,l]/sig[l]
                if p[l,l] <= 0.0 or sig[l] <= 0.0: continue
                if p[l,l]/sig[l] <= coln: continue
                pll = p[l,l]
                # Come here if predictor passes colinearity test.  Now
                # test reduction of variance (tvh)
                for n in range(ntand):
                    j = npred+n
                    tvh = (p[l,j]**2.0)/(pll*const[n])
                    #print k,l,n,j,p[l,j],pll,const[n],tvh,vht
                    if vht > tvh:
                        continue
                    else:
                        vht = tvh
                        key = l
                 
            if key == -1: continue
    
            # This replicates Do 525.
            for n in range(ntand):
                nn = npred+n
                vh[n] = (p[key,nn]**2.0)/(p[key,key]*const[n])

            # This replicates Do 530. For now, it only supports testing
            # ROV against any 1 predictand (in u600, NSNGL=1).
            # FUTURE: Added ability to test ROV against the avg of all predictands.
            for n in range(ntand):

                if vh[n] > cutoff:

                    # Do 555
                    for l in range(nvrbl):
                        tvh = p[l,k]
                        p[l,k] = p[l,key]
                        p[l,key] = tvh

                    # Do 560
                    for l in range(nvrbl):
                        tvh = p[k,l]
                        p[k,l] = p[key,l]
                        p[key,l] = tvh

                    # Do 565, Predictor ID stuff.
                    for j in range(5): 
                        ltvh = lp[j,k]
                        lp[j,k] = lp[j,key]
                        lp[j,key] = ltvh

                    tvh = sig[k]
                    sig[k] = sig[key]
                    sig[key] = tvh

                    # Do 570
                    for l in range(nvrbl):
                        if k == l: continue
                        f = p[l,k]/p[k,k]
                        # Do 569
                        for m in range(k,nvrbl):
                            p[l,m] -= (f*p[k,m])

                    f = p[k,k]

                    # Do 575
                    for l in range(k,nvrbl):
                        p[k,l] /= f

                    # Do 580
                    for n2 in range(ntand):
                        j = npred+n2
                        a[n2] = avg[j]

                    # Do 585
                    # IMPORTANT: Here if this is the first predictor chosen,
                    # k=0, but range(0) returns an empty list.  Instead, set
                    # kk=1, when k=1, otherwise kk=k.
                    kk = k
                    if k == 0: kk = 1
                    for l in range(kk):
                        nx = lp[0,l]
                        # Do 584
                        for n2 in range(ntand):
                            j = npred+n2
                            a[n2] -= p[l,j]*avg[nx] 

                    # Do 587
                    for n2 in range(ntand):
                        j = npred+n2
                        if p[j,j] >= 0.0:
                            ess[n2] = math.sqrt(p[j,j]/q[0][ng])
                        else:
                            ess[n2] = 0.0
                        rdvr[n2] = 1.0-(p[j,j]/q[0][ng])/(sig[j]**2.0)
                        if rdvr[n2] < 0.0:
                            corr[n2] = 0.0
                        else:
                            corr[n2] = math.sqrt(rdvr[n2])

                    # Still inside for k; for n in ntand; vh[n] > cutoff
                    print " VARIABLE ",lp[1:5,k]," SELECTED. TOTAL RV ",rdvr[:] 

                    # Increment k; set knt to the incremented k; then break the
                    # current for loop (n in range(ntand)).
                    k += 1
                    knt = k
                    break

                else: # vh[n] < cutoff
 
                    # Allow for loop (n in range(ntand) to continue since
                    # we have multiple predictands
                    if n < ntand-1: continue

                    # If we come here, then the next selected predictor does not
                    # contribute more reduction of variance than is set by the
                    # threshold variable, cutoff.  Here we hold k in knt and
                    # k is set to -1 to exit the while loop.  The regression
                    # screening is finished.
                    print " NEXT SELECTED PREDICTOR DOES NOT CONTRIBUTE MORE THAN ",cutoff," REDUCTION OF VARIANCE"
                    k = -1

        # Outside while k...Print regression equation information
        print " TOTAL RV BY ",knt," PREDICTORS: f",rdvr[:]
        print " MULTIPLE CORRELATION COEFFICIENT: ",corr[:]
        print " STD ERROR ESTIMATE: ",ess[:]
        print " REGRESSION EQUATION"
        print ""*44,"CONSTANT ",a[:]
        for k in range(knt):
            print k,lp[1,k],lp[2,k],lp[3,k],lp[4,k],p[k,npred:npred+ntand]
        print "\n %43s\n" % (43*"*")
        sys.stdout.flush()
            

# ---------------------------------------------------------------------------------------- 
# Main
# ---------------------------------------------------------------------------------------- 
dateListFile = sys.argv[1]
stationListFile = sys.argv[2]
idListFile = sys.argv[3]
predDataFile = sys.argv[4]
tandDataFile = sys.argv[5]

print "Date List File = ",dateListFile
dates=readDateList(dateListFile)
print "Total Number of Dates = ",len(dates)
print "Dates Generated = ",dates

print "Station List File = ",stationListFile
stagrp=readStationList(stationListFile)

print "Total Number of Stations = ",stagrp.nsta
print "Total Number of Groups = ",stagrp.kgp
print "Total Number of Stations per Group = ",stagrp.ngp
print "Groups: ",stagrp.groups
print "Unique Station List: ",stagrp.ccall

print "ID List File = ",idListFile
ntyp,ids=readIDList(idListFile)
print " IDS = ",ntyp,ids

print "TDLPACK Predictor Input File = ",predDataFile
print "TDLPACK Predictand Input File = ",tandDataFile
sys.stdout.flush()

aaa = loadData(predDataFile,tandDataFile,dates,ntyp,ids,stagrp.ccall)

q = xprod(aaa,dates,stagrp,ids)

cutoff = 0.005
regress(stagrp,ntyp,ids,aaa,q,cutoff=cutoff)
