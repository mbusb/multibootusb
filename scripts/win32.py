import collections
import ctypes
import io
import pywintypes
import struct
import sys
import time
import win32api
import win32con
import win32file
import winerror
import winioctlcon
import wmi

from ctypes import wintypes
from functools import reduce

kernel32 = ctypes.WinDLL('kernel32') # , use_last_error=True)

kernel32.FindFirstVolumeW.restype = wintypes.HANDLE
kernel32.FindNextVolumeW.argtypes = (wintypes.HANDLE,
                                     wintypes.LPWSTR,
                                     wintypes.DWORD)
kernel32.FindVolumeClose.argtypes = (wintypes.HANDLE,)

def FindFirstVolume():
    volume_name = ctypes.create_unicode_buffer(" " * 255)
    h = kernel32.FindFirstVolumeW(volume_name, 255)
    if h == win32file.INVALID_HANDLE_VALUE:
        raise RuntimeError("FindFirstVolume() returned an invalid handle.")
    return h, volume_name.value

def FindNextVolume(hSearch):
    volume_name = ctypes.create_unicode_buffer(" " * 255)
    if kernel32.FindNextVolumeW(hSearch, volume_name, 255) != 0:
        return volume_name.value
    else:
        errno = ctypes.GetLastError()
        if errno == winerror.ERROR_NO_MORE_FILES:
            FindVolumeClose(hSearch)
            return None
        raise RuntimeError("FindNextVolume failed (%s)" % errno)

def FindVolumeClose(hSearch):
    """Close a search handle opened by FindFirstVolume, typically
    after the last volume has been returned.
    """
    if kernel32.FindVolumeClose(hSearch) == 0:
        raise RuntimeError("FindVolumeClose() failed.")

def findAvailableDrives():
    return [(d, win32file.GetDriveType(d)) for d in
            win32api.GetLogicalDriveStrings().rstrip('\0').split('\0')]

def findNewDriveLetter(used_letters):
    all_letters = set([chr(i) for i in range(ord('C'), ord('Z')+1)])
    return min(list(all_letters - set([s[0] for s in used_letters])))

