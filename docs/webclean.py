#!/usr/bin/env python
import os
import sys
import numpy as np
from filecmp import dircmp
import shutil


def main():
    #set which two directories we are comparing
    build = '/home/eschlie/repositories/wisps/docs/build/html'
    webdir = '/mnt/project/users/wisps'
    #exception, this dir should be in the webdir and not in build
    ex = 'pdf'
    #compare the directories
    dcmp = dircmp(build, webdir)
    diff_list = dcmp.right_only

    #loop over list of files or directories that exist in webdir 
    #but not in the source build directory
    for diff in diff_list:
        print 'removing content that does not exist in our source directory'
        if diff == ex: continue #ignore our exception directory
        if diff != ex:
            #if it is a directory, remove it
            if os.path.isdir(webdir+'/'+diff):
                print 'removing directory: ', webdir+'/'+diff
                shutil.rmtree(webdir+'/'+diff)
            #if it is a file, remove it
            if os.path.isfile(webdir+'/'+diff):
                print 'removing file: ', webdir+'/'+diff
                os.remove(webdir+'/'+diff)
    print 'done removing files and/or directories' 
    
if __name__ == '__main__':
    main()    
        


