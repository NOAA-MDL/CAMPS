#!/usr/bin/env python

import ConfigParser as cp
import datetime as dt
import itertools
import math
import numpy as np
import pytdlpack
import sys
import time

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

    #print " -- INSIDE FUNCTION XPROD"

    # Set some parameters for this function
    ndates = len(dates)
    nvrbl = len(ids)
    print "ndates = ",ndates
    print "nvrbl = ",nvrbl
    print "Number of stations is stagrp.nsta =", stagrp.nsta

#   Matrix b will hold content of aaa after replacing missing values 9999
#   with zero values and shifting variables to start from index 1 instead of zero
#   Only variables start with index 1. Other indices (for stations, dates, groups) start from zero.
    b = np.zeros((nvrbl+1,stagrp.nsta,ndates),dtype='float32',order='F')
    for nv in range(nvrbl):
        b[nv+1,:,:]=aaa[nv,:,:]
     
    # Size arrays accordingly
    smpl = np.zeros((stagrp.kgp),dtype='float64',order='F')
    sums = np.zeros((stagrp.kgp,nvrbl+1),dtype='float64',order='F')
    sumx = np.zeros((stagrp.kgp,nvrbl+1,nvrbl+1),dtype='float64',order='F') # now full square matrix
#   no longer flattened upper triangle only
    tmp  = np.zeros((nvrbl+1,nvrbl+1),dtype='float64',order='F')
#    bld = np.zeros(nvrbl+1,dtype='float64',order='F')

    print "Shape of smpl = ",smpl.shape
    print "Shape of sums = ",sums.shape
    print "Shape of sumx = ",sumx.shape
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

                if list(b[:,loc,nd]).count(9999.0) == 0:
                    smpl[ng] += 1.0
                else:
                    b[:,loc,nd]=0.0
                    continue

#               The portion of b for given location and date that is used in 
#               calculations below. 
                bld=np.copy(b[:,loc,nd])   
               
                # Calc sum for each variable over all stations in the group and dates
                for nv in range(1,nvrbl+1):
#                    sums[ng,nv] += b[nv,loc,nd]  The line below is equivalent to this one
                    sums[ng,nv] += bld[nv]

                # For two variables nv and nvv calculate their dot product over 
                # all stations in the group and dates
                # Compute daigonal plus one triangle of the matrix sumx of dot products  
                for nv in range(1,nvrbl+1):
                    bnvld=bld[nv]
                    for nvv in range(nv,nvrbl+1):
#                        tmp[nvv,nv] += (b[nv,loc,nd]*b[nvv,loc,nd])  The line below is equivalent to this one
                        tmp[nvv,nv] += (bnvld*bld[nvv])  
        
        # Fill in the other triangle of sumx by symmetry
        for nv in range(1,nvrbl+1):
            for nvv in range(1,nv+1):
                sumx[ng,nvv,nv] = tmp[nv,nvv]
                sumx[ng,nv,nvv] = tmp[nv,nvv]       
        tmp = 0.0*tmp 

#####
#    for ng in range(stagrp.kgp):
#        print " Group ",ng+1,":"
#        print "         Sample Size: ",smpl[ng]
#        print "     Sum of each var: ",sums[ng,1:nvrbl+1]
#        print "Dot Products of vars: ",sumx[ng,1:nvrbl+1,1:nvrbl+1]
#####
    return [smpl,sums,sumx]

