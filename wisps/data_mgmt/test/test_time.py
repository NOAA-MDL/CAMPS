#!/usr/bin/env python

import os, sys
relative_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+"/..")
sys.path.insert(0, relative_path)
from datetime import datetime
from datetime import timedelta
import Time
from netCDF4 import Dataset
import pdb
import numpy as np

num_passed = 0

def test_PhenomenonTime():
    start_time = get_start_date()
    end_time = get_end_date()
    stride = Time.ONE_HOUR
    time = Time.PhenomenonTime(start_time, end_time, stride)
    test_time = Time.epoch_to_datetime(time.data[24])
    correct_time = datetime(2013, month=4,day=13)
    assert test_time == correct_time

    print "Passed test_PhenomenonTime"

def test_ValidTime():
    start_time = get_start_date()
    end_time = get_end_date()

    # Test unlimited valid
    time = Time.ValidTime(start_time, end_time, offset=0)
    test_time = time.data
    correct_time =  np.zeros(test_time.shape)
    correct_time[:] = None
    np.testing.assert_array_equal(correct_time, test_time)

    # Test fixed date valid 
    fixed_time = datetime(2012,07,04)
    time = Time.ValidTime(start_time, end_time, offset=fixed_time)
    test_time = time.data
    correct_time =  np.zeros(test_time.shape)
    correct_time[:] = Time.epoch_time(fixed_time)
    np.testing.assert_array_equal(correct_time, test_time)

    # Test 

    print "Passed test_ValidTime"

def test_get_stride():
    start_time = datetime(2016, 4, 5, 0, 0)
    end_time =  datetime(2016, 4, 15, 0, 0)
    time = Time.Time(start_time, end_time, Time.ONE_HOUR)
    stride = time.get_stride(True)
    correct_stride = timedelta(seconds=Time.ONE_HOUR)
    assert correct_stride == stride
    stride = time.get_stride()
    correct_stride = seconds=Time.ONE_HOUR
    assert correct_stride == stride
    print "Passed test_get_stride"

def test_epoch_time():
   epoch = datetime.utcfromtimestamp(0)
   seconds_from_epoch = Time.epoch_time(epoch)
   assert seconds_from_epoch == 0

   epoch_plus_hour = epoch + timedelta(hours=1)
   seconds_from_epoch = Time.epoch_time(epoch_plus_hour)
   assert seconds_from_epoch == Time.ONE_HOUR

   try:
       Time.epoch_time(int(42))
       raise Exception("Something's wrong. function shouldn't accept ints")
   except:
       pass
   print "Passed test_epoch_time"

def test_eq():
    t1 = Time.PhenomenonTime(get_start_date(), get_end_date())
    t2 = Time.PhenomenonTime(get_start_date(), get_end_date())

    assert t1 == t2
    print "Passed equality test"

def get_nc():
    Dataset.open('test.nc', 'w')

def get_start_date():
    return datetime(year=2013, month=4, day=12)
    
def get_end_date():
    return datetime(year=2013, month=5, day=12)



test_get_stride()
test_epoch_time()
test_PhenomenonTime()
test_ValidTime()
test_eq()

