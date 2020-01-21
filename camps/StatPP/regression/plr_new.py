#!/usr/bin/env python

import ConfigParser as cp
import datetime as dt
import itertools
import math
import numpy as np
import sys
import time
import pdb
import logging
import pytdlpack
from ...core import util as util

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


def get_aaa(stations, predictors):
    """aaa is 3D array used in xprod and mlr.
    dimensioned by [number_of_vars, number_of_stations, number_of_dates]
    """
    # Slice stations if need be

    # Slice Dates 

    # Stack data
    logging.info('Creating aaa array')
    aaa = None 
    for pred in predictors:
        # Just get the station and date dimensions
        num_dimensions =  len(pred.data.shape)
        cur_data = pred.data.copy()
        if num_dimensions > 2:
            cur_data = cur_data[:,:,0]
        if aaa is None:
            aaa = cur_data.copy()
        else:
            print cur_data.shape
            aaa = np.dstack((aaa,cur_data))
    # Correct dimensions 
    aaa = aaa.T
    return aaa


def xprod_new(aaa, num_dates, stations, groups, num_vars):

    logging.info('Calculating Cross Products')
    stations = list(stations)
    # Set some parameters for this function
    ndates = num_dates
    nvrbl = num_vars
    num_groups = len(groups)
    num_stations = len(stations)
    logging.info("Number of dates       : "+str(ndates))
    logging.info("Number of vars        : "+str(nvrbl))
    logging.info("Number of stations is :" +str(len(stations)))

#   Matrix b will hold content of aaa after replacing missing values 9999
#   with zero values and shifting variables to start from index 1 instead of zero
#   Only variables start with index 1. Other indices (for stations, dates, groups) start from zero.
    b = np.zeros((nvrbl+1,num_stations,ndates),dtype='float32',order='F')
    for nv in range(nvrbl):
        b[nv+1,:,:]=aaa[nv,:,:]
     
    # Size arrays accordingly
    smpl = np.zeros((num_groups),dtype='float64',order='F')
    sums = np.zeros((num_groups,nvrbl+1),dtype='float64',order='F')
    sumx = np.zeros((num_groups,nvrbl+1,nvrbl+1),dtype='float64',order='F') # now full square matrix
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
    for ng,g in enumerate(groups):
        for ns,s in enumerate(g):

            # Get location of station in ccall list.  This corresponds to the
            # location of the stations data in aaa. We do not need to use
            # try/except here.
            loc = stations.index(s)

            # Calc sample size and sums
            for nd in range(ndates):

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

    return [smpl,sums,sumx]

