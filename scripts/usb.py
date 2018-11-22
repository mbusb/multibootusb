#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     usb.py
# Purpose:  Module to list USB devices and get details under Linux and Windows
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import collections
import ctypes
import os
import platform
import shutil
import subprocess
import sys
import time

if platform.system()=='Linux':
    import dbus

from . import config
from . import gen
from . import osdriver

if platform.system() == 'Linux':
    from . import udisks
    UDISKS = udisks.get_udisks(ver=None)

if platform.system() == 'Windows':
    import win32com.client


class PartitionNotMounted(Exception):

    def __init__(self, partition):
        self.message = 'Partition is not mounted: {}'.format(partition)


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


def list_devices(fixed=False):
    """
    List inserted USB devices.
    :return: USB devices as list.
    """
    devices = []
    if platform.system() == "Linux":
        try:
            # pyudev is good enough to detect USB devices on modern Linux machines.
            gen.log("Using pyudev for detecting USB drives...")
            try:
                import pyudev
            except Exception as e:
                gen.log('PyUdev is not installed on host system, using built-in.')
                from . import pyudev
            context = pyudev.Context()

            for device in context.list_devices(subsystem='block'):
                if fixed is True:
                    if device.get('DEVTYPE') in ['disk', 'partition'] and device.get('ID_PART_TABLE_TYPE'):
                        devices.append(str(device.get('DEVNAME')))
                        gen.log("\t" + device.get('DEVNAME'))
                else:
                    if device.get('ID_BUS') in ['usb'] and device.get('ID_PART_TABLE_TYPE'):
                        devices.append(str(device.get('DEVNAME')))
                        gen.log("\t" + device.get('DEVNAME'))

        except Exception as e:
            gen.log(e)
            bus = dbus.SystemBus()
            try:
                # You should come here only if your system does'nt have udev installed.
                # We will use udiskd2 for now.
                gen.log("Falling back to Udisks2..")
                ud_manager_obj = bus.get_object(
                    'org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
                ud_manager = dbus.Interface(
                    ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')
                for k, v in ud_manager.GetManagedObjects().items():
                    drive_info = v.get('org.freedesktop.UDisks2.Block', {})
                    if fixed is True:
                        if drive_info.get('IdUsage') == "filesystem" and not drive_info.get('ReadOnly'):
                            device = drive_info.get('Device')
                            device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                            devices.append(device)
                    else:
                        if drive_info.get('IdUsage') == "filesystem" and not drive_info.get(
                                'HintSystem') and not drive_info.get('ReadOnly'):
                            device = drive_info.get('Device')
                            device = bytearray(device).replace(
                                b'\x00', b'').decode('utf-8')
                            devices.append(device)

            except Exception as e:
                gen.log(e, error=True)
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
                except Exception as e:
                    gen.log(e, error=True)
                    gen.log("No USB device found...")

        devices.sort()

    elif platform.system() == "Windows":
        volumes = osdriver.wmi_get_volume_info_all()
        devices = []
        for pdrive in osdriver.wmi_get_physicaldrive_info_all():
            if (not fixed) and pdrive.MediaType != 'Removable Media':
                continue
            devices.append(osdriver.win_physicaldrive_to_listbox_entry(pdrive))
            devices.extend([osdriver.win_volume_to_listbox_entry(d)
                            for d in volumes.get(pdrive.Index, [])])
    if devices:
        return devices
    else:
        gen.log("No USB device found...")
        return None


def parent_partition(partition):
    exploded = [c for c in partition]
    while exploded[-1].isdigit():
        exploded.pop()
    return ''.join(exploded)


def details_udev(usb_disk_part):
    """
    Get details of USB partition using udev
    """
    assert usb_disk_part is not None
    assert platform.system() == "Linux"

    try:
        import pyudev
    except:
        from . import pyudev
#   Try with PyUdev to get the details of USB disks.
#   This is the easiest and reliable method to find USB details.
#   Also, it is a standalone package and no dependencies are required.
    context = pyudev.Context()
    try:
        device = pyudev.Device.from_device_file(context, usb_disk_part)
    except:
        gen.log("ERROR: Unknown disk/partition (%s)" % str(usb_disk_part))
        return None

    try:
        ppart = parent_partition(usb_disk_part)
        fdisk_cmd_out = subprocess.check_output(
            'LANG=C fdisk -l ' + ppart, shell=True)
        partition_prefix = bytes(usb_disk_part, 'utf-8') + b' '
        out = []
        for l in fdisk_cmd_out.split(b'\n'):
            if not l.startswith(b'/dev/'):
                out.append(l)
                continue
            if l.startswith(partition_prefix):
                out.append(l)
            # filter out non-relevant partition info
        fdisk_cmd_out = b'\n'.join(out)

    except subprocess.CalledProcessError:
        gen.log("ERROR: fdisk failed on disk/partition (%s)" %
                str(usb_disk_part))
        return None

    detected_type = None
    for keyword, ptype in [(b'Extended', 'extended partition'),
                           (b'swap', 'swap partition'),
                           (b'Linux LVM', 'lvm partition'),]:
        if keyword in fdisk_cmd_out:
            detected_type = ptype
            break
    if detected_type:
        mount_point = ''
        uuid = ''
        file_system = ''
        vendor = ''
        model = ''
        label = ''
        devtype = detected_type
    elif device.get('DEVTYPE') == "partition":
        uuid = device.get('ID_FS_UUID') or ""
        file_system = device.get('ID_FS_TYPE') or ""
        label = device.get('ID_FS_LABEL') or ""
        remounted = []
        mount_point = UDISKS.mount(usb_disk_part, remounted) or ""
        if remounted and remounted[0]:
            config.add_remounted(usb_disk_part)
        mount_point = mount_point.replace('\\x20', ' ')
        vendor = device.get('ID_VENDOR') or ""
        model = device.get('ID_MODEL') or ""
        devtype = "partition"

    elif device.get('DEVTYPE') == "disk":
        mount_point = ""
        uuid = ""
        file_system = ""
        label = device.get('ID_FS_LABEL') or ""
        vendor = device.get('ID_VENDOR') or ""
        model = device.get('ID_MODEL') or ""
        devtype = "disk"

    if mount_point not in ["", "None"]:
        size_total = shutil.disk_usage(mount_point)[0]
        size_used = shutil.disk_usage(mount_point)[1]
        size_free = shutil.disk_usage(mount_point)[2]

    else:
        fdisk_cmd = 'LANG=C fdisk -l ' + usb_disk_part + \
          ' | grep "^Disk /" | sed -re "s/.*\s([0-9]+)\sbytes.*/\\1/"'
        size_total = subprocess.check_output(fdisk_cmd, shell=True).strip()
        size_used = 0
        size_free = 0
        mount_point = ""

    return {'uuid': uuid, 'file_system': file_system, 'label': label, 'mount_point': mount_point,
            'size_total': size_total, 'size_used': size_used, 'size_free': size_free,
            'vendor': vendor, 'model': model, 'devtype': devtype}


def details_udisks2(usb_disk_part):
    """
    Get details of USB disk detail.
    usb_disk_part: It is the partition of an USB removable disk.
    """
    import dbus
    bus = dbus.SystemBus()

    mount_point = ''
    uuid = ''
    file_system = ''
    vendor = ''
    model = ''
    label = ''
    devtype = "disk"

    bd = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2/block_devices%s'%usb_disk_part[4:])
    device = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
    device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
    if device[-1].isdigit() is True:
        uuid = bd.Get('org.freedesktop.UDisks2.Block', 'IdUUID', dbus_interface='org.freedesktop.DBus.Properties')
        file_system = bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
        mount_point = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
        devtype = 'partition'
    else:
        devtype = 'disk'
        file_system = 'No_File_System'
    if mount_point:
        # mount_point = str(bytearray(mount_point[0]).decode('utf-8').replace(b'\x00', b''))
        mount_point = bytearray(mount_point[0]).replace(b'\x00', b'').decode('utf-8')
    else:
        try:
            mount_point = UDISKS.mount(usb_disk_part)
            config.add_remounted(usb_disk_part)
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
            size_total, size_used, size_free = \
                        shutil.disk_usage(mount_point)[:3]
    else:
        raise PartitionNotMounted(usb_disk_part)

    return {'uuid': uuid, 'file_system': file_system, 'label': label, 'mount_point': mount_point,
            'size_total': size_total, 'size_used': size_used, 'size_free': size_free,
            'vendor': vendor, 'model': model, 'devtype': devtype}


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


def gpt_device(dev_name):
    """
    Find if the device inserted is GPT or not. We will just change the variable parameter in config file for later use
    :param dev_name:
    :return: True if GPT else False
    """
    is_gpt = osdriver.gpt_device(dev_name)
    config.usb_gpt = is_gpt
    gen.log('Device %s is %s disk.' % (dev_name, is_gpt and 'a GPT' or 'an MBR'))


def unmount(usb_disk):
    UDISKS.unmount(usb_disk)


class RemountError(Exception):
    def __init__(self, caught_exception, *args, **kw):
        super(RemountError, self).__init__(*args, **kw)
        self.caught_exception = caught_exception

    def __str__(self):
        return "%s due to '%s'" % (
            self.__class__.__name__, self.caught_exception)


class UnmountError(RemountError):
    def __init__(self, *args, **kw):
        super(UnmountError, self).__init__(*args, **kw)


class MountError(RemountError):
    def __init__(self, *args, **kw):
        super(MountError, self).__init__(*args, **kw)


class UnmountedContext:
    def __init__(self, usb_disk, exit_callback):
        self.usb_disk = usb_disk
        self.exit_callback = exit_callback
        self.is_relevant = platform.system() != 'Windows' and \
          self.usb_disk[-1:].isdigit()

    def assert_no_access(self):
        p = subprocess.Popen(['lsof', self.usb_disk],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)
        output = p.communicate()
        if len(output[0].strip()) != 0:
            gen.log("Open handle exists.")
            gen.log(output[0])
            raise UnmountError(Exception('open handle exists.'))

    def __enter__(self):
        if not self.is_relevant:
            return
        self.assert_no_access()
        try:
            gen.log("Unmounting %s" % self.usb_disk)
            os.sync() # This is needed because UDISK.unmount() can timeout.
            UDISKS.unmount(self.usb_disk)
        except dbus.exceptions.DBusException as e:
            gen.log("Unmount of %s has failed." % self.usb_disk)
            # This may get the partition mounted. Don't call!
            # self.exit_callback(details(self.usb_disk))
            raise UnmountError(e)
        gen.log("Unmounted %s" % self.usb_disk)
        return self

    def __exit__(self, type_, value, traceback_):
        if not self.is_relevant:
            return
        os.sync()     # This should not be strictly necessary
        time.sleep(1)  # Yikes, mount always fails without this sleep().
        try:
            mount_point = UDISKS.mount(self.usb_disk)
            config.add_remounted(self.usb_disk)
            self.exit_callback(details(self.usb_disk))
        except dbus.exceptions.DBusException as e:
            raise MountError(e)
        gen.log("Mounted %s" % (self.usb_disk))


def check_vfat_filesystem(usb_disk, result=None):
    p = subprocess.Popen(['fsck.vfat', '-n', usb_disk],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE)
    output = p.communicate()
    gen.log("fsck.vfat -n returned %d" % p.returncode)
    gen.log(b"fsck.vfat -n said:" + b'\n---\n'.join(f for f in output if f))
    if result is not None:
        result.append((p.returncode, output, 'fsck.vfat -n'))
    return len(output[0].split(b'\n'))==3 and output[1]==b'' \
           and p.returncode==0


def repair_vfat_filesystem(usb_disk, result=None):
    for args, input_ in [
            (['-a', usb_disk], None,      ),
            (['-r', usb_disk], b'1\ny\n', ),
            ]:
        cmd = ['fsck.vfat'] + args
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        output = p.communicate(input=input_)
        gen.log("%s returned %d" % (' '.join(cmd), p.returncode))
        gen.log(b"It said:" + b'\n---\n'.join(f for f in output if f))
        if result is not None:
            result.append((p.returncode, output, ' '.join(cmd)))
    return None

def details(disk_or_partition):
    """
    Populate and get details of an USB disk.
    :param disk_or_partition: USB disk. Example.. "/dev/sdb1" on Linux and "D:\" on Windows.
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

    assert disk_or_partition is not None

    details = {}

    if platform.system() == 'Linux':
        try:
            details = details_udev(disk_or_partition)
        except:
            details = details_udisks2(disk_or_partition)
    elif platform.system() == 'Windows':
        if type(disk_or_partition) == int:
            details = osdriver.wmi_get_physicaldrive_info_ex(disk_or_partition)
        else:
            details = osdriver.wmi_get_volume_info_ex(disk_or_partition)
    return details


if __name__ == '__main__':
    usb_devices = list_devices()
    if usb_devices is not None:
        for dev in usb_devices:
            gen.log(details(dev))