def _openHandle(path, bWriteAccess, bWriteShare,
                logfunc = lambda s: None):
    TIMEOUT, NUM_RETRIES = 10, 20
    for retry_count in range(6):
        try:
            access_flag = win32con.GENERIC_READ | \
                          (bWriteAccess and win32con.GENERIC_WRITE or 0)
            share_flag = win32con.FILE_SHARE_READ | \
                         (bWriteShare and win32con.FILE_SHARE_WRITE or 0)
            handle = win32file.CreateFile(
                path, access_flag, share_flag, None,
                win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
            nth = { 0: 'first', 1:'second', 2:'third'}
            logfunc("Opening [%s]: success at the %s iteration" %
                    (path, nth.get(retry_count, '%sth' % (retry_count+1))))
            return handle
        except pywintypes.error as e:
            logfunc('Exception=>'+str(e))
            if NUM_RETRIES/3 < retry_count:
                bWriteShare = True
        time.sleep(TIMEOUT / float(NUM_RETRIES))
    else:
        raise RuntimeError("Couldn't open handle for %s." % path)

def _closeHandle(h):
    x = win32file.CloseHandle(h)
    assert x != win32file.INVALID_HANDLE_VALUE
    return x

class openHandle:
    def __init__(self, path, bWriteAccess, bWriteShare,
                 logfunc = lambda s: None):
        self.path = path
        self.bWriteAccess = bWriteAccess
        self.bWriteShare = bWriteShare
        self.logfunc = logfunc
        self.h = None

    def __enter__(self):
        self.h = _openHandle(self.path, self.bWriteAccess, self.bWriteShare,
                             self.logfunc)
        return self

    def __exit__(self, type_, value, traceback_):
        _closeHandle(self.h)

    def assert_physical_drive(self):
        if self.path.lower().find('physicaldrive')<0:
            raise RuntimeError("Handle is not one of a physical drive.")

    def LockPhysicalDrive(self):
        self.assert_physical_drive()
        lockPhysicalDrive(self.h, self.logfunc)
        self.logfunc("Successfully locked '%s'" % self.path)


    def ReadFile(self, size):
        return win32file.ReadFile(self.h, size, None)

    def WriteFile(self, b):
        return win32file.WriteFile(self.h, b, None)

    geometory_tuple = collections.namedtuple(
        'DiskGeometory',
        ['number_of_cylinders', 'media_type', 'tracks_per_cylinder',
         'sectors_per_track', 'bytes_per_sector', 'disk_size'])
    def DiskGeometory(self):
        self.assert_physical_drive()
        o = win32file.DeviceIoControl(
            self.h, winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY_EX,
            None, 256, None)
        return self.geometory_tuple(*struct.unpack('<qiiiiq', o[:32]))

    MAX_SECTORS_TO_CLEAR=128
    def ZapMBRGPT(self, disk_size, sector_size, add1MB):
        self.assert_physical_drive()
        # Implementation borrowed from rufus: https://github.com/pbatard/rufus
        num_sectors_to_clear \
            = (add1MB and 2048 or 0) + self.MAX_SECTORS_TO_CLEAR
        zeroBuf = b'\0' * sector_size
        for i in range(num_sectors_to_clear):
            self.WriteFile(zeroBuf)
        offset = disk_size - self.MAX_SECTORS_TO_CLEAR * sector_size
        win32file.SetFilePointer(self.h, offset, win32con.FILE_BEGIN)
        for i in range(num_sectors_to_clear):
            self.WriteFile(zeroBuf)
        # We need to append paddings as CREATE_DISK structure contains a union.
        param = struct.pack('<IIIHH8s',
                            winioctlcon.PARTITION_STYLE_MBR, 0xdeadbeef,
                            0,0,0,b'abcdefgh')
        win32file.DeviceIoControl(
            self.h, winioctlcon.IOCTL_DISK_CREATE_DISK, param, 0, None)

    def CopyFrom(self, src_file, progress_cb):
        with openHandle(src_file, True, False,
                        lambda s:sys.stdout.write(s+'\n')) as src:
            total_bytes = 0
            hr, b = src.ReadFile(1024*1024)
            # win32file.ReadFile() seems to have a bug in the interpretation
            # of 'hr'. https://sourceforge.net/p/pywin32/bugs/689/
            # The following loop condition is a workaround, which may not
            # work properly.
            while hr == 0 and len(b):
                win32file.WriteFile(self.h, b, None)
                total_bytes += len(b)
                progress_cb(total_bytes)
                hr, b = src.ReadFile(1024*1024)


def lockPhysicalDrive(handle, logfunc=lambda s: None):
    try:
        win32file.DeviceIoControl(
            handle, winioctlcon.FSCTL_ALLOW_EXTENDED_DASD_IO,
            None, 0, None)
    except pywintypes.error as e:
        logfunc('IO boundary checks diabled.')
    for retry in range(20):
        try:
            win32file.DeviceIoControl(handle, winioctlcon.FSCTL_LOCK_VOLUME,
                                      None, 0, None)
            return
        except pywintypes.error as e:
            logfunc( str(e) )
            time.sleep(1)
    raise RuntimeError("Couldn't lock the Volume.")


def findVolumeGuids():
    DiskExtent = collections.namedtuple(
        'DiskExtent', ['DiskNumber', 'StartingOffset', 'ExtentLength'])
    Volume = collections.namedtuple(
        'Volume', ['Guid', 'MediaType', 'DosDevice', 'Extents'])
    found = []
    h, guid = FindFirstVolume()
    while h and guid:
        #print (guid)
        #print (guid, win32file.GetDriveType(guid),
        #       win32file.QueryDosDevice(guid[4:-1]))
        hVolume = win32file.CreateFile(
            guid[:-1], win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL,  None)
        extents = []
        driveType = win32file.GetDriveType(guid)
        if driveType in [win32con.DRIVE_REMOVABLE, win32con.DRIVE_FIXED]:
            x = win32file.DeviceIoControl(
                hVolume, winioctlcon.IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS,
                None, 512, None)
            instream = io.BytesIO(x)
            numRecords = struct.unpack('<q', instream.read(8))[0]
            fmt = '<qqq'
            sz = struct.calcsize(fmt)
            while 1:
                b = instream.read(sz)
                if len(b) < sz:
                    break
                rec = struct.unpack(fmt, b)
                extents.append( DiskExtent(*rec) )
        vinfo = Volume(guid, driveType, win32file.QueryDosDevice(guid[4:-1]),
                       extents)
        found.append(vinfo)
        guid = FindNextVolume(h)
    return found    

def ZapPhysicalDrive(target_drive, get_volume_info_func, log_func):
    with openHandle('\\\\.\\PhysicalDrive%d' % target_drive, True, False,
                    lambda s:sys.stdout.write(s+'\n')) as hDrive:
        hDrive.LockPhysicalDrive()
        geom = hDrive.DiskGeometory()
        for v in get_volume_info_func(target_drive):
            volume_path = '\\\\.\\'+v.DeviceID
            log_func('Dismounting volume ' + volume_path)
            with openHandle(volume_path, False, False) as h:
                x = win32file.DeviceIoControl(
                    h.h, winioctlcon.FSCTL_DISMOUNT_VOLUME, None, None)
                print ('FSCTL_DISMOUNT_VOLUME=>%s' % x)
            x = win32file.DeleteVolumeMountPoint(volume_path+'\\')
            log_func('DeleteVolumeMountPoint=>%s' % x)
        else:
            log_func('No volumes on %s' % target_drive)

        add1MB = False
        hDrive.ZapMBRGPT(geom.disk_size, geom.bytes_per_sector, add1MB)


if __name__ == '__main__':

    # used_letters = [d for d in
    #       win32api.GetLogicalDriveStrings().rstrip('\0').split('\0')]
    # print (used_letters)
    # print (findNewDriveLetter(used_letters))
    # TargetDrive = 2
    # vinfo_list = [x for x in findVolumeGuids()
    #               if x.Extents and x.Extents[0].DiskNumber==TargetDrive]

    TargetDrive = 5
    with openHandle('\\\\.\\PhysicalDrive%d' % TargetDrive, True, False,
                    lambda s:sys.stdout.write(s+'\n')) as hDrive:
        hDrive.CopyFrom('c:/Users/shinj/Downloads/salitaz-rolling_iso',
                        lambda b: None)
