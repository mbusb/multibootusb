#! /usr/bin/python

"""  Dump raw meta data of iso9660 file system. """
##
## Extract directory or file from iso.
## Support RRIP.
## 

# Author : LiQiong Lee

import sys
import struct
import os
import re
import var
from ctypes import *

BLOCK_SIZE = 2048

g_fISO = None
g_priVol = None
g_rripOffset = -1
g_rootDir = None

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

       iso://dir [-r]  [-o output] [-p pattern]  - Dump a dirctory or file to [output]
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

class PrimaryVolume(Structure):
    _fields = [("sys_identifier", c_char_p),
               ("vol_identifier", c_char_p),
               ("vol_size",       c_uint),
               ("vol_seq",        c_short),
               ("block_size",     c_short),
               ("pt_size",        c_uint),
               ("pt_L_rd",        c_uint),
               ("fs_ver",         c_ubyte),
               ("root_loc",       c_uint),
               ("root_total",     c_uint)]

class DirRecord(Structure):
    _fields = [("len_dr",       c_ubyte),
               ("len_eattr",    c_ubyte),
               ("loc_extent",   c_uint),
               ("len_data",     c_uint),
               ("dt_year",      c_ubyte),
               ("dt_month",     c_ubyte),
               ("dt_hour",      c_ubyte),
               ("dt_minute",    c_ubyte),
               ("dt_second",    c_ubyte),
               ("dt_offset",    c_ubyte),
               ("f_flag",       c_ubyte),
               ("f_unit_size",  c_ubyte),
               ("gap_size",     c_ubyte),
               ("vol_seq_nr",   c_ushort),
               ("len_fi",       c_ubyte),
               ("f_identifier", c_char_p),
               ("sys_use_star", c_uint),
               ("susp_buf",     c_char_p)]

               
class PathTabelItem(Structure):
    _fields = [("len_di",       c_ubyte),
               ("len_eattr",    c_ubyte),
               ("loc_extent",   c_uint),
               ("pdir_nr",      c_ushort),
               ("f_identifier", c_char_p)]

class RripInode(Structure):
    _fields = [("offset", c_uint),
               ("altname", c_char_p)]

# ============================================================== #

#  RRIP extension
def rrip_loop(desc_buf, len_buf):

    if g_rripOffset > 0:
        entry_buf = desc_buf[g_rripOffset:]
        print "rrip_loop offset:%d"%(g_rripOffset)
    else:
        entry_buf = desc_buf

    rrInode = RripInode()
    rrInode.offset = -1
    rrInode.altname = ""
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
            #print "Got a entry in rrip_loop (%c,%c) of SUSP with length:(%d),version:(%d)-->"%(sig1,sig2,len_entry, ver),

            if sig1 == ord('S') and sig2 == ord('P'):
                ck1 = struct.unpack("B", entry_buf[4])[0]
                ck2 = struct.unpack("B", entry_buf[5])[0]
                skip = struct.unpack("B", entry_buf[6])[0]
                #print "-->(0x%x==0xBE,0x%x==EF,%d)" %(ck1, ck2, skip)
                if ck1 == 0xBE and ck2 == 0xEF:
                    rrInode.offset = skip
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
                    rrInode.altname += "."
                elif flag == 0x04:   # FLAG_PARENT
                    rrInode.altname += ".."
                elif flag == 0x01 or flag ==0:  # 1:FLAG_CONTINUE
                    rrInode.altname += entry_buf[5:len_entry]                
                continue
            
            if sig1 == ord('E') and sig2 == ord('R'):
                len_id = struct.unpack("B", entry_buf[4])[0]
                len_des = struct.unpack("B", entry_buf[5])[0]
                len_src = struct.unpack("B", entry_buf[6])[0]
                ext_ver = struct.unpack("B", entry_buf[7])[0]
                continue

            if sig1 == ord('P') and sig2 == ord('X'):
                f_mode = struct.unpack("<L", entry_buf[4:8])[0]
                s_link = struct.unpack("<L", entry_buf[12:16])[0]
                uid = struct.unpack("<L", entry_buf[20:24])[0]
                gid = struct.unpack("<L", entry_buf[28:32])[0]
                continue

            if sig1 == ord('S') and sig2 == ord('T'):
                return rrInode

            #print "\n"
        # while (len_buf - head < 4) #

        if ce_len > 0:
            #print " Read CE block, (%d, %d, %d)"%(ce_blk, ce_len, ce_off)
            g_fISO.seek(ce_blk*BLOCK_SIZE + ce_off)
            entry_buf = g_fISO.read(ce_len)
            len_buf = ce_len
        else:
            break

    return rrInode

# ============================================================== #

