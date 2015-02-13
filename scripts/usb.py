#!/usr/bin/python2.7
# coding: utf-8
import collections
import sys
import os
import platform
import ctypes


def disk_usage(mount_path):
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


def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n


def get_usb():
    devices = []

    if platform.system() == "Linux":
        import pyudev
        import dbus
        try:
            print "Using PyUdev for detecting USB drives..."
            context = pyudev.Context()
            for device in context.list_devices(subsystem='block', DEVTYPE='partition', ID_FS_USAGE="filesystem",
                                               ID_TYPE="disk", ID_BUS="usb"):
                if device['ID_BUS'] == "usb" and device['DEVTYPE'] == "partition":
                    devices.append(device['DEVNAME'])
        except:
            try:
                print "Falling back to Udisks2.."
                bus = dbus.SystemBus()
                ud_manager_obj = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
                om = dbus.Interface(ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')
                for k,v in om.GetManagedObjects().iteritems():
                    drive_info = v.get('org.freedesktop.UDisks2.Block', {})
                    if drive_info.get('IdUsage') == "filesystem" and not drive_info.get('HintSystem') and not drive_info.get('ReadOnly'):
                        device = drive_info.get('Device')
                        device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                        devices.append(device)
            except:
                try:
                    print "Falling back to Udisks1..."
                    bus = dbus.SystemBus()
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
                    print "No device found..."

    elif platform.system() == "Windows":
        import win32com.client
        oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
        oDrives = oFS.Drives
        for drive in oDrives:
            if drive.DriveType == 1 and drive.IsReady:
                devices.append(drive)

    return devices


def usb_details(selected_device):
    drive = {}
    if selected_device:

        if platform.system() == "Linux":
            import pyudev
            import dbus
            try:
                """
                Try with PyUdev to get the details of USB disks.
                This is the easiest and reliable method to find USB details.
                Also, it is a standalone package and no dependencies are required.
                """
                print "Using PyUdev for detecting USB details..."
                context = pyudev.Context()
                for device in context.list_devices(subsystem='block', DEVTYPE='partition', ID_FS_USAGE="filesystem",
                                                   ID_TYPE="disk", ID_BUS="usb"):
                    if device['ID_BUS'] == "usb" and device['DEVTYPE'] == "partition":
                        if (device['DEVNAME']) == selected_device:
                            uuid = device['ID_FS_UUID']
                            file_system = device['ID_FS_TYPE']
                            mount_point_strip = os.popen('mount | grep %s | cut -d" " -f3' % selected_device).read().strip()
                            try:
                                label = device['ID_FS_LABEL']
                                print 'Name of the USB partition is %s'%label
                            except:
                                label = "No label."
                '''
                drive = {'label': label,
                            'mount': mount_point_strip,
                            'uuid': uuid,
                            'filesystem': file_system,
                            'device': selected_device,
                            'total_size': bytes2human(disk_usage(mount_point_strip).total),
                            'free_size': bytes2human(disk_usage(mount_point_strip).free),
                            'used_size': bytes2human(disk_usage(mount_point_strip).used)}
                '''
            except:
                try:
                    """
                    Now lets try with UDisks2. The latest but painful software.
                    """
                    print "Falling back to UDisks2 for detecting USB details..."
                    bus = dbus.SystemBus()
                    bd = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2/block_devices%s'%device[4:])
                    device = bd.Get('org.freedesktop.UDisks2.Block', 'Device', dbus_interface='org.freedesktop.DBus.Properties')
                    device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
                    uuid = bd.Get('org.freedesktop.UDisks2.Block', 'IdUUID', dbus_interface='org.freedesktop.DBus.Properties')
                    file_system =  bd.Get('org.freedesktop.UDisks2.Block', 'IdType', dbus_interface='org.freedesktop.DBus.Properties')
                    mount_point = bd.Get('org.freedesktop.UDisks2.Filesystem', 'MountPoints', dbus_interface='org.freedesktop.DBus.Properties')
                    mount_point = bytearray(mount_point[0]).decode('utf-8')
                    mount_point_strip = str(mount_point.replace(b'\x00', b''))
                    try:
                        label = bd.Get('org.freedesktop.UDisks2.Block', 'IdLabel', dbus_interface='org.freedesktop.DBus.Properties')
                        print 'Name of the USB partition is %s'%label
                    except:
                        label = "No label."
                    '''
                    drive = {'label': label,
                            'mount': mount_point_strip,
                            'uuid': uuid,
                            'filesystem': file_system,
                            'device': device,
                            'total_size': bytes2human(disk_usage(mount_point_strip).total),
                            'free_size': bytes2human(disk_usage(mount_point_strip).free),
                            'used_size': bytes2human(disk_usage(mount_point_strip).used)}
                    '''
                except:
                    try:
                        """
                        Finally we will try with UDisks(1).
                        """
                        print "Falling back to UDisks as a last choice for getting USB details..."
                        bus = dbus.SystemBus()
                        device_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks/devices" + device[4:])
                        device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
                        selected_device = device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile")
                        mount_point_strip = device_props.Get('org.freedesktop.UDisks.Device', "DeviceMountPaths")[0]
                        uuid = device_props.Get('org.freedesktop.UDisks.Device', "IdUuid")
                        file_system =  device_props.Get('org.freedesktop.UDisks.Device', "IdType")
                        try:
                            label = device_props.Get('org.freedesktop.UDisks.Device', "IdLabel")
                        except:
                            label = "No label."
                    except:
                        print "Error detecting USB details."

        else:
            import win32com.client
            try:
                selected_usb_part = str(selected_device)
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
                mount_point_strip = selected_usb_device + ":\\"
                file_system = d.FileSystem
                '''
                selected_usb_total_size = psutil.disk_usage(selected_usb_mount_path)[0]
                selected_usb_avail_size = psutil.disk_usage(selected_usb_mount_path)[2]
                selected_usb_used_size = psutil.disk_usage(selected_usb_mount_path)[1]

                drive = {'label': label,
                        'mount': mount_point_strip,
                        'uuid': uuid,
                        'filesystem': file_system,
                        'device': selected_device,
                        'total_size': bytes2human(disk_usage(mount_point_strip).total),
                        'free_size': bytes2human(disk_usage(mount_point_strip).free),
                        'used_size': bytes2human(disk_usage(mount_point_strip).used)}
                '''
            except:
                print "Error detecting USB details."
    if mount_point_strip:
        print "Device mounted."
        total_size = bytes2human(disk_usage(mount_point_strip).total)
        free_size = bytes2human(disk_usage(mount_point_strip).free)
        used_size = bytes2human(disk_usage(mount_point_strip).used)
    else:
        mount_point_strip = "Not mounted."
        total_size = "Not mounted."
        free_size = "Device not mounted."
        used_size = "Device not mounted."
        print "fail"

    drive = {'label': label,
            'mount': mount_point_strip,
            'uuid': uuid,
            'filesystem': file_system,
            'device': selected_device,
            'total_size': total_size,
            'free_size': free_size,
            'used_size': used_size}


    return drive


'''
devices = get_usb()
for dev in devices:
    print dev
    deteials = usb_details(dev)
    print deteials['mount']
'''