def regress(groups,predictors,predictands,aaa,q,regression_params):

    # Note the following:
    #
    #     q[0] = list of sample size per group (NumPy float64)
    #     q[1] = list of sums for each variable per group (NumPy float64)
    #     q[2] = list of dot products among variables per group (NumPy float64)

    logging.info(" -- INSIDE FUNCTION REGRESS")
    cutoff = regression_params['cutoff']

    npred = len(predictors)
    #remove next line
    #npred = npred - 2
    ntand = len(predictands)
    nvrbl = ntand + npred
    num_stations = aaa.shape[1]
    #for t in typ:
    #    if t == 1: npred += 1
    #    if t == 2: ntand += 1
    logging.info(" nvrbl = " + str(nvrbl))
    logging.info(" npred = " + str(npred))
    logging.info(" ntand = " + str(ntand))


    # Riley
    predictor_list = np.zeros((nvrbl+1),dtype='int32',order='F')
    coefs = np.zeros((len(groups),nvrbl),dtype='int32',order='F')
    constants = np.zeros((len(groups)),dtype='int32',order='F')
    predictand_list = np.zeros((len(predictands)),dtype='int32',order='F')
    summary = [([0]*12) for i in range((npred))]
    # End Riley

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

    #Riley


    # Init Equations
    equations = []
    for ng,group in enumerate(groups):
        equations.append({'stations' : group})
        equations[ng]['predictors'] = []
        equations[ng]['constant'] = []
        equations[ng]['coefs'] = [np.zeros((ntand), dtype='int32')]*npred
        equations[ng]['ancil'] = {}

    eq_list = []
    #End Riley
    # Begin iteration over groups
    for ng,g in enumerate(groups):


        if (q[0][ng] <= 200):
            logging.info(" EQUATION DEVELOPMENT FOR GROUP " + str(ng))
            logging.info(" STATION NAME "+ str(groups[ng]))
            logging.info(" NOT ENOUGH SAMPLES TO CALCULATE")
            logging.info(str(43*"*"))
            sys.stdout.flush()
            #continue
        if (q[0][ng] <= 1):
            continue

        logging.info(" EQUATION DEVELOPMENT FOR GROUP "+str(ng))
        logging.info(" STATION NAME "+str(groups[ng]))
        print(" %6d TOTAL CASES FOR REGRESSION ANALYSIS\n" % (q[0][ng]))
        sys.stdout.flush()

        # Initialize lp for each equation group, this assumes the ids
        # are listed first.
       # for n in range(1,npred+1):
       #     lp[0,n] = n
       #     lp[1,n] = int(ids[n-1][0])
       #     lp[2,n] = int(ids[n-1][1])
       #     lp[3,n] = int(ids[n-1][2])
       #     lp[4,n] = int(ids[n-1][3])

        # Riley
        for n in range(1, len(predictors)):
            predictor_list[n] = n # make predictor list hold index associated with predictor place
        # End Riley

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
        if 0 not in const[1:ntand+1]:
            const_1[1:ntand+1] = np.reciprocal(const[1:ntand+1])

        # Begin regression analysis. DEFAULT for now to select based on
        # single predictand RoV.
        coln = regression_params['coln'] # set here for now...later in regress call
        nst = regression_params['nst']# limit on the number of predictors to select.
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
                #tmp5 = np.copy(lp[:,k+1])
                #lp[:,k+1] = lp[:,key]
                #lp[:,key] = tmp5
                # Riley
                try:
                    tmp5 = np.copy(predictor_list[k+1])
                    predictor_list[k+1] = predictor_list[key]
                    predictor_list[key] = tmp5
                except:
                    pdb.set_trace()
                # End Riley

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
                #print " VARIABLE ",lp[1:5,k+1]," SELECTED. TOTAL RV ",rdvr[rngc] 
                logging.info(" VARIABLE "+str(predictor_list[k+1])+" SELECTED. TOTAL RV "+str(rdvr[rngc]))

                # increment k to continue while loop, set knt to the number of selected predictors 
                k += 1
                knt = k

            else: # vh[n] < cutoff

                # If we come here, then the next selected predictor does not
                # contribute more reduction of variance than is set by the
                # threshold variable, cutoff. 
                # The regression screeneng while loop is finished.
                logging.info(" NEXT SELECTED PREDICTOR DOES NOT CONTRIBUTE MORE THAN "+str(cutoff)+" REDUCTION OF VARIANCE")
                done = True

        # Outside while k...Print regression equation information
        logging.info(" TOTAL RV BY "+str(knt)+" PREDICTORS: f "+str(rdvr[rngc]))
        logging.info(" MULTIPLE CORRELATION COEFFICIENT: "+str(corr[rngc]))
        logging.info(" STD ERROR ESTIMATE: "+str(ess[rngc]))
        logging.info(" REGRESSION EQUATION")
        logging.info(""*44+"CONSTANT "+str(a[rngc]))
        equations[ng]['constant'] = a[rngc]
        equations[ng]['ancil']['Equation Constant'] = a[rngc]
        equations[ng]['ancil']['Multiple Correlation Coeeficient'] = corr[rngc]
        equations[ng]['ancil']['Standard Error Estimate'] = ess[rngc]
        equations[ng]['ancil']['Reduction of Variance'] = rdvr[rngc]
        equations[ng]['ancil']['Predictand Average'] = avg[-ntand:]
        equations[ng]['constant'] = a[rngc]
        for k in range(1,knt+1):
            #print k,lp[1,k],lp[2,k],lp[3,k],lp[4,k],p[k,npred+1:npred+ntand+1]
            logging.info(str(k) + " " + str(predictor_list[k]) + " " +str(p[k,npred+1:npred+ntand+1]))
            equations[ng]['predictors'].append(predictor_list[k])
            equations[ng]['coefs'][predictor_list[k]-1] = p[k,npred+1:npred+ntand+1]
#            summary[predictor_list[k]][k] += 1
        logging.info("\n %43s\n" % (43*"*"))
#        sys.stdout.flush()       
    for i,j in enumerate(predictors):
        logging.info(i)
        logging.info(j)
#    for i in summary:
        
#        print i[1:]
    return equations 

def make_consistent_dims(predictors, predictands):
    """Makes dimensions consistent across predictors and predictands.
    assumes at least on predictor and predictand.
    """
    all_locs = []
    all_vars = predictands + predictors
    for var in all_vars:
        if var.dimensions.index('number_of_stations') == 0:
            var.data = var.data.T

    pred_stations = predictors[0].location.get_stations()
    tand_stations = predictands[0].location.get_stations()
    # Check to be sure pred and tand station lists are formatted the same
    char_lengths = [np.max([len(s) for s in tand_stations]),np.max([len(s) for s in pred_stations])]
    if char_lengths[0]!=char_lengths[1]: 
        max_char_ind = char_lengths.index(max(char_lengths))
        if max_char_ind==0:
            tand_stations = np.array(util.station_trunc(tand_stations))
        elif max_char_ind==1:
            pred_stations = np.array(util.station_trunc(pred_stations))
    indices_pred = np.in1d(pred_stations,tand_stations)
    indices_tand = np.in1d(tand_stations,pred_stations)
    pred_stations = pred_stations[indices_pred]
    tand_stations = pred_stations[indices_tand]
    pred_sorted_indices = np.argsort(pred_stations)
    tand_sorted_indices = np.argsort(tand_stations)
    # Each type should all reference a single location
    for pred in predictors:
        pred.data = pred.data[:,indices_pred]
        pred.data = pred.data[:,pred_sorted_indices]

    for tand in predictands:
        tand.data = tand.data[:,indices_tand]
        tand.data = tand.data[:,tand_sorted_indices]
    
    return pred_stations[pred_sorted_indices]

    
   
def main_camps(control, stations, predictors, predictands):
    """Main driver for mlr.
    """
    all_vars = predictors+predictands
    make_consistent_dims(predictors, predictands)
    aaa = get_aaa(stations, all_vars)
    # Get Station groups
    groups = [[x] for x in stations]
    num_dates = aaa.shape[2]
    q = xprod_new(aaa, num_dates, stations, groups, len(all_vars))
    equations = regress(groups,predictors,predictands,aaa,q,control.regression_parameters)
    return equations

