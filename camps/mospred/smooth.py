import sys
import os
import numpy as np
import pdb

from ..gui.display import display

"""Module: smooth.py
Applies smoothing to two-dimensional data.  Various smoothing
kernels are available.  Some are applied more than once.

Methods:
    smooth_var
    smooth
"""


def smooth_var(w_obj, args):
    """Smooths the first two dimensions of the data in
    a camps data object w_obj, with the type of
    smoothing indicated by args.
    """

    #Smooth the first two dimensions of the variable's data array
    #and reset it to these two dimensions.
    data = w_obj.data
    if len(data.shape) == 3:
        out_arr = smooth(data[:,:,0], args)
    else:
        out_arr = smooth(data, args)
    w_obj.data = out_arr

    #This smoothing is identified as linear smoothing.
    w_obj.add_process('LinSmooth')
    w_obj.add_metadata('smooth',args)


def smooth(a, smooth_type):
    """Given a 2D array arr, smooth with smooth_type.
    Smooth_type can be 5, 9, 25, 81, or 169.
    Smooth_type of 5, 9, and 25 are applied once
    with square smoothing kernels of 5, 9, and 25 equally
    weighted points, respectively.  A smooth_type
    of 81 is applying the 9-point kernel twice and
    a smooth_type of 169 corresponds to applying
    the same kernel thrice.
    """

    smooth_type = int(smooth_type)
    allowable_smoothing = [5,9,25,81,169]
    assert smooth_type in allowable_smoothing
    assert len(a.shape) == 2

    ny = a.shape[0]
    nx = a.shape[1]

    # For 81 and 169 point smoothing, apply 25 point smoothing 2x or
    # 3x respectively.
    if smooth_type in [81,169]:
        out = smooth(a, 25)
        out = smooth(out, 25)
        if smooth_type == 169: smooth(out, 25)
        return out

    if smooth_type == 5:
        window = 1
    elif smooth_type == 9:
        window = 1
    elif smooth_type == 25:
        window = 2
        
    adata = np.ma.getdata(a)
    amask = np.ma.getmaskarray(a)
    out_arr = np.ma.zeros((ny,nx),dtype=a.dtype)

    # Construct a NumPy nditer instance. Iterate over the 2D grid.
    it = np.nditer([adata,out_arr],flags=['multi_index',],op_flags=[['readonly'],['readwrite']])
    if smooth_type == 5:
        for a1,w1 in it:
            j = it.multi_index[0]
            i = it.multi_index[1]
            jrange = np.arange(max(j-window,0),min(j+1+window,ny),2)
            irange = np.arange(max(i-window,0),min(i+1+window,nx),2)
            jdx = np.ix_(jrange,[i])
            idx = np.ix_([j],irange)
            w1[...] = (np.sum(adata[jdx])+np.sum(adata[idx])+adata[j,i])/np.float32(len(irange)+len(jrange)+1)
    else:
        for a1,w1 in it:
            j = it.multi_index[0]
            i = it.multi_index[1]
            jrange = np.arange(max(j-window,0),min(j+1+window,ny))
            irange = np.arange(max(i-window,0),min(i+1+window,nx))
            idx = np.ix_(jrange,irange)
            w1[...] = np.average(adata[idx])

    return out_arr