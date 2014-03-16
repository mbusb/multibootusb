#! /usr/bin/python

""" ISO9660fs
Dump raw meta data of iso9660 file system.
Extract directories and files.
"""
##
## Extract directory or file from iso.
## Support RRIP.
## 

# Author : LiQiong Lee

import sys
import struct
import os
import re
import stat
import var
from ctypes import *

BLOCK_SIZE = 2048
S_IFSOCKET = 0o140000
S_IFLINK   = 0o120000
S_IFREG    = 0o100000
S_IFBLK    = 0o060000
S_IFCHR    = 0o020000
S_IFDIR    = 0o040000
S_IFIFO    = 0o010000

E_SUCCESS = 0
E_FAILURE = -1
E_DEVICEFILE = -2  # can't write device file

class PrimaryVolume(Structure):
   def  __init__(self):
       self.sysIdentifier = ""
       self.volIdentifier = ""
       self.volSize   = 0
       self.volSeq    = 0
       self.blockSize = 0
       self.ptSize    = 0
       self.ptLRd     = 0
       self.fsVer     = 0
       self.rootLoc   = 0
       self.rootTotal = 0

class Rrip(Structure):
    def __init__(self):
        self.offset  =  -1
        self.altname = ""
        self.devH    =  0
        self.devL    =  0
        self.fMode   =  0

class DirRecord(Structure):
    def __init__(self):
       self.lenDr    =    0
       self.lenEattr =    0
       self.locExtent=    0
       self.lenData  =    0
       self.dtYear   =    0
       self.dtMonth  =    0
       self.dtHour   =    0
       self.dtMinute =    0
       self.dtSecond =    0
       self.dtOffset =    0
       self.fFlag    =    0
       self.fUnitSize=    0
       self.gapSize  =    0
       self.volSeqNr =    0
       self.lenFi    =    0
       self.fIdentifier = ""
       self.sysUseStar = 0
       self.suspBuf =  ""
       self.rrip = None
               
class PathTabelItem(Structure):
    def __init__(self):
    	self.lenDi =       0
        self.lenEattr =    0
        self.locExtent =   0
        self.pdirNr =      0
        self.fIdentifier = ""

