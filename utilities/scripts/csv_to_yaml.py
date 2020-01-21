#!/usr/bin/env python
import csv
import sys
"""Converts csv file from codes registry to the format in ObservedProperties.yaml file. 
"""


if len(sys.argv) < 2:
    print "Need more aguments"
    raise Exception
filename = sys.argv[1]

reader = csv.reader(open(filename))

for i,row in enumerate(reader):
    if i == 0:
        continue
    print "'" + row[2]+"'",':', "'" + row[0] + "'"

