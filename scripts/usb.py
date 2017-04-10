#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     usb.py
# Purpose:  Module to list USB devices and get details under Linux and Windows
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import sys
import platform
import os
import shutil
import collections
import ctypes
import subprocess
from . import gen
if platform.system() == 'Linux':
    from . import udisks
    u = udisks.get_udisks(ver=None)
if platform.system() == 'Windows':
    import psutil
    import win32com.client
    import win32com.client
    import wmi
    import pythoncom


def is_block(usb_disk):
    """
    Function to detect if the USB is block device
    :param usb_disk: USB disk path
    :return: True is devie is block device else False
    """
    import stat
    if platform.system() == 'Linux':
        if len(usb_disk) != 9:
            return False
    elif platform.system() == 'Windows':
        if len(usb_disk) != 2:
            return False
        else:
            return True
    try:
        mode = os.stat(usb_disk).st_mode
        gen.log(mode)
        gen.log(stat.S_ISBLK(mode))
    except:
        return False

    return stat.S_ISBLK(mode)


def disk_usage(mount_path):
    """
    Return disk usage statistics about the given path as a (total, used, free)
    namedtuple.  Values are expressed in bytes.
    """
    # Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
    # License: MIT
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


def list(partition=1, fixed=None):
    """
    List inserted USB devices.
    :return: USB devices as list.
    """
    devices = []
    if platform.system() == "Linux":
        import pyudev
        import dbus

        try:
            # pyudev is good enough to detect USB devices on modern Linux machines.
            gen.log("Using pyudev for detecting USB drives...")
            context = pyudev.Context()
            if fixed is None:
                for device in context.list_devices(subsystem='block', DEVTYPE='partition',
                                                   ID_FS_USAGE="filesystem", ID_TYPE="disk",
                                                   ID_BUS="usb"):
                    # if device['ID_BUS'] == "usb" and device['DEVTYPE'] == "partition":
                    if device.get('ID_BUS') in ("usb", "scsi") and device.get('DEVTYPE') == "partition":
                        # gen.log(device['DEVNAME'])
                        devices.append(str(device['DEVNAME']))
            else:
                for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
                    devices.append(str(device['DEVNAME']))
        except:
            bus = dbus.SystemBus()
            try:
                # You should come here only if your system does'nt have udev installed.
                # We will use udiskd2 for now.
                gen.log("Falling back to Udisks2..")
                ud_manager_obj = bus.get_object(
                    'org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
                ud_manager = dbus.Interface(
                    ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')
                for k, v in ud_manager.GetManagedObjects().iteritems():
                    drive_info = v.get('org.freedesktop.UDisks2.Block', {})
                    if drive_info.get('IdUsage') == "filesystem" and not drive_info.get(
                            'HintSystem') and not drive_info.get('ReadOnly'):
                        device = drive_info.get('Device')
                        device = bytearray(device).replace(
                            b'\x00', b'').decode('utf-8', 'replace')
                        devices.append(device)
            except:
                try:
                    # You must be using really old distro. Otherwise, the code
                    # should not reach here.
                    gen.log("Falling back to Udisks1...")
                    ud_manager_obj = bus.get_object(
                        "org.freedesktop.UDisks", "/org/freedesktop/UDisks")
                    ud_manager = dbus.Interface(
                        ud_manager_obj, 'org.freedesktop.UDisks')
                    for dev in ud_manager.EnumerateDevices():
                        device_obj = bus.get_object(
                            "org.freedesktop.UDisks", dev)
                        device_props = dbus.Interface(
                            device_obj, dbus.PROPERTIES_IFACE)
                        if device_props.Get('org.freedesktop.UDisks.Device',
                                            "DriveConnectionInterface") == "usb" and device_props.Get(
                                'org.freedesktop.UDisks.Device', "DeviceIsPartition"):
                            if device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsMounted"):
                                device_file = device_props.Get(
                                    'org.freedesktop.UDisks.Device', "DeviceFile")
                                devices.append(device_file)
                except:
                    gen.log("No USB device found...")

    elif platform.system() == "Windows":
        if fixed is not None:
            for drive in psutil.disk_partitions():
                if 'cdrom' in drive.opts or drive.fstype == '':
                    # Skip cdrom drives or the disk with no filesystem
                    continue
                devices.append(drive[0][:-1])
        else:
            try:
                # Try new method using psutil. It should also detect USB 3.0 (but not tested by me)
                for drive in psutil.disk_partitions():
                    if 'cdrom' in drive.opts or drive.fstype == '':
                        # Skip cdrom drives or the disk with no filesystem
                        continue
                    if 'removable' in drive.opts:
                        devices.append(drive[0][:-1])
            except:
                # Revert back to old method if psutil fails (which is unlikely)
                oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
                oDrives = oFS.Drives
                for drive in oDrives:
                    if drive.DriveType == 1 and drive.IsReady:
                        devices.append(drive)

    if devices:
        return devices
    else:
        gen.log("No USB device found...")
        return None


def details_udev(usb_disk_part):
    """
    Get details of USB partition using udev
    """
    if platform.system() == "Linux":
        import pyudev
        """
        Try with PyUdev to get the details of USB disks.
        This is the easiest and reliable method to find USB details.
        Also, it is a standalone package and no dependencies are required.
        """
        # gen.log "Using PyUdev for detecting USB details..."
        context = pyudev.Context()
        for device in context.list_devices(subsystem='block', DEVTYPE='partition',
                                           ID_FS_USAGE="filesystem", ID_TYPE="disk",
                                           ID_BUS="usb"):
            fdisk_cmd_out = subprocess.check_output('fdisk -l ' + usb_disk_part, shell=True)
            if b'Extended' in fdisk_cmd_out:
                mount_point = ''
                uuid = 'No_UUID'
                file_system = 'No_FS'
                vendor = 'No_Vendor'
                model = 'No_Model'
                label = 'No_Label'
            elif device.get('ID_BUS') in ("usb", "scsi") and device.get('DEVTYPE') == "partition":
                if (device['DEVNAME']) == usb_disk_part:
                    uuid = str(device['ID_FS_UUID'])
                    file_system = str(device['ID_FS_TYPE'])
                    try:
                        label = str(device['ID_FS_LABEL'])
                    except:
                        label = "No_Label"
                    mount_point = u.mount(usb_disk_part)
                    # mount_point = os.popen('findmnt -nr -o target -S %s' % usb_disk_part).read().strip()
                    # Convert the hex string of space to empty space.
                    mount_point = mount_point.replace('\\x20', ' ')
                    try:
                        vendor = str(device['ID_VENDOR'])
                    except:
                        vendor = str('No_Vendor')
                    try:
                        model = str(device['ID_MODEL'])
                    except:
                        model = str('No_Model')

        if not mount_point == '':
            size_total = shutil.disk_usage(mount_point)[0]
            size_used = shutil.disk_usage(mount_point)[1]
            size_free = shutil.disk_usage(mount_point)[2]

        else:
            size_total = str('No_Mount')
            size_used = str('No_Mount')
            size_free = str('No_Mount')
            mount_point = str('No_Mount')

    return {'uuid': uuid, 'file_system': file_system, 'label': label, 'mount_point': mount_point,
            'size_total': size_total, 'size_used': size_used, 'size_free': size_free,
            'vendor': vendor, 'model': model}


def details_udisks2(usb_disk_part):
    """
    Get details of USB disk detail.
    usb_disk_part: It is the partition of an USB removable disk.
    """
    import dbus
    bus = dbus.SystemBus()
    bd = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2/block_devices%s'%usb_disk_part[4:])
    device = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
    device = bytearray(device).replace(b'\x00', b'').decode('utf-8', 'replace')
    uuid = bd.Get('org.freedesktop.UDisks2.Block', 'IdUUID', dbus_interface='org.freedesktop.DBus.Properties')
    file_system =  bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
    mount_point = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
    if mount_point:
        # mount_point = str(bytearray(mount_point[0]).decode('utf-8').replace(b'\x00', b''))
        mount_point = bytearray(mount_point[0]).replace(b'\x00', b'').decode('utf-8')
    else:
        try:
            mount_point = u.mount(usb_disk_part)
        except:
            mount_point = "No_Mount"
    try:
        label = bd.Get('org.freedesktop.UDisks2.Block', 'IdLabel', dbus_interface='org.freedesktop.DBus.Properties')
    except:
        label = "No_Label"
    usb_drive_id = (bd.Get('org.freedesktop.UDisks2.Block', 'Drive', dbus_interface='org.freedesktop.DBus.Properties'))
    bd1 = bus.get_object('org.freedesktop.UDisks2', usb_drive_id)
    try:
        vendor = bd1.Get('org.freedesktop.UDisks2.Drive', 'Vendor', dbus_interface='org.freedesktop.DBus.Properties')
    except:
        vendor = str('No_Vendor')
    try:
        model = bd1.Get('org.freedesktop.UDisks2.Drive', 'Model', dbus_interface='org.freedesktop.DBus.Properties')
    except:
        model = str('No_Model')
    if not mount_point == "No_Mount":
            size_total = shutil.disk_usage(mount_point)[0]
            size_used = shutil.disk_usage(mount_point)[1]
            size_free = shutil.disk_usage(mount_point)[2]
    else:
        size_total = str('No_Mount')
        size_used = str('No_Mount')
        size_free = str('No_Mount')

    return {'uuid': uuid, 'file_system': file_system, 'label': label, 'mount_point': mount_point,
            'size_total': size_total, 'size_used': size_used, 'size_free': size_free,
            'vendor': vendor, 'model': model}


def bytes2human(n):
    """
    Convert the size to human readable format
    Authored by 'Giampaolo Rodolà' and original link is:-
    http://code.activestate.com/recipes/577972-disk-usage/
    """
    try:
        n = int(n)
    except:
        return 'Unknown'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n


def win_disk_details(disk_drive):
    """
    Populate and get details of an USB disk under windows. Minimum required windows version is Vista.
    :param disk_drive: USB disk like 'G:'
    :return: See the details(usb_disk_part) function for return values.
    """
    pythoncom.CoInitialize()
    vendor = 'Not_Found'
    model = 'Not_Found'
    selected_usb_part = str(disk_drive)
    oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
    d = oFS.GetDrive(oFS.GetDriveName(oFS.GetAbsolutePathName(selected_usb_part)))
    selected_usb_device = d.DriveLetter
    label = (d.VolumeName).strip()
    if not label.strip():
        label = "No_label"
    mount_point = selected_usb_device + ":\\"
    serno = "%X" % (int(d.SerialNumber) & 0xFFFFFFFF)
    uuid = serno[:4] + '-' + serno[4:]
    file_system = (d.FileSystem).strip()
    size_total = shutil.disk_usage(mount_point)[0]
    size_used = shutil.disk_usage(mount_point)[1]
    size_free = shutil.disk_usage(mount_point)[2]
    '''
    # The below code works only from vista and above. I have removed it as many people reported that the software
    # was not working under windows xp. Even then, it is significantly slow if 'All Drives' option is checked.
    # Removing the code doesn't affect the functionality as it is only used to find vendor id and model of the drive.
    c = wmi.WMI()
    for physical_disk in c.Win32_DiskDrive(InterfaceType="USB"):
        for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                if logical_disk.Caption == disk_drive:
                    vendor = (physical_disk.PNPDeviceID.split('&VEN_'))[1].split('&PROD_')[0]
                    model = (physical_disk.PNPDeviceID.split('&PROD_'))[1].split('&REV_')[0]
    '''

    return {'uuid': uuid, 'file_system': file_system, 'label': label, 'mount_point': mount_point,
            'size_total': size_total, 'size_used': size_used, 'size_free': size_free,
            'vendor': vendor, 'model': model}


def details(usb_disk_part):
    """
    Populate and get details of an USB disk.
    :param usb_disk_part: USB disk. Example.. "/dev/sdb1" on Linux and "D:\" on Windows.
    :return:    label       == > returns name/label of an inserted USB device.
                mount_point == > returns mount path of an inserted USB device.
                uuid        == > returns uuid of an inserted USB device.
                file_system == > returns type of filesystem of an inserted USB device.
                device      == > returns device path of an inserted USB device.
                size_total  == > returns total size in MB/GB of an inserted USB device.
                size_free   == > returns free size in MB/GB of an inserted USB device.
                size_used   == > returns used size in MB/GB of an inserted USB device.
                vendor      == > returns the name of the manufacturer.
                model       == > returns the model name of the USB.
    """
    if platform.system() == 'Linux':
        try:
            udev = details_udev(usb_disk_part)
            uuid = udev['uuid']
            file_system = udev['file_system']
            label = udev['label']
            mount_point = udev['mount_point']
            size_total = udev['size_total']
            size_used = udev['size_used']
            size_free = udev['size_free']
            vendor = udev['vendor']
            model = udev['model']
        except:
            udisks2 = details_udisks2(usb_disk_part)
            uuid = udisks2['uuid']
            file_system = udisks2['file_system']
            label = udisks2['label']
            mount_point = udisks2['mount_point']
            size_total = udisks2['size_total']
            size_used = udisks2['size_used']
            size_free = udisks2['size_free']
            vendor = udisks2['vendor']
            model = udisks2['model']
    elif platform.system() == 'Windows':
        win_details = win_disk_details(usb_disk_part)
        uuid = win_details['uuid']
        file_system = win_details['file_system']
        label = win_details['label']
        mount_point = win_details['mount_point']
        size_total = win_details['size_total']
        size_used = win_details['size_used']
        size_free = win_details['size_free']
        vendor = win_details['vendor']
        model = win_details['model']

    return {'uuid': uuid, 'file_system': file_system, 'label': label, 'mount_point': mount_point,
            'size_total': size_total, 'size_used': size_used, 'size_free': size_free,
            'vendor': vendor, 'model': model}

if __name__ == '__main__':
    usb_devices = list()
    if usb_devices is not None:
        for dev in usb_devices:
            gen.log(details(dev))