class ISO9660:
    """
    This class can dump iso9660 file system meta data and extract files.
    Support:
        RRIP extension.
    """

    def __init__(self, isofile):
        try:
            f = open(isofile, 'rb')
        except(IOError):
            sys.stderr.write("can't open {0}".format(isofile))
            sys.exit(-1)
        
        self.isoFile = f
        self.priVol = None
        self.rootDir = None
        self.rripOffset = -1

        desc_nr = 0;
        while True:
            desc_nr = desc_nr + 1;
            self.isoFile.seek(BLOCK_SIZE*(15+desc_nr))
            volume_dsc = self.isoFile.read(BLOCK_SIZE)
            flag = struct.unpack('B',volume_dsc[0])[0]
            if flag == 1:
                self.__readPrimaryVolume__(volume_dsc)
                continue
            if flag == 255:
                break;

    def __del__(self):
        self.isoFile.close()

    def __readPrimaryVolume__(self, volume_dsc):
        """ Dump primary volume descriptor """
        global BLOCK_SIZE
        priVol = PrimaryVolume()
        priVol.sysIdentifier = volume_dsc[8:40]
        priVol.volIdentifier = volume_dsc[40:72]
        priVol.volSize = struct.unpack('<L',volume_dsc[80:84])[0]
        priVol.volSeq = struct.unpack('<H',volume_dsc[124:126])[0]
        priVol.blockSize = struct.unpack('<H',volume_dsc[128:130])[0]
        priVol.ptSize = struct.unpack('<L',volume_dsc[132:136])[0]
        priVol.ptLRd = struct.unpack('<L',volume_dsc[140:144])[0]
        priVol.fsVer = struct.unpack('B', volume_dsc[881])[0]
        dirRec = self.readDirrecord(volume_dsc[156:190])
        priVol.rootLoc = dirRec.locExtent
        priVol.rootTotal = dirRec.lenData
        BLOCK_SIZE = priVol.blockSize

        # Check RRIP
        #print "loc extent(%d)"%(dirRec.locExtent)
        self.priVol = priVol # readDirItems will use self.priVol
        root_dir = self.readDirItems(dirRec.locExtent, priVol.rootTotal)[0]        
        rripNode = self.__rripLoop__(root_dir.suspBuf, root_dir.lenDr-root_dir.sysUseStar)
        if rripNode.offset != -1:
            self.rripOffset = rripNode.offset
            print "RRIP: rrip_offset %d"%(self.rripOffset)
        else:
            print " This disc don't support RRIP"
        self.rootDir = root_dir

    #  Rrip extension
    def __rripLoop__(self, desc_buf, len_buf):
    
        if self.rripOffset > 0:
            entry_buf = desc_buf[self.rripOffset:]
            print "__rripLoop__ offset:%d"%(self.rripOffset)
        else:
            entry_buf = desc_buf
        
        rr = Rrip()
        while True:
            ce_blk = 0
            ce_len = 0
            ce_off = 0
            head = 0
            len_entry = 0
    
            while True:
                head += len_entry
                #print ("\n%d, %d\n")%(len_buf, head)
                if len_buf - head < 4: # less than one entry
                    break;
                entry_buf = entry_buf[len_entry:]
    
                sig1 = struct.unpack("B", entry_buf[0])[0]
                sig2 = struct.unpack("B", entry_buf[1])[0]
                len_entry = struct.unpack("B", entry_buf[2])[0]
                ver = struct.unpack("B", entry_buf[3])[0]
                #print "Got a entry in __rripLoop__ (%c,%c) of SUSP with length:(%d),version:(%d)-->"%(sig1,sig2,len_entry, ver),
    
                if sig1 == ord('S') and sig2 == ord('P'):
                    ck1 = struct.unpack("B", entry_buf[4])[0]
                    ck2 = struct.unpack("B", entry_buf[5])[0]
                    skip = struct.unpack("B", entry_buf[6])[0]
                    #print "-->(0x%x==0xBE,0x%x==EF,%d)" %(ck1, ck2, skip)
                    if ck1 == 0xBE and ck2 == 0xEF:
                        rr.offset = skip
                    continue
    
                if sig1 == ord('C') and sig2 == ord('E'):
                    ce_blk = struct.unpack("<L", entry_buf[4:8])[0]
                    ce_off = struct.unpack("<L", entry_buf[12:16])[0]
                    ce_len = struct.unpack("<L", entry_buf[20:24])[0]
                    #print "-->(%d,%d,%d)" %(ce_blk, ce_off, ce_len)
                    continue
    
                if sig1 == ord('N') and sig2 == ord('M'):
                    flag = struct.unpack("B", entry_buf[4])[0]
                    #print "-->(flag:(0x%x), name:(%s))" %(flag, entry_buf[5:len_entry])
                    if flag == 0x02:     # FLAG_CURRENT
                        rr.altname += "."
                    elif flag == 0x04:   # FLAG_PARENT
                        rr.altname += ".."
                    elif flag == 0x01 or flag ==0:  # 1:FLAG_CONTINUE
                        rr.altname += entry_buf[5:len_entry]                
                    continue
    
                if sig1 == ord('P') and sig2 == ord('N'):
                    rr.devH = struct.unpack("<L", entry_buf[4:8])[0]
                    rr.devL = struct.unpack("<L", entry_buf[12:16])[0]
                    continue
    
                if sig1 == ord('E') and sig2 == ord('R'):
                    len_id = struct.unpack("B", entry_buf[4])[0]
                    len_des = struct.unpack("B", entry_buf[5])[0]
                    len_src = struct.unpack("B", entry_buf[6])[0]
                    ext_ver = struct.unpack("B", entry_buf[7])[0]
                    continue
    
                if sig1 == ord('P') and sig2 == ord('X'):
                    rr.fMode = struct.unpack("<L", entry_buf[4:8])[0]
                    s_link = struct.unpack("<L", entry_buf[12:16])[0]
                    uid = struct.unpack("<L", entry_buf[20:24])[0]
                    gid = struct.unpack("<L", entry_buf[28:32])[0]
                    continue
    
                if sig1 == ord('S') and sig2 == ord('T'):
                    return rr
    
                #print "\n"
            # while (True) end #
    
            if ce_len > 0:
                #print " Read CE block, (%d, %d, %d)"%(ce_blk, ce_len, ce_off)
                self.isoFile.seek(ce_blk*BLOCK_SIZE + ce_off)
                entry_buf = self.isoFile.read(ce_len)
                len_buf = ce_len
            else:
                break
        # while (True) end #
        return rr


    def searchDir(self, path):
        # /root/abc/ - ['', 'root', 'abc', '']
        # /root/abc  - ['', 'root', 'abc']
        # /          - ['', '']
        dircomps = path.split('/')
        if dircomps[-1] == '':
            dircomps.pop()
        if dircomps == []:
            print "you want dump iso:/ ?" 
            return
    
        if len(dircomps) == 1:
            return self.rootDir
    
        pdir_loc = self.priVol.rootLoc
        pdir_len = self.priVol.rootTotal
        i_dircomp = 1
    
        while True:
            found = False
            dirs = self.readDirItems(pdir_loc, pdir_len)
            for item in dirs:
                if item.fIdentifier == dircomps[i_dircomp]:
                    pdir_loc = item.locExtent
                    pdir_len = item.lenData
                    found = True                
                    #print "found (%s)"%(dircomps[i_dircomp])
                    break
            if found: # advacne
                if i_dircomp < len(dircomps)-1:
                    i_dircomp = i_dircomp + 1
                else:
                    return item
            else:                    
                print "can't find " + dircomps[i_dircomp]
                return None

    def readDirrecord(self, desc_buf):
        """ Dump file  dirctory record
        Return a directory record reading from a Directory Descriptors.
        """
        dirRec = DirRecord()
        dirRec.lenDr = struct.unpack("B", desc_buf[0])[0]
        if dirRec.lenDr == 0:
            return None;
    
        dirRec.lenEattr = struct.unpack("B", desc_buf[1])[0]
        dirRec.locExtent = struct.unpack("<L", desc_buf[2:6])[0]
        dirRec.lenData = struct.unpack("<L", desc_buf[10:14])[0]
        dirRec.fFlag = struct.unpack("B", desc_buf[25])[0]
        dirRec.fUnitSize = struct.unpack("B", desc_buf[26])[0]
        dirRec.gapSize = struct.unpack("B", desc_buf[27])[0]
        dirRec.volSeqNr = struct.unpack("<H", desc_buf[28:30])[0]
        dirRec.lenFi = struct.unpack("B", desc_buf[32])[0]
        dirRec.fIdentifier = ""
        if dirRec.lenFi == 1:
            dirRec.fIdentifier  = struct.unpack("B", desc_buf[33])[0]
            if dirRec.fIdentifier  == 0:
                dirRec.fIdentifier = "."
            elif dirRec.fIdentifier == 1:
                dirRec.fIdentifier = ".."
        else:
            dirRec.fIdentifier = desc_buf[33:33+dirRec.lenFi]
            idx = dirRec.fIdentifier.rfind(";")
            if idx != -1:
                dirRec.fIdentifier = dirRec.fIdentifier[0:idx]
    
        dirRec.suspBuf = ""
        dirRec.sysUseStar = 34 + dirRec.lenFi -1
        if dirRec.lenFi % 2 == 0:
            dirRec.sysUseStar += 1
        
        # Extension Attribute
        if dirRec.lenDr > dirRec.sysUseStar+4:
            if dirRec.locExtent == self.priVol.rootLoc:
                dirRec.suspBuf = desc_buf[dirRec.sysUseStar:dirRec.lenDr]
            suspBuf = desc_buf[dirRec.sysUseStar:dirRec.lenDr]
            if self.rripOffset != -1:
                rripNode = self.__rripLoop__(suspBuf, dirRec.lenDr-dirRec.sysUseStar)
                dirRec.rrip = rripNode
                if rripNode != None:
                    if rripNode.altname != "":
                        dirRec.fIdentifier = rripNode.altname
                        dirRec.lenFi = len(rripNode.altname)
                        #print "rrip_altname: %s"%(dirRec.fIdentifier)
                # if rripNode end #
            # if self.rripOffset != -1 end #
        # if dirRec.lenDr > .. end #
        return dirRec

    def readDirItems(self, block_nr=None, total=None):
        """ Read file dirctory records
         Read dirctory records from 'block_nr' with a length of 'total'.
         Return a list containing directory records(DirRecord). 
        """
        dirs = []
        total_blk = (total+BLOCK_SIZE-1)/BLOCK_SIZE
        i_blk = 0
        while i_blk < total_blk:
            self.isoFile.seek((block_nr+i_blk)*BLOCK_SIZE)
            desc_buf = self.isoFile.read(BLOCK_SIZE)
            i_blk = i_blk + 1
            while True:
                dirItem = self.readDirrecord(desc_buf)
                if dirItem == None:
                    break;

                dirs.append(dirItem)
                if desc_buf.__len__() > dirItem.lenDr:
                    desc_buf = desc_buf[dirItem.lenDr:]            
                else:
                   break;
        return dirs;
    
    def readPathtableL(self):
        """ Read path table of L typde """
        block_nr = self.priVol.ptLRd
        total = self.priVol.ptSize

        path_table = []
        self.isoFile.seek(block_nr*BLOCK_SIZE)
        ptbuf = self.isoFile.read(BLOCK_SIZE * ((total+BLOCK_SIZE-1)/BLOCK_SIZE))
        i = 0
        r_size = 0;
        while True :
            i = i+1
            t = PathTabelItem()
            
            t.lenDi = struct.unpack('B', ptbuf[0])[0]
            t.lenEattr = struct.unpack('B', ptbuf[1])[0]
            t.locExtent = struct.unpack('<L', ptbuf[2:6])[0]
            t.pdirNr = struct.unpack('<H', ptbuf[6:8])[0]
            t.fIdentifier = ptbuf[8:8+t.lenDi]
            path_table.append(t);
            if t.lenDi % 2 :
                len_pd = 1
            else:
                len_pd = 0
    
            r_size += 9+t.lenDi-1+len_pd;
            if r_size >= total:         
                break;
            ptbuf = ptbuf[9+t.lenDi-1+len_pd:]
        # while True
        return path_table

    # @path -- path within iso file system.
    # @output -- what local path you want write to.
    # @pattern -- regular expression.
    # @r -- recursion flag, write the whole sub-directories or not.
    # @all_type -- which file type should be writed.
    #              False: Write regular type files only.
    #              True: Wirte all types files (regular, device file, link, socket, etc)
    def writeDir(self, path, output, pattern="", r=True, all_type=False):
        """ Extract a directory
        Return 0 means success otherwise failure.
        """
        d = self.searchDir(path)
        if d != None:
            if output.endswith("/"):
                output = output[0:-1]
            # Try to make target directory.
            if not os.path.exists(output):
                try:
                    os.makedirs(output)
                except(OSError):
                    sys.stderr.write("can't make dirs({0})\n".format(p))
                    return E_FAILURE
            pp = None
            if pattern != "":
                p = r'{0}'.format(pattern)
                pp = re.compile(p)

            if d.fFlag & 0x02 == 0x02:
                # Check if a clean directory.
                try:
                    if len(os.listdir(output)) > 0:
                        sys.stderr.write("The target directory is not empty\n")
                        return E_FAILURE
                except(OSError):
                    sys.stderr.write("can't access dirs({0})\n".format(p))
                    return E_FAILURE

                self.writeDir_r(output, d, pp, r, all_type)
                return E_SUCCESS
            else:
                return self.writeFile(d, output+path, all_type)
        else:
            return E_FAILURE
    
    def writeDir_r(self, det_dir, dire, pp, r, all_type):
        #print "write dir:(%s)"%(det_dir)
        dirs = self.readDirItems(dire.locExtent, dire.lenData)
        for d in dirs:
            if not d.fIdentifier in [".", ".."]:
                if (pp != None) and (pp.search(d.fIdentifier) == None):
                    match = False
                else:
                    match = True
                #print "mathing %s, %s"%(match, d.fIdentifier)
                p = det_dir + "/" + d.fIdentifier
                if d.fFlag & 0x02 == 0x02:
                    if not os.path.exists(p):
                        os.makedirs(p, 0777)                            
                    if r:
                        if match:
                            self.writeDir_r(p, d, None, r, all_type) # Don't need to match subdirectory.                        
                        else:
                            self.writeDir_r(p, d, pp, r, all_type)
                elif match:
                    self.writeFile(d, p, all_type)
                var.extract_file_name = ""
            # if not d.fIdentifier end #
        # for d in dirs end #
    
    def writeFile(self, dirRec, detFile, all_type):
        """ Write a file to detFile 
        Return 0 means success otherwise failure.
        """
        if detFile == "" or dirRec == None:
            sys.stderr.write("can't write file\n")
            return E_FAILURE
    
        #print "write file (%s)"%(detFile)
        var.extract_file_name = "Extracting  " + detFile[(var.install_dir_count):]
        dirname = os.path.dirname(detFile)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname, 0777)
            except(OSError):
                sys.stderr.write("can't makedirs\n")
                return E_FAILURE

        if all_type == True:
            # device file
            if dirRec.rrip != None and (dirRec.rrip.devH != 0 or dirRec.rrip.devL != 0):
            	#fFlag == 0
                high = dirRec.rrip.devH
                low = dirRec.rrip.devL
                if high == 0:
                    device = os.makedev(os.major(low), os.minor(low))
                else:
                    device = os.makedev(high, os.minor(low))
                try:
                    mode = dirRec.rrip.fMode & 0o770000
                    if mode == S_IFCHR:
                        os.mknod(detFile, 0777|stat.S_IFCHR, device)
                    elif mode  == S_IFBLK:
                        os.mknod(detFile, 0777|stat.S_IFBLK, device)
                except(OSError):
                    sys.stderr.write("can't mknode, maybe no permission\n")
                    return E_DEVICEFILE

                return E_SUCCESS

        loc = dirRec.locExtent
        length = dirRec.lenData
        self.isoFile.seek(BLOCK_SIZE * loc)
        #print "file length(%d)"%(length)
        r_size = BLOCK_SIZE
    
        try:
            f_output = open(detFile, 'wb')
        except(IOError):
            sys.stderr.write("can't open{0} for write\n".format(detFile))            
            return E_FAILURE
    
        while True:
            if length == 0:
                break 
            elif length <= BLOCK_SIZE:
                r_size = length
                length = 0
            else:
                length = length - BLOCK_SIZE
    
            buf = self.isoFile.read(r_size)
            f_output.write(buf)
        # while True end.
        f_output.close()
        return E_SUCCESS
    
    def readDir(self, dir_path, r=True):
        file_list = []
        d = self.searchDir(dir_path)
        if d != None:
            if (d.fFlag & 0x02) == 0x02:
                #print "readDir (%x, %x)"%(d.locExtent, d.lenData)
                if dir_path.endswith("/"):
                    dir_path = dir_path[0:-1]
                self.readDir_r(file_list, dir_path, d, r)
            # if (d.fFlag & 0x02) == 0x02: #
        # if d != None:
        return file_list

    def readDir_r(self, file_list, dir_path, dire, r):
        if (dire.fFlag & 0x02) != 0x02:
            return
        dirs = self.readDirItems(dire.locExtent, dire.lenData)
        for d in dirs:
            if not d.fIdentifier in [".", ".."]:
                p = dir_path + "/" + d.fIdentifier
                file_list.append(p)
                if r:
                    self.readDir_r(file_list, p, d, r)
            # if not d.fIdentifier #
        # for d in dirs: #

