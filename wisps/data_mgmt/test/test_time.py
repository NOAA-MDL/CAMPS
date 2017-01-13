#!/usr/bin/env python

import os, sys
relative_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+"/..")
sys.path.insert(0, relative_path)
from datetime import datetime
from datetime import timedelta
import Time

num_passed = 0

def passed():
    global num_passed
    print "passed", num_passed
    num_passed += 1

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
       
   

test_epoch_time()



