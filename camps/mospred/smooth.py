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
    smooth_5pt
    smooth_point
"""


def smooth_var(w_obj, args):
    """Smooths the first two dimensions of the data in 
    a camps data object w_obj, with the type of
    smoothing indicated by args.
    """

    #Smooth the first two dimensions of the variable's data array
    #and reset it to these two dimensions.
    if len(w_obj.data.shape) == 3:
        out_arr = smooth(w_obj.data[:,:,0], args)
    else:
        out_arr = smooth(w_obj.data[:,:], args)
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
    assert len(arr.shape) == 2
    
    # 9pt smooth twice
    if smooth_type == 81: 
        smooth(arr, 9)
        smooth(arr, 9)
        return arr

    # 9pt smooth thrice
    if smooth_type == 169: 
        smooth(arr, 9)
        smooth(arr, 9)
        smooth(arr, 9)
        return arr

    if smooth_type == 25:
        freedom = 2 #(2*freedom+1) by (2*freedom+1) kernel
    elif smooth_type == 9:
        freedom = 1
    elif smooth_type == 5:
        return smooth_5pt(arr)

    len_x = len(arr[:,0])
    len_y = len(arr[0,:])

    #This loop performs smoothing using the equal-weighted
    #9-point or 25-point square kernels.
    #Create temporary array to contain smoothed values
    out_arr = np.zeros((len_x, len_y))
    for x in range(len_x):
        for y in range(len_y):
            #Account for the kernel being at an edge.
            left_bound = max(x-freedom, 0)
            right_bound = min(x+freedom, len_x-1)
            top_bound = max(y-freedom, 0)
            bottom_bound = min(y+freedom, len_y-1)
            
            #The kernel.
            #+1 because second index is not inclusive.
            sub_arr = arr[left_bound:right_bound+1, top_bound:bottom_bound+1]

            sub_arr_sum = sub_arr.sum()
            smoothed_value = sub_arr_sum/sub_arr.size

            out_arr[x,y] = smoothed_value

    return out_arr


def smooth_5pt(arr):
    """Smooth with an equally-weighted, 5-point cross-shaped kernel."""

    len_x = len(arr[:,0])
    len_y = len(arr[0,:])

    # Create Temp array
    out_arr = np.zeros((len_x, len_y))

    for x in range(len_x):
        for y in range(len_y):
            sub_arr = []
            sub_arr.append(arr[x,y])
            # Top
            if x > 0:
                sub_arr.append(arr[x-1,y])
            if y > 0:
                sub_arr.append(arr[x,y-1])
            if x < len_x-1:
                sub_arr.append(arr[x+1,y])
            if y < len_y-1:
                sub_arr.append(arr[x,y+1])
            avg = sum(sub_arr)/len(sub_arr)
            sub_arr = []
            out_arr[x,y] = avg

    return out_arr


def smooth_point(arr, x, y, freedom, len_x, len_y):
    """returns the value for a point (x,y) in a 
    len_x by len_y arr that is the average of a square 
    kernel centered at the point.  The dimensions of the
    kernel are (2*freedom+1) by (2*freedom+1) points.
    """

    left_bound = max(x-freedom, 0)
    right_bound = min(x+freedom, len_x-1)
    top_bound = max(y-freedom, 0)
    bottom_bound = min(y+freedom, len_y-1)
    sub_arr = arr[left_bound:right_bound+1, top_bound:bottom_bound+1]

    avg = sum(sub_arr)/len(sub_arr)

    return avg
     
    
            





