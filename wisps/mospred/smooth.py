import sys
import os
relative_path = os.path.abspath(
                    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
from gui.display import display
import numpy as np
import pdb


def smooth_var(w_obj, args):
    if len(w_obj.data.shape) == 3:
        out_arr = smooth(w_obj.data[:,:,0], args[0])
    else:
        out_arr = smooth(w_obj.data[:,:], args[0])
    w_obj.data = out_arr
    w_obj.add_process('LinSmooth')


def smooth(arr, smooth_type):
    """Given a 2D array, smooth with smooth_type.
    Smooth_type can be 5, 9, 25, 81, or 169.
    """
    #display(arr)
    smooth_type = int(smooth_type)
    allowable_smoothing = [5,9,25,81,169]
    assert smooth_type in allowable_smoothing
    assert len(arr.shape) == 2
    
    # 25pt smooth twice
    if smooth_type == 81: 
        smooth(arr, 9)
        smooth(arr, 9)
        return arr

    # 25pt smooth thrice
    if smooth_type == 169: 
        smooth(arr, 9)
        smooth(arr, 9)
        smooth(arr, 9)
        return arr

    if smooth_type == 25:
        freedom = 2
    elif smooth_type == 9:
        freedom = 1
    elif smooth_type == 5:
        return smooth_5pt(arr)

    len_x = len(arr[:,0])
    len_y = len(arr[0,:])

    # Create Temp array
    out_arr = np.zeros((len_x, len_y))

    for x in range(len_x):
        for y in range(len_y):
            # Compute sum for each point surrounding it.
            left_bound = max(x-freedom, 0)
            right_bound = min(x+freedom, len_x-1)
            top_bound = max(y-freedom, 0)
            bottom_bound = min(y+freedom, len_y-1)
            
            # +1 because second index is not inclusive.
            sub_arr = arr[left_bound:right_bound+1, top_bound:bottom_bound+1]

            sub_arr_sum = sub_arr.sum()
            smoothed_value = sub_arr_sum/sub_arr.size

            out_arr[x,y] = smoothed_value
    
    #display(out_arr)
    return out_arr

def smooth_5pt(arr):
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
    """
    returns the value for a point (x,y) in arr that is the average of 'freedom' 
    number of points surrounding it
    """
    sum = 0
    left_bound = max(x-freedom, 0)
    right_bound = min(x+freedom, len_x-1)
    top_bound = max(y-freedom, 0)
    bottom_bound = min(y+freedom, len_y-1)
     
    
            





