#!/usr/bin/env python

__version__ = '1.0.0'
import fortranfile as ff
import numpy as np
import os
import struct
import sys
import tdlpack

# ---------------------------------------------------------------------------------------- 
# Class: TdlpackRecord
# ---------------------------------------------------------------------------------------- 
class TdlpackRecord(object):
    def __init__(self,**kwargs):
        """
  create a TdlpackRecord class instance given a TDLPACK file
        """
        for k,v in kwargs.items():
            setattr(self,k,v)

        self.tdlpack_record_length = self.indicator_section[1]
        self.tdlpack_version_number = self.indicator_section[2]
        self.year = self.product_definition_section[2]
        self.month = self.product_definition_section[3]
        self.day = self.product_definition_section[4]
        self.hour = self.product_definition_section[5]
        self.minutes = self.product_definition_section[6]
        self.date = self.product_definition_section[7]
        self.id_word1 = self.product_definition_section[8]
        self.id_word2 = self.product_definition_section[9]
        self.id_word3 = self.product_definition_section[10]
        self.id_word4 = self.product_definition_section[11]
        self.id = [self.id_word1,self.id_word2,self.id_word3,self.id_word4]
        self.forecast_hour = self.product_definition_section[12]
        self.model_id = self.product_definition_section[14]
        self.decimal_scale_factor = self.product_definition_section[16]
        self.plain_language = self.setPlainLanguage()

    def __repr__(self):
        strings = []
        keys = self.__dict__.keys()
        keys.sort()
        for k in keys:
            if not k.startswith('_'):
                strings.append('%s = %s\n'%(k,self.__dict__[k]))
        return ''.join(strings)

    def setPlainLanguage(self):
        nchars=self.product_definition_section[21]
        plainLang=''
        for n in range(nchars):
            i=int(self.product_definition_section[22+n])
            plainLang=plainLang+chr(i)
        return plainLang

    def unpackData(self):
        igive = 2
        moctet = np.zeros(1,dtype='int32',order='F')
        data=np.zeros(self.nvalues,dtype='float32',order='F')
        iret = tdlpack.unpack4(self.ipack,igive,self.product_definition_section,\
                               self.grid_definition_section,self._is4Pos,\
                               self.data_section,data)
        #iret = tdlpack.unpack5(self.ipack,self._is4Pos)
        if iret == 0 and self.nvalues == self.data_section[2]: return data

    values = property(unpackData) 

# ---------------------------------------------------------------------------------------- 
# Function TdlpackDecode
# ---------------------------------------------------------------------------------------- 
def TdlpackDecode(filename,dates=[],ids=[]):
    """
 Read the contents of a TDLPACK file.
    """

    # Open file and set its file size.
    f = ff.FortranFile(filename,'>')
    f.seek(0,os.SEEK_END)
    fsize = f.tell()
    f.seek(0)

    # Initialize lists
    ccalls = []
    nstas = []
    tdlps = []

    # Initialize NumPy arrays
    is0 = np.zeros(54,dtype='int32',order='F')
    is1 = np.zeros(54,dtype='int32',order='F')
    is2 = np.zeros(54,dtype='int32',order='F')
    is4 = np.zeros(54,dtype='int32',order='F')
    moctet = np.zeros(1,dtype='int32',order='F')

    # Iterate through the file
    cnt = 0
    igive = 1
    nccall = 0
    while 1:

        isTDLP = False

        # Check for at EOF
        if fsize == f.tell(): break 

        # Read using fortranfile.readInts() method.  This is the Python equivlent
        # to Fortran's READ statement. rec contains the entire Fortran record.
        # ioctet is the 8-byte integer that is the TDLPACK record size in bytes.
        # ipack becomes the TDLPACK record.
        rec = f.readInts()
        ioctet = struct.unpack('>q',rec[0:2])[0]
        ipack = rec[2:]

        # When ipack[0] = 0, its the trailer record and there is no need to
        # do anything with this record.
        if ipack[0] == 0:
            ccall = []
            continue

        kwargs = {}

        # Determine the record type.  Above we are already checking for a trailer
        # record so the below checks are for a TDLPACK record and station CALL
        # letter record.
        #
        # If we come here, then we need to check the first 4-bytes of the TDLPACK
        # record for the "TDLP" string. Since TDLPACK is big-endian, on a 
        # little-endian system, the TDLPACK identifying string will appear as "PLDT".
        tdlpHeader = struct.unpack('<4s',ipack[0])[0]
        if sys.byteorder == 'big' and tdlpHeader == 'TDLP' or \
           sys.byteorder == 'little' and tdlpHeader == 'PLDT':

            # Before unpacking begins check to see is a date and/or id list has been
            # passed into this function. If so, then check the date and ID from ipack
            # against dates and IDs in their lists.
            cnt = 0
            if dates: cnt = dates.count(ipack[4])
            if cnt > 0: cnt = ids.count(list(ipack[5:9]))

            # If cnt == 0, then the TDLPACK record is ted given the dates and/or
            # IDs -- iterate.
            if (dates or ids) and cnt == 0: continue
           
            # Let the function know this is a TDLPACK record and to set ipack
            # instance variable.
            isTDLP = True
            kwargs['ipack'] = np.copy(ipack)

            # Unpack sections 0 and 1.
            iret = tdlpack.unpack0(ipack,moctet,is0)
            iret = tdlpack.unpack1(ipack,moctet,is1)

            # Determine whether the data are gridded.  If so, then unpack
            # Section 2 (Grid Definition Section).
            #
            #    IMPORTANT: nvalues is set here.  The value should match
            #    is4[2] (3rd value).  This will be checked when method
            #    unpackData() is called.
            if is1[1] & 1:
                # TDLPACK Gridded Record
                iret = tdlpack.unpack2(ipack,moctet,is2)
                kwargs['nvalues'] = is2[2]*is2[3]
                kwargs['ccall'] = []
                kwargs['nsta'] = 0
                kwargs['nccall'] = 0
            else:
                # TDLPACK Vector Record
                kwargs['nvalues'] = nstas[len(nstas)-1]
                kwargs['nsta'] = nstas[len(nstas)-1]
                kwargs['ccall'] = ccalls[len(ccalls)-1]
                kwargs['nccall'] = nccall

            # Data section will be unpacked using method unpackData(). Here
            # we just need to know the beginning position of Section 4.
            kwargs['_is4Pos'] = np.copy(moctet)

            # Populate kwargs. Even though we have notunpacked section 4, 
            # we need to save the empty array for each instance.
            #    IMPORTANT: Use np.copy()!
            kwargs['indicator_section'] = np.copy(is0)
            kwargs['product_definition_section'] = np.copy(is1)
            kwargs['grid_definition_section'] = np.copy(is2)
            kwargs['data_section'] = np.copy(is4)

        else:

            # Record contains station call letter records.  Catalog them.
            nsta = ioctet/8
            ccall = []
            for n in range(0,len(ipack),2):
                ccall.append(struct.unpack('>8s',ipack[n:n+2])[0].strip(' '))
            nstas.append(nsta)
            ccalls.append(ccall)
            nccall += 1

        # Append TdlpackRecord instance to return list.
        if isTDLP: tdlps.append(TdlpackRecord(**kwargs))

    f.close()

    return tdlps # Return from function TdlpackDecode

# ---------------------------------------------------------------------------------------- 
# End of pytdlpack.py
# ---------------------------------------------------------------------------------------- 
