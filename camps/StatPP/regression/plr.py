import sys
import numpy as np
import pdb
import logging
from ...core import util as util


def get_aaa(stations, predictors):
    """aaa is a 3D data array used in xprod and plr. When returned, aaa is
       dimensioned by [number_of_vars, number_of_stations, number_of_dates].
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
            aaa = np.dstack((aaa,cur_data))

    return aaa.T


def xprod(regression_params, aaa, num_dates, stations, groups, num_vars):

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

    # Matrix b will hold content of aaa after replacing missing values 9999 with zero
    # values and shifting variables to start from index 1 instead of zero. Only 
    # variables start with index 1. Other indices (for stations, dates, groups)
    # start from zero.
    b = np.zeros((nvrbl+1,num_stations,ndates),dtype='float32',order='F')
    for nv in range(nvrbl):
        b[nv+1,:,:]=aaa[nv,:,:]

    # Size arrays accordingly
    smpl = np.zeros((num_groups),dtype='float64',order='F')
    sums = np.zeros((num_groups,nvrbl+1),dtype='float64',order='F')
    sumx = np.zeros((num_groups,nvrbl+1,nvrbl+1),dtype='float64',order='F') # now full square matrix
    tmp  = np.zeros((nvrbl+1,nvrbl+1),dtype='float64',order='F')

    print("Shape of smpl = ",smpl.shape)
    print("Shape of sums = ",sums.shape)
    print("Shape of sumx = ",sumx.shape)
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
                
                if np.count_nonzero(b[:,loc,nd]==9999.0) == 0:
                    smpl[ng] += 1.0
                else:
                    b[:,loc,nd] = 0.0
                    continue

                # The portion of b for given location and date that is used in
                bld=np.copy(b[:,loc,nd])

                # Calc sum for each variable over all stations in the group and dates
                for nv in range(1,nvrbl+1):
                    sums[ng,nv] += bld[nv]

                # For two variables nv and nvv calculate their dot product over
                # all stations in the group and dates
                # Compute daigonal plus one triangle of the matrix sumx of dot products
                for nv in range(1,nvrbl+1):
                    bnvld=bld[nv]
                    for nvv in range(nv,nvrbl+1):
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

    nst = regression_params['nst']       # Number of predictors to select.
    mforce = regression_params['mforce'] # Number of predictors to force.
    nselt = regression_params['nselt']   # Selection method.
    nsmeth = regression_params['nsmeth'] # Stopping method.
    #necvrb = regression_params['necvrb'] # Number of values required for a variable to be used.
    neccas = regression_params['neccas'] # Number of cases required for an equation to be developed.
    cutoff = regression_params['cutoff'] # The reduction of variance necessary for adding a predictor.
    forcut = regression_params['forcut'] # The reduction of variance necessary for adding a forced predictor.
    varnb = regression_params['varnb']   # Variance necessary for a point binary to be used.
    varngb = regression_params['varngb'] # Variance necessary for a grid binary to be used.
    coln = regression_params['coln']     # Remaining RV of a continuous predictor for it to be selected
    colnb = regression_params['colnb']   # Remaining RV of a point binary predictor for it to be selected
    colngb = regression_params['colngb'] # Remaining RV of a grid binary predictor for it to be selected

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

    #lp = np.zeros((5,nvrbl+1),dtype='int32',order='F')
    #slp = np,.zeros((5,nvrbl+1),dtype='float32',order='F')

    avg = np.zeros((nvrbl+1),dtype='float64',order='F') # Arithmetic average for each variable.
    const = np.zeros((ntand+1),dtype='float64',order='F')  # variances of predictands
    const_1 = np.zeros((ntand+1),dtype='float64',order='F') # reciprocal values of const
    p = np.zeros((nvrbl+1,nvrbl+1),dtype='float64',order='F') # matrix of covariances
    # that gets transformed using Gaussian elimination to determine regression coefficients
    # corresponding to knt predictors
    ptmp =  np.zeros((nvrbl+1),dtype='float64',order='F') # temporary array
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

    # Init Equations
    equations = []
    for ng,group in enumerate(groups):
        equations.append({'stations' : group})
        equations[ng]['predictors'] = []
        equations[ng]['constant'] = []
        equations[ng]['coefs'] = [np.zeros((ntand), dtype='int32')]*npred
        equations[ng]['ancil'] = {}

    eq_list = []

    # Begin iteration over groups
    for ng,g in enumerate(groups):

        a = np.zeros((ntand+1),dtype='float64',order='F') # regression constants
        corr = np.zeros((ntand+1),dtype='float64',order='F') # multiple correlation coefficient
        ess = np.zeros((ntand+1),dtype='float64',order='F') # standard error estimate
        rdvr = np.zeros((ntand+1),dtype='float64',order='F') # coefficient of determination

        # CHECK: Number of cases (neccas) for equation development.
        if q[0][ng] <= neccas:
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
        print((" %6d TOTAL CASES FOR REGRESSION ANALYSIS\n" % (q[0][ng])))
        sys.stdout.flush()

        # Initialize lp for each equation group, this assumes the ids
        # are listed first.
        # for n in range(1,npred+1):
        #     lp[0,n] = n
        #     lp[1,n] = int(ids[n-1][0])
        #     lp[2,n] = int(ids[n-1][1])
        #     lp[3,n] = int(ids[n-1][2])
        #     lp[4,n] = int(ids[n-1][3])

        # Make predictor list hold index associated with predictor place
        for n in range(1, len(predictors)):
            predictor_list[n] = n # make predictor list hold index associated with predictor place

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
        sig = np.copy(stddev)

        # CHECK: Check variances of point and grid binary predictors against their
        #        thresholds varnb and varngb, respectively.
        for n in predictor_list:
            if "BinaryGrid" in predictors[n].SOSA__usedProcedure:
                # ADD logging...
                if stddev[n]**2.0 < varngb:
                    for nn in predictor_list:
                        p[n,nn] = 0.0
                        p[nn,n] = 0.0
                    stddev[n] = 0.0
                    sig[n] = 0.0
                    var[n] = 0.0
            elif "BinaryPoint" in predictors[n].SOSA__usedProcedure:
                # ADD logging...
                if stddev[n]**2.0 < varnb:
                    for nn in predictor_list:
                        p[n,nn] = 0.0
                        p[nn,n] = 0.0
                    stddev[n] = 0.0
                    sig[n] = 0.0
                    var[n] = 0.0

        # Initially, set sig to stddev, then for predictors only, set sig
        # to diagonal elements of p, each being the sum of squares for that variable.
        sig[1:npred+1] = var[1:npred+1]

        # Deal with binary predictands...not yet. For now, just put some data
        # into const.
        const[1:ntand+1] = np.copy(var[npred+1:nvrbl+1])
        if 0 not in const[1:ntand+1]:
            const_1[1:ntand+1] = np.reciprocal(const[1:ntand+1])

        # --------------------------------------------
        # ----- REGRESSION SCREENING BEGINS HERE -----
        # --------------------------------------------

        # IMPORTANT: The "*x" versions of regression parameters are for each equation group.
        nstx = min(npred,nst)
        colnx = coln
        colnbx = colnb
        colngbx = colngb

        # The below while loop will run until a predictors reduction of
        # variance does not exceed cutoff
        k = 0
        knt = 0  # number of predictors chosen
        done = False
        while (not done and k < nstx):

            # Choose next predictor 'key' to add to the regression
            # p[rng,rngd] is submatrix d_k of transformend P after Gaussian elimination on columns 1 to k
            rng = list(range(k+1,npred+1)) # range of reminaing predictors in p
            rngd = list(range(npred+1,nvrbl+1))     # predictand range in p
            rngc = list(range(1,ntand+1))  # predictand range in const, vh

            # Perform colinearity test
            # IMPORTANT: Here we need to determine if predictor is continuous,
            #            point binary, or grid binary and use the appropriate
            #            colnx, colnbx, or colgbx.
            coln_test = colnx
            cor2 = 0.0*cor2
            for l in rng:
                # Use l-1, but might have to used l-ntand....maybe
                if "BinaryGrid" in predictors[l-1].SOSA__usedProcedure:
                    coln_test = colngbx
                elif "BinaryPoint" in predictors[l-1].SOSA__usedProcedure:
                    coln_test = colnbx
                else:
                    coln_test = colnx

                if (p[l,l]>0.0 and sig[l]>0.0 and p[l,l]>coln_test*sig[l]):
                    pll_1=1.0/p[l,l]
                    cor2[l,rngd] = pll_1*np.multiply(p[[l],:][:,rngd],p[[l],:][:,rngd])

            cor2[:,rngd] = np.multiply(cor2[:,rngd],const_1[rngc])

            # find 'key' as the predictor with strongest (anti)correlation with one of the predictands
            cor2maxl = np.amax(cor2, axis=1)
            vht      = np.amax(cor2maxl)
            key      = np.argmax(cor2maxl)

            # This replicates Do 525.
            vh[rngc] = np.copy(cor2[[key],:][:,rngd])
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
                ess[rngc] = np.copy(np.diag(p[rngd,:][:,rngd]))
                ess = np.where(ess>0, ess, 0)
                ess = np.sqrt(1.0/q[0][ng]*ess)

                # coefficient of determination
                # which is proportion of variablity of predictand that can
                # be attributed to variability in predictiors selected fo far
                rdvr[rngc] = np.copy(sig[rngd])
                rdvr[rngc] = np.true_divide (1.0/q[0][ng],np.multiply(rdvr[rngc],rdvr[rngc]))
                rdvr[rngc] = 1.0- np.multiply(np.diag(p[rngd,:][:,rngd]),rdvr[rngc])
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
        if var.dimensions.index('stations') == 0:
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
    tand_stations = tand_stations[indices_tand]
    pred_sorted_indices = np.argsort(pred_stations)
    tand_sorted_indices = np.argsort(tand_stations)
    # Each type should all reference a single location
    for pred in predictors:
        pred.data = pred.data[:,indices_pred]
        pred.data = pred.data[:,pred_sorted_indices]
        pred.location.set_stations(pred_stations[pred_sorted_indices])

        pred.location.set_stations(pred_stations[pred_sorted_indices])

    for tand in predictands:
        tand.data = tand.data[:,indices_tand]
        tand.data = tand.data[:,tand_sorted_indices]
        tand.location.set_stations(tand_stations[tand_sorted_indices])

    return pred_stations[pred_sorted_indices]


def main_camps(control, predictors, predictands):
    """Main driver for mlr.
    """
    all_vars = predictors+predictands
    stations = make_consistent_dims(predictors, predictands)
    aaa = get_aaa(stations, all_vars)
    aaa = np.ma.masked_greater_equal(aaa,9999)
    # Get Station groups
    groups = [[x] for x in stations]
    num_dates = aaa.shape[2]
    q = xprod(control.regression_parameters, aaa, num_dates, stations, groups, len(all_vars))
    equations = regress(groups,predictors,predictands,aaa,q,control.regression_parameters)
    return equations