def search_dir(path):
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
        return g_rootDir

    pdir_loc = g_priVol.root_loc
    pdir_len = g_priVol.root_total
    i_dircomp = 1

    while True:
        found = False
        dirs = read_dirs(pdir_loc, pdir_len)
        for item in dirs:
            if item.f_identifier == dircomps[i_dircomp]:
                pdir_loc = item.loc_extent
                pdir_len = item.len_data
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

# ============================================================== #

# Return a directory record reading from File and 
# Directory Descriptors.
def read_dirrecord(desc_buf):
    """ Dump file  dirctory record """
    global g_rripOffset

    dirRec = DirRecord()
    dirRec.len_dr = struct.unpack("B", desc_buf[0])[0]
    if dirRec.len_dr == 0:
        return None;

    dirRec.len_eattr = struct.unpack("B", desc_buf[1])[0]
    dirRec.loc_extent = struct.unpack("<L", desc_buf[2:6])[0]
    dirRec.len_data = struct.unpack("<L", desc_buf[10:14])[0]
    dirRec.f_flag = struct.unpack("B", desc_buf[25])[0]
    dirRec.f_unit_size = struct.unpack("B", desc_buf[26])[0]
    dirRec.gap_size = struct.unpack("B", desc_buf[27])[0]
    dirRec.vol_seq_nr = struct.unpack("<H", desc_buf[28:30])[0]
    dirRec.len_fi = struct.unpack("B", desc_buf[32])[0]
    dirRec.f_identifier = ""
    if dirRec.len_fi == 1:
        dirRec.f_identifier  = struct.unpack("B", desc_buf[33])[0]
        if dirRec.f_identifier  == 0:
            dirRec.f_identifier = "."
        elif dirRec.f_identifier == 1:
            dirRec.f_identifier = ".."
    else:
        dirRec.f_identifier = desc_buf[33:33+dirRec.len_fi]
        idx = dirRec.f_identifier.rfind(";")
        if idx != -1:
            dirRec.f_identifier = dirRec.f_identifier[0:idx]

    dirRec.susp_buf = ""
    dirRec.sys_use_star = 34 + dirRec.len_fi -1
    if dirRec.len_fi % 2 == 0:
        dirRec.sys_use_star += 1
    
    if dirRec.len_dr > dirRec.sys_use_star+4:
        if dirRec.loc_extent == g_priVol.root_loc:
            dirRec.susp_buf = desc_buf[dirRec.sys_use_star:dirRec.len_dr]
        susp_buf = desc_buf[dirRec.sys_use_star:dirRec.len_dr]
        if g_rripOffset != -1:
            rripNode = rrip_loop(susp_buf, dirRec.len_dr-dirRec.sys_use_star)
            if rripNode != None:
                if rripNode.altname != "":
                    dirRec.f_identifier = rripNode.altname
                    dirRec.len_fi = len(rripNode.altname)
                    #print "rrip_altname: %s"%(dirRec.f_identifier)
        
    return dirRec

# Read dirctory records from 'block_nr' with a length of 'total'
# Return a list containing directory records(DirRecord). 
def read_dirs(block_nr=None, total=None):
    """ Read file dirctory records """

    dirs = []
    total_blk = (total+BLOCK_SIZE-1)/BLOCK_SIZE
    i_blk = 0
    while i_blk < total_blk:
        g_fISO.seek((block_nr+i_blk)*BLOCK_SIZE)
        desc_buf = g_fISO.read(BLOCK_SIZE)
        i_blk = i_blk + 1
        while True:
            dirItem = read_dirrecord(desc_buf)
            if dirItem == None:
                break;
        
            dirs.append(dirItem)
            if desc_buf.__len__() > dirItem.len_dr:
                desc_buf = desc_buf[dirItem.len_dr:]            
            else:
               break;
    return dirs;

# Read pathtable record.
def read_pathtable_L(block_nr, total):
    """ Read path table of L typde """

    path_table = []
    g_fISO.seek(block_nr*BLOCK_SIZE)
    ptbuf = g_fISO.read(BLOCK_SIZE * ((total+BLOCK_SIZE-1)/BLOCK_SIZE))
    i = 0
    r_size = 0;
    while True :
        i = i+1
        t = PathTabelItem()
        
        t.len_di = struct.unpack('B', ptbuf[0])[0]
        t.len_eattr = struct.unpack('B', ptbuf[1])[0]
        t.loc_extent = struct.unpack('<L', ptbuf[2:6])[0]
        t.pdir_nr = struct.unpack('<H', ptbuf[6:8])[0]
        t.f_identifier = ptbuf[8:8+t.len_di]

        path_table.append(t);

        if t.len_di % 2 :
            len_pd = 1
        else:
            len_pd = 0

        r_size += 9+t.len_di-1+len_pd;
        if r_size >= total:         
            break;
        ptbuf = ptbuf[9+t.len_di-1+len_pd:]
    return path_table

