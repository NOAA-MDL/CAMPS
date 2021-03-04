import sys
import os
import numpy as np
import pdb


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
    if len(data.shape) > 3:
        out_arr = smooth(data[:,:,:,0], args)
    else:
        out_arr = smooth(data, args)
    w_obj.data = out_arr

    #This smoothing is identified as linear smoothing.
    w_obj.add_process('LinSmooth')
    w_obj.add_metadata('smooth',args)


def smooth(arr, smooth_type):
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
    assert len(arr.shape) == 3

    ndays = arr.shape[0]
    ny = arr.shape[1]
    nx = arr.shape[2]

    # For 81 and 169 point smoothing, apply 25 point smoothing 2x or
    # 3x respectively.
    if smooth_type in [81,169]:
        out = smooth(arr, 25)
        out = smooth(out, 25)
        if smooth_type == 169: smooth(out, 25)
        return out

    if smooth_type == 5 or smooth_type==9:
        window = 1
    elif smooth_type == 25:
        window = 2

    ndays = arr.shape[0]
    len_x = arr.shape[2]
    len_y = arr.shape[1]

    # This loop performs smoothing using the equal-weighted
    # 9-point or 25-point square kernels.
    # Create arrays based on size of desired smoothing and determine bounds
    L = window*2+1
    inter_arr = np.ma.zeros(arr.shape+(L,L))
    cnt_arr = np.ma.zeros(arr.shape,dtype=int)

    left_bound = np.maximum(np.arange(len_x)-window, 0)
    right_bound = np.minimum(np.arange(len_x)+window, len_x-1)
    top_bound = np.maximum(np.arange(len_y)-window, 0)
    bottom_bound = np.minimum(np.arange(len_y)+window, len_y-1)

    # Loop over smoothing points for entire input array
    for i in range(L):
        i_ind = np.minimum(left_bound+i,right_bound)[np.minimum(left_bound+i,right_bound)!=np.minimum(left_bound+i-1,right_bound)]
        x_ind = np.arange(0+int((len_x-i_ind.size)/2),len_x-int((len_x-i_ind.size)/2))
        for j in range(L):
            j_ind = np.minimum(top_bound+j,bottom_bound)[np.minimum(top_bound+j,bottom_bound)!=np.minimum(top_bound+j-1,bottom_bound)]
            y_ind = np.arange(0+int((len_y-j_ind.size)/2),len_y-int((len_y-j_ind.size)/2))
            # If doing 5 point smooth, remove "corners"
            if smooth_type==5:
                valid_inds = np.where(~((j_ind==y_ind-window)[:,None] & (i_ind==x_ind-window)[None,:]) & \
                                      ~((j_ind==y_ind-window)[:,None] & (i_ind==x_ind+window)[None,:]) & \
                                      ~((j_ind==y_ind+window)[:,None] & (i_ind==x_ind-window)[None,:]) & \
                                      ~((j_ind==y_ind+window)[:,None] & (i_ind==x_ind+window)[None,:]))
                inter_arr[:,y_ind[:,None][valid_inds[0],0],x_ind[None,:][0,valid_inds[1]],j,i] = arr[:,j_ind[:,None],i_ind[None,:]][:,valid_inds[0],valid_inds[1]]
                cnt_arr[:,y_ind[:,None][valid_inds[0],0],x_ind[None,:][0,valid_inds[1]]] += 1
            else:
                inter_arr[:,y_ind[:,None],x_ind[None,:],j,i] = arr[:,j_ind[:,None],i_ind[None,:]]
                cnt_arr[:,y_ind[:,None],x_ind[None,:]] += 1

    # Sum array and divide by number of valid points
    sum_arr = inter_arr.sum(axis=(3,4))
    out_arr = sum_arr/cnt_arr

    return out_arr
