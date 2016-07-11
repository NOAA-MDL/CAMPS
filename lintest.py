#!/contrib/anaconda/2.3.0/bin/python

# Test a linear forward regression algorithm.
# Jason Levit, MDL, July 2016

# Declare imports
import csv
import pandas as pd
import numpy as np
import sys
import time
from datetime import datetime, date, timedelta
import calendar
from netCDF4 import Dataset
import statsmodels.formula.api as smf
from forward import forward_selected
from stepreg import stepregress
from scipy import stats
from sklearn import linear_model
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression

model = np.load("model.npy")
obs = np.load("obs.npy")
ones = np.ones([365])

y = obs[0,:,0]

nantest = np.isnan(y)
if (np.all(nantest) != True):
    result, predictors = stepregress(model[:,:,0],y)
print result.rsquared_adj, predictors