def read_primary_volume(volume_dsc):
    """ Dump primary volume descriptor """
    global BLOCK_SIZE
    global g_priVol
    global g_rripOffset
    global g_rootDir

    g_priVol = PrimaryVolume()
    g_priVol.sys_identifier = volume_dsc[8:40]
    g_priVol.vol_identifier = volume_dsc[40:72]
    g_priVol.vol_size = struct.unpack('<L',volume_dsc[80:84])[0]
    g_priVol.vol_seq = struct.unpack('<H',volume_dsc[124:126])[0]
    g_priVol.block_size = struct.unpack('<H',volume_dsc[128:130])[0]
    g_priVol.pt_size = struct.unpack('<L',volume_dsc[132:136])[0]
    g_priVol.pt_L_rd = struct.unpack('<L',volume_dsc[140:144])[0]
    g_priVol.fs_ver = struct.unpack('B', volume_dsc[881])[0]
    dirRec = read_dirrecord(volume_dsc[156:190])
    g_priVol.root_loc = dirRec.loc_extent
    g_priVol.root_total = dirRec.len_data
    BLOCK_SIZE = g_priVol.block_size
    
    # Check RRIP
    #print "loc extent(%d)"%(dirRec.loc_extent)
    root_dir = read_dirs(dirRec.loc_extent, g_priVol.root_total)[0]
    rripNode = rrip_loop(root_dir.susp_buf, root_dir.len_dr-root_dir.sys_use_star)
    if rripNode != None:
        g_rripOffset = rripNode.offset
        print "RRIP: rrip_offset %d"%(g_rripOffset)
    else:
        print " This disc don't support RRIP"
    
    g_rootDir = root_dir

def write_dir(path, output, r, pattern):
    d = search_dir(path)
    if d != None:
        pp = None
        if pattern != "":
            p = r'{0}'.format(pattern)
            pp = re.compile(p)
        if d.f_flag & 0x02 == 0x02:
            if output.endswith("/"):
                output = output[0:-1]
            write_dir_r(output, d, r, pp)
        else:
            write_file(d, output)

def write_dir_r(det_dir, dire, r, pp):
    dirs = read_dirs(dire.loc_extent, dire.len_data)
    for d in dirs:
        if not d.f_identifier in [".", ".."]:
            if (pp != None) and (pp.search(d.f_identifier) == None):
                match = False
            else:
                match = True
            #print "mathing %s, %s"%(match, d.f_identifier)
            p = det_dir + "/" + d.f_identifier
            if d.f_flag & 0x02 == 0x02:
                if not os.path.exists(p):
                    os.makedirs(p)
                if r:
                    if match:
                        write_dir_r(p, d, r, None) # Don't need to match subdirectory.
                    else:
                        write_dir_r(p, d, r, pp)
            elif match:
                write_file(d, p)
                var.extract_file_name = ""

def write_file(file_rec, det_file):
    """ Write a file to det_file """

    if det_file == "" or file_rec == None:
        print "can't write file"
        return
    #print "write file (%s)"%(det_file)
    var.extract_file_name = "Extracting  " + det_file[(var.install_dir_count):]
    print var.extract_file_name
    dir_nm = os.path.dirname(det_file)
    if not os.path.exists(dir_nm):
        os.makedirs(dir_nm)
    loc = file_rec.loc_extent
    g_fISO.seek(BLOCK_SIZE * loc)
    length = file_rec.len_data
    #print "file length(%d)"%(length)
    r_size = BLOCK_SIZE

    try:
        f_output = open(det_file, 'wb')
    except(IOError):
        print "can't open(%s) for write"%(det_file)
        return

    while True:
        if length == 0:
            break 
        elif length <= BLOCK_SIZE:
            r_size = length
            length = 0
        else:
            length = length - BLOCK_SIZE

        buf = g_fISO.read(r_size)
        f_output.write(buf)
    # while True end.
    f_output.close()

def dump_dir(path, r):
    d = search_dir(path)
    if d != None:
        if (d.f_flag & 0x02) == 0x02:
            print "dump_dir (%x, %x)"%(d.loc_extent, d.len_data)
            print "==========================================\n"
            if path.endswith("/"):
                path = path[0:-1]
            dump_dir_r(path, d, r)
    	else:
            print("%s is a file")%(path)

def dump_dir_r(dir_path, dire, r):
    if (dire.f_flag & 0x02) != 0x02:
        return
    dirs = read_dirs(dire.loc_extent, dire.len_data)
    for d in dirs:
        if not d.f_identifier in [".", ".."]:
            p = dir_path + "/" + d.f_identifier
            var.iso_file_list.append(p)
            print p

            if r:
                dump_dir_r(p, d, r)