# ---------------------------------------------------------------------------------------- 
# regress - "the black box" :)
# ---------------------------------------------------------------------------------------- 
def regress(stagrp,typ,ids,aaa,q,cutoff=0.0):

    # Note the following:
    #
    #     q[0] = list of sample size per group (NumPy float64)
    #     q[1] = list of sums for each variable per group (NumPy float64)
    #     q[2] = list of dot products among variables per group (NumPy float64)

    print " -- INSIDE FUNCTION REGRESS"

    nvrbl = len(ids)
    npred = 0
    ntand = 0
    for t in typ:
        if t == 1: npred += 1
        if t == 2: ntand += 1
    print " nvrbl, npred, ntand = ",nvrbl,npred,ntand

    lp = np.zeros((5,nvrbl+1),dtype='int32',order='F')
    #slp = np,.zeros((5,nvrbl+1),dtype='float32',order='F')

    a = np.zeros((ntand+1),dtype='float64',order='F') # regression constants    
    avg = np.zeros((nvrbl+1),dtype='float64',order='F') 
    # avg is the mean = sum of variable values divided by the sample size   
    const = np.zeros((ntand+1),dtype='float64',order='F')  # variances of predictands  
    const_1 = np.zeros((ntand+1),dtype='float64',order='F') # reciprocal values of const
    corr = np.zeros((ntand+1),dtype='float64',order='F') # multiple correlation coefficient  
    ess = np.zeros((ntand+1),dtype='float64',order='F') # standard error estimate  
    p = np.zeros((nvrbl+1,nvrbl+1),dtype='float64',order='F') # matrix of covariances 
    # that gets transformed using Gaussian elimination to determine regression coefficients 
    # corresponding to knt predictors  
    ptmp =  np.zeros((nvrbl+1),dtype='float64',order='F') # temporary array
    rdvr = np.zeros((ntand+1),dtype='float64',order='F') # coefficient of determination  
    var = np.zeros((nvrbl+1),dtype='float64',order='F') # variances in the diagonal of matrix p
    sig = np.zeros((nvrbl+1),dtype='float64',order='F') # variances of predictors, std. deviations of predictands   
    stddev = np.zeros((nvrbl+1),dtype='float64',order='F') # std. deviations   
    vh = np.zeros((ntand+1),dtype='float64',order='F') # correlations between predictor key and each predictand   
    tmp = np.zeros((ntand+1),dtype='float64',order='F') # temporary array used for permutation of columns or rows
    tmp5 = np.zeros(5,dtype='int32',order='F') # temporary array used for permutation 
    # of columns of LP 
    cor2 = np.zeros((nvrbl+1,nvrbl+1),dtype='float64',order='F') # temporary array for 
    # finding strongest (anti)-correlations between remaining predictors and predictands
    # to be used to select next predictor key to add to regression equation 

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
        for n in range(1,npred+1):
            lp[0,n] = n
            lp[1,n] = int(ids[n-1][0])
            lp[2,n] = int(ids[n-1][1])
            lp[3,n] = int(ids[n-1][2])
            lp[4,n] = int(ids[n-1][3])

        # Put dot products into p( , ). This replicates xfer.f. 
        p = np.copy(q[2][ng,:,:])

        # Compute means, covariances, standard deviations for each variable in group
        # avg is the mean = sum of variable values divided by the sample size
        avg = 1.0/q[0][ng] * q[1][ng,:]
        # p is covariance after centering over means of variables
        p -= np.outer(avg,q[1][ng,:])

        # Replicate Do 425/424 loops
        var = np.copy(np.diag(p))
        p -= np.diag(var)
        var = np.where(var>0, var, 0)
        p += np.diag(var)  # ensure that diagonal elements of p are not negative
        stddev = np.sqrt(1.0/q[0][ng] * var) # compute standard deviation   

        # Initially, set sig to stddev, then for predictors only, set sig
        # to diagonal elemants of p, each being the sum of squares for that variable.
        sig = np.copy(stddev)
        sig[1:npred+1] = var[1:npred+1]

        # Deal with binary predictands...not yet. For now, just put some data
        # into const. 
        const[1:ntand+1] = np.copy(var [npred+1:nvrbl+1])
        const_1[1:ntand+1] = np.reciprocal(const[1:ntand+1])

        # Begin regression analysis. DEFAULT for now to select based on
        # single predictand RoV.
        coln = 0.10 # set here for now...later in regress call
        nst = 15 # limit on the number of predictors to select.
        nstx = min(npred,nst) # maximum number of predictors that the regression will return

        # ----- REGRESSION SCREENING BEGINS HERE -----
        # The below while loop will run until a predictors reduction of
        # variance does not exceed cutoff 
        k = 0  
        knt = 0  # number of predictors chosen
        done = False
        while (not done and k < nstx):

            # Choose next predictor 'key' to add to the regression
            # p[rng,rngd] is submatrix d_k of transformend P after Gaussian elimination on columns 1 to k
            rng = range(k+1,npred+1) # range of reminaing predictors in p
            rngd = range (npred+1,nvrbl+1)     # predictand range in p
            rngc = range (1,ntand+1)  # predictand range in const, vh

            # perform colinearity test
            cor2 = 0.0*cor2
            for l in rng: 
                if (p[l,l]>0.0 and sig[l]>0.0 and p[l,l]>coln*sig[l]):
                    pll_1=1.0/p[l,l]
                    cor2[l,rngd] = pll_1*np.multiply(p[[l],:][:,rngd],p[[l],:][:,rngd])
            cor2[:,rngd] = np.multiply(cor2[:,rngd],const_1[rngc])

            # find 'key' as the predictor with strongest (anti)correlation with one of the predictands
            cor2maxl = np.amax(cor2, axis=1)
            vht      = np.amax(cor2maxl)
            key      = np.argmax(cor2maxl)



            # This replicates Do 525.
            vh [rngc] = np.copy(cor2[[key],:][:,rngd])
            vh[rngc] = np.copy(cor2[key,rngd])             
                
            # This replicates Do 530. For now, it only supports testing
            # ROV against any 1 predictand (in u600, NSNGL=1).
            # FUTURE: Added ability to test ROV against the avg of all predictands.

            if (vht>0 and key>k and key<=npred and np.any(vh[rngc] > cutoff)):

                # number of operations below: 
                # number of groups * nstx (< npred) * (npred + ntand)
                # Typical number 2 * 10^6 ~= 3000 * 15 * 44
                # Variable  key  is the strongest (anti-)correlated predictor 
                # for some predictant
                # among all remaining predictors [k+1:npred+1].
                # Bring variable  key  to  the place of  k+1, 
                # which is the first of the remaining predictors. 
                # Swap columns key and k+1 of matrices p, lp;
                # Swap rows    key and k+1 of matrix p; 
                # swap elements key and k+1 of vectors sig, avg
                # 
                # Do 555

                tmp = np.copy(p[:,k+1])
                p[:,k+1]=p[:,key]
                p[:,key] = tmp

                # Do 560
                tmp = np.copy(p[k+1,:])
                p[k+1,:] = p[key,:]
                p[key,:] = tmp

                # Do 565, Predictor ID stuff.
                tmp5 = np.copy(lp[:,k+1])
                lp[:,k+1] = lp[:,key]
                lp[:,key] = tmp5

                tvh = np.copy(sig[k+1])
                sig[k+1] = sig[key]
                sig[key] = tvh

                # IS: New, swap k+1 and key elements of avg
                tvh = np.copy(avg[k+1])
                avg[k+1] = avg[key]
                avg[key] = tvh

                # Gaussian elimination on column k+1 to make it the transpose of
                # [0 .. 0 1 0....0] with 1 in the row with index k+1 
                # Do 570
                ptmp = np.copy(p[k+1,:])
                f=1.0/p[k+1,k+1]
                p -= f* np.outer(p[:,k+1],ptmp)
                # Do 575
                p[k+1,:] = f * ptmp                    

                # Compute regression constants using eq. (1) in documentation
                # Do 580
                a[rngc] = np.copy(avg[rngd])
                # Do 585
                # Do 584
                a[rngc] -= np.dot(avg[1:k+2],p[1:k+2,rngd])


                # Do 587
                # standard error estimate
                ess [rngc] = np.copy(np.diag(p[rngd,:][:,rngd]))
                ess = np.where(ess>0, ess, 0)
                ess = np.sqrt(1.0/q[0][ng]*ess)

                # coefficient of determination
                # which is proportion of variablity of predictand that can 
                # be attributed to variability in predictiors selected fo far
                rdvr [rngc] = np.copy(sig[rngd])
                rdvr [rngc] = np.true_divide (1.0/q[0][ng],np.multiply(rdvr[rngc],rdvr[rngc]))
                rdvr [rngc] = 1.0- np.multiply(np.diag(p[rngd,:][:,rngd]),rdvr[rngc])
                rdvr = np.where (rdvr>0, rdvr,0)

                # multiple correlation coefficient
                corr = np.sqrt(rdvr)

                # Still inside for k; for n in ntand; vh[n] > cutoff
                print " VARIABLE ",lp[1:5,k+1]," SELECTED. TOTAL RV ",rdvr[rngc] 

                # increment k to continue while loop, set knt to the number of selected predictors 
                k += 1
                knt = k

            else: # vh[n] < cutoff

                # If we come here, then the next selected predictor does not
                # contribute more reduction of variance than is set by the
                # threshold variable, cutoff. 
                # The regression screeneng while loop is finished.
                print " NEXT SELECTED PREDICTOR DOES NOT CONTRIBUTE MORE THAN ",cutoff," REDUCTION OF VARIANCE"
                done = True

        # Outside while k...Print regression equation information
        print " TOTAL RV BY ",knt," PREDICTORS: f",rdvr[rngc]
        print " MULTIPLE CORRELATION COEFFICIENT: ",corr[rngc]
        print " STD ERROR ESTIMATE: ",ess[rngc]
        print " REGRESSION EQUATION"
        print ""*44,"CONSTANT ",a[rngc]
        for k in range(1,knt+1):
            print k,lp[1,k],lp[2,k],lp[3,k],lp[4,k],p[k,npred+1:npred+ntand+1]
        print "\n %43s\n" % (43*"*")
#        sys.stdout.flush()            

# ---------------------------------------------------------------------------------------- 
# Main
# ---------------------------------------------------------------------------------------- 
dateListFile = sys.argv[1]
stationListFile = sys.argv[2]
idListFile = sys.argv[3]
predDataFile = sys.argv[4]
tandDataFile = sys.argv[5]

start = time.clock()


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
print "loaded data"

loaded = time.clock()
q = xprod(aaa,dates,stagrp,ids)
print "Computed q array and going into regression"

endxprod = time.clock()
cutoff = 0.005
regress(stagrp,ntyp,ids,aaa,q,cutoff=cutoff)
endregress = time.clock()

print "xprod time = ", endxprod - loaded
print "regress time = ", endregress - endxprod
print "total time = ", endregress - start

