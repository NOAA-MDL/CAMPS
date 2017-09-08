#!/usr/bin/env python
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import fetch
import pdb


def test_fetch():
    """Test fetch function"""
    # Create metadata dictionary of variable that should be pulled.
    metadata = {'property':'Temp', 
                'vert_coord1' : 500}
    w_obj = fetch.fetch(**metadata)
    assert w_obj

    metadata = {'property':'StatPP/Data/Temp', 
                'vert_coord1' : 500}
    w_obj2 = fetch.fetch(**metadata)
    assert w_obj.data.all() == w_obj2.data.all()
    

if __name__ == "__main__":
    test_fetch()
    print "fetch passed"
    