def dump_dirrecord(dirs=None):
    """ Dump all the file dirctory records contained in desc_buf """

    print "Dump file/deirectory record"
    print "===========================\n" 

    for f in dirs:
        print "length of directory record:(0x%x), length of extend attribute:(%d), \
location of record:(%d)BLOCK->(0x%x), data length(%d) size of file unit:(%d), \
interleave gap size:(%d), file flag:(0x%x),name length:(%d) identify:(%s)\n" \
%(f.len_dr, f.len_eattr, f.loc_extent, f.loc_extent*BLOCK_SIZE,f.len_data, \
f.f_unit_size, f.gap_size, f.f_flag, f.len_fi, f.f_identifier)

def dump_pathtable_L(path_table):
    """ Dump path table of L typde """
    
    print "Dump path table"
    print "================\n"
    #path_table = read_pathtable_L()
    i = 0;
    for t in path_table:
        i = i + 1
        if t.len_di == 1:
            if t.f_identifier in [0, 1]:
                print "is a root directory(%d)" %(is_root)
        print "%d->length of identify:(%d), length of extend attribute:(%d), \
local:(%d)->(0x%x), parent dir number:(%d), identify:(%s)\n" \
%(i, t.len_di, t.len_eattr, t.loc_extent, t.loc_extent*BLOCK_SIZE, t.pdir_nr, t.f_identifier)

def dump_primary_volume():
    """ Dump primary volume descriptor """

    global g_priVol

    if g_priVol == None:
        print "Can't dump, read primary volume first"
        return
    print "===== Dump primary volume descriptor =="

    print "System Identifier:(%s)" %(g_priVol.sys_identifier)
    print "Volume Identifier:(%s)" %g_priVol.vol_identifier
    print "Volume Space size:(0x%x)BLOCKS(2kB)" %g_priVol.vol_size
    print "Volume sequence number:(%d)" %(g_priVol.vol_seq)
    print "logic block size:(0x%x)" %(g_priVol.block_size)
    print "Volume path talbe L's BLOCK number is :(0x%x-->0x%x)" %(g_priVol.pt_L_rd, g_priVol.pt_L_rd*BLOCK_SIZE)
#    print "Abstract File Identifier: (%s)" %(volume_dsc[739:776])
#    print "Bibliographic File Identifier: (%s)" %(volume_dsc[776:813])
    print "pathtable locate (%d)" %(g_priVol.pt_L_rd)
    print "File Structure Version:(%d)" %(g_priVol.fs_ver)
    print "Root directory is at (%d)block, have(0x%x)bytes" %(g_priVol.root_loc, g_priVol.root_total)
#    dump_dirrecord(None, 23, 1)

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

def main(argv=sys.argv):
    global g_fISO

    if len(argv) < 3:
        usage()

    dump_what = argv[1]
    try:
        g_fISO = open(argv[-1], 'rb')
    except(IOError):
        g_fISO.close()
        usage()

    # read volume descriptor
    desc_nr = 0;
    while True:
        desc_nr = desc_nr + 1;
        g_fISO.seek(BLOCK_SIZE*(15+desc_nr))
        volume_dsc = g_fISO.read(BLOCK_SIZE)
        flag = struct.unpack('B',volume_dsc[0])[0]
        if flag == 0:
            if dump_what == "boot":
                dump_boot_record(volume_dsc)
            continue

        if flag == 1:
            read_primary_volume(volume_dsc)
            continue

        if flag == 255:
            break;
    # while True End

    if dump_what == "primary-volume":
        dump_primary_volume()
        # dump root
        dirs = read_dirs(g_priVol.root_loc, g_priVol.root_total)
        dump_dirrecord(dirs)
    elif dump_what == "pathtable":
        path_table = read_pathtable_L(g_priVol.pt_L_rd, g_priVol.pt_size)
        dump_pathtable_L(path_table)
    if dump_what == "dir-record":
        if len(argv) == 5:
            print "dump dir-record (%s, %s)"%(argv[2], argv[3])
            dirs = read_dirs(int(argv[2]), int(argv[3]))
            dump_dirrecord(dirs)
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

        iso_path = dump_what[4:]
        if o_path == "":
            print "dump_dir(%s)"%(iso_path)
            dump_dir(iso_path, r)
        else:
            write_dir(iso_path, o_path, r, pattern)
            print "write_dir(%s)->(%s) with pattern(%s)"%(iso_path, o_path, pattern)

    g_fISO.close()
    return 0

# @dir_name: iso:/dir
# @pattern: Regular Expression.
# @iso_name: iso file path.
def extract_directory(dir_name, out_dir, iso_name, pattern=""):
    """ Extract a directory for iso file  """
    argv = ["isodump.py", dir_name, "-r", "-o", out_dir, "-p", pattern, iso_name]
    main(argv)

if __name__ == '__main__':
    sys.exit(main())