def dump_dir_record(dirs):
    """ Dump all the file dirctory records contained in desc_buf """

    print "Dump file/deirectory record"
    print "===========================\n" 
    if dirs != None:
        for f in dirs:
            print "length of directory record:(0x%x), length of extend attribute:(%d), \
location of record:(%d)BLOCK->(0x%x), data length(%d) size of file unit:(%d), \
interleave gap size:(%d), file flag:(0x%x),name length:(%d) identify:(%s)\n" \
%(f.lenDr, f.lenEattr, f.locExtent, f.locExtent*BLOCK_SIZE,f.lenData, \
f.fUnitSize, f.gapSize, f.fFlag, f.lenFi, f.fIdentifier)
    
def dump_pathtable_L(path_table):
    """ Dump path table of L typde """
    
    print "Dump path table"
    print "================\n"
    #path_table = readPathtableL()
    i = 0;
    for t in path_table:
        i = i + 1
        if t.lenDi == 1:
            if t.fIdentifier in [0, 1]:
                print "is a root directory(%d)" %(is_root)
        print "%d->length of identify:(%d), length of extend attribute:(%d), \
local:(%d)->(0x%x), parent dir number:(%d), identify:(%s)\n" \
%(i, t.lenDi, t.lenEattr, t.locExtent, t.locExtent*BLOCK_SIZE, t.pdirNr, t.fIdentifier)

