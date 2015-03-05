#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     usb.py
# Purpose:  Module to detect USB devices under Linux and Windows
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import collections
import sys
import os
import platform
import ctypes


if platform.system() == "Linux":
    sys.path.append('pyudev')
    import pyudev
    import dbus

elif platform.system() == "Windows":
    import win32com.client


class USB():
    """
    List and get USB details.
    """

    '''
    def __init__(self, usb_disk=None):
        """
        Parameters
        -----------
        usb_disk : string
        It is the USB disk as detected by the host system
        Under Linux it should look like "/dev/sdb1"
        On Windows it should look like "C:\\"
        """
        #if usb_disk is not None:
        self.usb_disk = usb_disk
        '''

    def disk_usage(self, mount_path):
        """
        Function to detect various size os an USB disk.
        :param mount_path: Path to USB mount point.
        :return: total used and free size of an USB.
        """
        _ntuple_diskusage = collections.namedtuple('usage', 'total used free')

        if platform.system() == "Linux":
            st = os.statvfs(mount_path)
            free = st.f_bavail * st.f_frsize
            total = st.f_blocks * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize

            return _ntuple_diskusage(total, used, free)

        elif platform.system() == "Windows":

            _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
                               ctypes.c_ulonglong()
            if sys.version_info >= (3,) or isinstance(mount_path, unicode):
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
            else:
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
            ret = fun(mount_path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
            if ret == 0:
                raise ctypes.WinError()
            used = total.value - free.value

            return _ntuple_diskusage(total.value, used, free.value)
        else:
            raise NotImplementedError("Platform not supported.")

    def bytes2human(self, n):
        """
        Function to convert integer values to human readable format.
        :param n: Integer Value.
        :return: Integer value converted to human readable form
        """
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i+1)*10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n

    def list_usb(self):
        """
        List inserted USB devices.
        :return: USB device as list.
        """
        devices = []
        try:
            print "Using PyUdev for detecting USB drives..."
            context = pyudev.Context()
            for device in context.list_devices(subsystem='block', DEVTYPE='partition', ID_FS_USAGE="filesystem",
                                               ID_TYPE="disk", ID_BUS="usb"):
                if device['ID_BUS'] == "usb" and device['DEVTYPE'] == "partition":
                    devices.append(str(device['DEVNAME']))
        except:
            bus = dbus.SystemBus()
            try:
                print "Falling back to Udisks2.."
                ud_manager_obj = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
                ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')
                for k, v in ud_manager.GetManagedObjects().iteritems():
                    drive_info = v.get('org.freedesktop.UDisks2.Block', {})
                    if drive_info.get('IdUsage') == "filesystem" and not drive_info.get('HintSystem') and not drive_info.get('ReadOnly'):
                        device = drive_info.get('Device')
                        device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                        devices.append(device)
            except:
                try:
                    print "Falling back to Udisks1..."
                    ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
                    ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks')
                    for dev in ud_manager.EnumerateDevices():
                            device_obj = bus.get_object("org.freedesktop.UDisks", dev)
                            device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
                            if device_props.Get('org.freedesktop.UDisks.Device',
                                                "DriveConnectionInterface") == "usb" and device_props.Get(
                                    'org.freedesktop.UDisks.Device', "DeviceIsPartition"):
                                if device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsMounted"):
                                    device_file = device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile")
                                    devices.append(device_file)
                except:
                    print "No USB device found..."

        if devices:
            #print devices
            return devices
        else:
            return None

    def get_usb(self, usb_disk):
        """
        Populate and get details of an USB disk.
        :param usb_disk: USB disk. Example.. "/dev/sdb1" on Linux and "D:\" on Windows.
        :return:    label       == > returns name/label of an inserted USB device.
                    mount       == > returns mount path of an inserted USB device.
                    uuid        == > returns uuid of an inserted USB device.
                    filesystem  == > returns type of filesystem of an inserted USB device.
                    device      == > returns device path of an inserted USB device.
                    total_size  == > returns total size in MB/GB of an inserted USB device.
                    free_size   == > returns free size in MB/GB of an inserted USB device.
                    used_size   == > returns used size in MB/GB of an inserted USB device.
        """
        import collections
        _ntuple_diskusage = collections.namedtuple('usage', 'label mount uuid filesystem device total_size free_size \
                                                            used_size')
        if not usb_disk:
            print "You can not pass empty argument."
        else:
            if platform.system() == "Linux":
                try:
                    """
                    Try with PyUdev to get the details of USB disks.
                    This is the easiest and reliable method to find USB details.
                    Also, it is a standalone package and no dependencies are required.
                    """
                    #print "Using PyUdev for detecting USB details..."
                    context = pyudev.Context()
                    for device in context.list_devices(subsystem='block', DEVTYPE='partition', ID_FS_USAGE="filesystem",
                                                       ID_TYPE="disk", ID_BUS="usb"):
                        if device['ID_BUS'] == "usb" and device['DEVTYPE'] == "partition":
                            if (device['DEVNAME']) == usb_disk:
                                uuid = str(device['ID_FS_UUID'])
                                file_system = str(device['ID_FS_TYPE'])

                                mount_point = str(os.popen('mount | grep %s | cut -d" " -f3' % usb_disk).read().strip())
                                try:
                                    label = str(device['ID_FS_LABEL'])
                                except:
                                    label = "No label."
                except:
                    try:
                        """
                        Now lets try with UDisks2. The latest but painful software.
                        """
                        #print "Falling back to UDisks2 for detecting USB details..."
                        bus = dbus.SystemBus()
                        bd = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2/block_devices%s'%usb_disk[4:])
                        device = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
                        device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                        uuid = bd.Get('org.freedesktop.UDisks2.Block', 'IdUUID', dbus_interface='org.freedesktop.DBus.Properties')
                        file_system = bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
                        mount_point = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
                        mount_point = str(bytearray(mount_point[0]).decode('utf-8').replace(b'\x00', b''))
                        try:
                            label = str(bd.Get('org.freedesktop.UDisks2.Block', 'IdLabel', dbus_interface='org.freedesktop.DBus.Properties'))
                            if not label:
                                print 'Name of the USB partition is %s'%label
                            else:
                                label = "No label."
                        except:
                            label = "No label."
                    except:
                        try:
                            """
                            Finally we will try with UDisks(1).
                            """
                            print "Falling back to UDisks as a last choice for getting USB details..."
                            bus = dbus.SystemBus()
                            device_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks/devices" + str(usb_disk[4:]))
                            device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
                            device = device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile")
                            mount_point = device_props.Get('org.freedesktop.UDisks.Device', "DeviceMountPaths")[0]
                            uuid = device_props.Get('org.freedesktop.UDisks.Device', "IdUuid")
                            file_system =  device_props.Get('org.freedesktop.UDisks.Device', "IdType")
                            try:
                                label = device_props.Get('org.freedesktop.UDisks.Device', "IdLabel")
                            except:
                                label = "No label."
                        except:
                            print "Error detecting USB details."
            else:
                try:
                    selected_usb_part = str(usb_disk)
                    oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
                    d = oFS.GetDrive(oFS.GetDriveName(oFS.GetAbsolutePathName(selected_usb_part)))
                    selected_usb_device = d.DriveLetter
                    serno = "%X" % (long(d.SerialNumber) & 0xFFFFFFFF)
                    uuid = serno[:4] + '-' + serno[4:]
                    label = d.VolumeName
                    if label:
                        print 'Name of the USB partition is %s'%label
                    else:
                        label = "No label."
                    mount_point = selected_usb_device + ":\\"
                    file_system = d.FileSystem
                except:
                    print "Error detecting USB details."

            if mount_point:
                total_size = self.bytes2human(self.disk_usage(mount_point).total)
                free_size = self.bytes2human(self.disk_usage(mount_point).free)
                used_size = self.bytes2human(self.disk_usage(mount_point).used)
                device = str(usb_disk)
            else:
                mount_point = "Not mounted."
                total_size = "Not mounted."
                free_size = "Not mounted."
                used_size = "Not mounted."
            return _ntuple_diskusage(label, mount_point, uuid, file_system, device, total_size, free_size, used_size)