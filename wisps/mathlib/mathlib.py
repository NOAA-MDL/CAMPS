import numpy as np
from numpy import linalg
import statsmodels.formula.api as smf

def stepregress (xdata, y):
    '''regress binary random variable on a array of explanatory variables

    Regressors are added sequentially, one at a time, by best improvement
    in out-of-sample prediction. If no additional regressor improves the
    prediction then the iteration stops
    '''
    nreg = xdata.shape[0]

    idxincl = []
    idxremain = range(nreg)

    ones = np.ones([365])

    bestcorr = 0
    oldbest = 0
#    print "Before while loop."
    while len(idxremain)>0:
        bestidx = 0
#        print 'remaining', idxremain
        for xidx in idxremain:
            idxuse = idxincl + [xidx]
            x = np.vstack([xdata[idxuse,:],ones]).T
            result = smf.OLS(y,x,missing='drop').fit()
            correctpercent = result.rsquared_adj
            if (correctpercent > bestcorr):
                bestidx = xidx
                bestcorr = correctpercent
                
        if ((bestcorr > oldbest) & (bestcorr - oldbest > 0.005)):
            idxincl.append(bestidx)
            idxremain.remove(bestidx)
            oldbest = bestcorr
            predictors = idxincl
#            print 'added: ', bestidx, 'new correct prediction', bestcorr
        else:
#            print 'no improvement found'
            break
#    print result.rsquared_adj, result.params, idxuse
    if (len(predictors) > 0):
        return result, predictors
    else:
        predictors = []
        print "No predictors found."
        return result, predictors