def dump_primary_volume(privol=None):
    """ Dump primary volume descriptor """

    if privol == None:
        print "Can't dump, read primary volume first"
        return
    print "===== Dump primary volume descriptor =="

    print "System Identifier:(%s)" %(privol.sysIdentifier)
    print "Volume Identifier:(%s)" %privol.volIdentifier
    print "Volume Space size:(0x%x)BLOCKS(2kB)" %privol.volSize
    print "Volume sequence number:(%d)" %(privol.volSeq)
    print "logic block size:(0x%x)" %(privol.blockSize)
    print "Volume path talbe L's BLOCK number is :(0x%x-->0x%x)" %(privol.ptLRd, privol.ptLRd*BLOCK_SIZE)
#    print "Abstract File Identifier: (%s)" %(volume_dsc[739:776])
#    print "Bibliographic File Identifier: (%s)" %(volume_dsc[776:813])
    print "pathtable locate (%d)" %(privol.ptLRd)
    print "File Structure Version:(%d)" %(privol.fsVer)
    print "Root directory is at (%d)block, have(0x%x)bytes" %(privol.rootLoc, privol.rootTotal)
#    dump_dir_record(None, 23, 1)

def dump_boot_record(volume_dsc):
    """ Dump boot record  """

    print "===== Dump boot record =="
    std_identifier = volume_dsc[1:6]
    print "Standard Identifier:(%s)" %std_identifier

    vol_ver = struct.unpack('B', volume_dsc[6])
    print "Volume descriptor version:(%d)" %vol_ver

    bootsys_identifier = volume_dsc[7:39]
    print "boot system identifier(%s)" %bootsys_identifier

    boot_identifier = volume_dsc[39:71]
    print "boot  identifier(%s)" %boot_identifier

def usage():
    """ Prompt user how to use   """
    print """
Usage: isodump  dump-what [options]  iso-file
       [dump-what]
       -----------
       boot               - Dump boot record.
       primary-volume     - Dump primary volume.
       pathtable          - Dump path table.
       dir-record [block number] [length] - Dump a raw data of a Directory Record

       iso:/dir [-r]  [-o output] [-p pattern]  - Dump a dirctory or file to [output]
           -r    recursively visit directory.
           -p    spcify a Regular expression pattern for re.search(pattern,).

isodump xx.iso              - Dump the root directory
isodump pathtable xx.iso    - Dump the path table record.

isodump iso:/ -r     xx.iso
    -- Dump the root directory of xx.iso recursively.

isodump iso:/ -r -o /tmp/iso    xx.iso
    -- Extract the iso to /tmp/iso/.

isodump iso:/boot -o /tmp/iso/boot    xx.iso
    -- Extract the /boot directory of xx.iso to /tmp/iso/boot.

isodump iso:/boot/grup.cfg -o /tmp/grub.cfg  xx.iso
    -- Extract the file "grup.cfg" to "/tmp/grub.cfg"

isodump iso:/boot -r -o /tmp/iso -p "*.cfg"  xx.iso
    -- Extract any files or directories under /boot maching "*.cfg" to /tmp/iso/.
"""
    sys.exit(-1)

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) < 3:
        usage()

    iso9660fs = ISO9660(argv[-1])
    dump_what = argv[1]

    if dump_what == "primary-volume":
        dump_primary_volume(iso9660fs.priVol)
    elif dump_what == "pathtable":
        path_table = iso9660fs.readPathtableL()
        dump_pathtable_L(path_table)
    if dump_what == "dir-record":
        if len(argv) == 5:
            print "dump dir-record (%s, %s)"%(argv[2], argv[3])
            dirs = iso9660fs.readDirItems(int(argv[2]), int(argv[3]))
            dump_dir_record(dirs)
        else:
            usage()
    elif dump_what.startswith("iso:"): 
        o_path = ""
        r = False
        o = False
        p = False
        pattern = ""
        for arg in argv[2:-1]:
            if arg == "-r":
                r = True
                o = False
                p = False
            elif arg == "-o":
                o = True
                p = False
            elif arg == "-p":
                o = False
                p = True
            elif o == True:
                o_path = arg
                o = False
            elif p == True:
                pattern = arg
                p = False

        isodir = dump_what[4:]
        if o_path == "":
            print "dump_dir(%s)"%(isodir)
            filelist = iso9660fs.readDir(isodir, r)
            if filelist == []:
                print "can't read any file from (%s)"%(isodir)
            else:
                for f in filelist:
                    print f
        else:
            print "writeDir(%s)->(%s) with pattern(%s)"%(isodir, o_path, pattern)
            sys.exit(iso9660fs.writeDir(isodir, o_path, pattern, r, True))

