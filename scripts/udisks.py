#!/usr/bin/env python3
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
# Name:     udisks.py
# Purpose:  Module to mount unmount and eject using dbus and udisk
# Authors:  Original author is Kovid Goyal <kovid@kovidgoyal.net> and python3
# supporte by Sundar for multibootusb project
# Licence:  'GPL v3' as per original Licence

__license__   = 'GPL v3'
__copyright__ = '2010, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

# from __future__ import print_function
import os
import re


def de_mangle_mountpoint(raw):
    return raw.replace('\\040', ' ').replace('\\011', '\t') \
      .replace('\\012', '\n').replace('\\0134', '\\')

def node_mountpoint(node):

    for line in open('/proc/mounts').readlines():
        line = line.split()
        if line[0] == node:
            return de_mangle_mountpoint(line[1])
    return None

def find_mounted_partitions_on(disk):
    assert not disk[-1:].isdigit()
    with open('/proc/mounts') as f:
        relevant_lines = [l.split(' ') for l in f.readlines()
                          if l.startswith(disk)]
    return [ [v[0], de_mangle_mountpoint(v[1])] + v[2:] for v
             in relevant_lines ]

class NoUDisks1(Exception):
    pass


class UDisks(object):

    def __init__(self):
        import dbus
        self.bus = dbus.SystemBus()
        try:
            self.main = dbus.Interface(self.bus.get_object('org.freedesktop.UDisks',
                        '/org/freedesktop/UDisks'), 'org.freedesktop.UDisks')
        except dbus.exceptions.DBusException as e:
            if getattr(e, '_dbus_error_name', None) == 'org.freedesktop.DBus.Error.ServiceUnknown':
                raise NoUDisks1()
            raise

    def device(self, device_node_path):
        import dbus
        devpath = self.main.FindDeviceByDeviceFile(device_node_path)
        return dbus.Interface(self.bus.get_object('org.freedesktop.UDisks',
                        devpath), 'org.freedesktop.UDisks.Device')

    def mount(self, device_node_path, remounted=None):
        mp = node_mountpoint(str(device_node_path))
        if mp:
            return mp
        d = self.device(device_node_path)
        r = str(d.FilesystemMount(
            '', ['auth_no_user_interaction', 'rw', 'noexec', 'nosuid',
                 'nodev', 'uid=%d'%os.geteuid(), 'gid=%d'%os.getegid()]))
        if remounted is not None:
            remounted.append(True)
        return r

    def unmount(self, device_node_path):
        d = self.device(device_node_path)
        d.FilesystemUnmount(['force'])

    def eject(self, device_node_path):
        parent = device_node_path.rstrip('0123456789')
        d = self.device(parent)
        d.DriveEject([])


class NoUDisks2(Exception):
    pass


class UDisks2(object):

    BLOCK = 'org.freedesktop.UDisks2.Block'
    FILESYSTEM = 'org.freedesktop.UDisks2.Filesystem'
    DRIVE = 'org.freedesktop.UDisks2.Drive'

    def __init__(self):
        import dbus
        self.bus = dbus.SystemBus()
        try:
            self.bus.get_object('org.freedesktop.UDisks2',
                        '/org/freedesktop/UDisks2')
        except dbus.exceptions.DBusException as e:
            if getattr(e, '_dbus_error_name', None) == 'org.freedesktop.DBus.Error.ServiceUnknown':
                raise NoUDisks2()
            raise

    def device(self, device_node_path):
        device_node_path = os.path.realpath(device_node_path)
        devname = device_node_path.split('/')[-1]

        # First we try a direct object path
        bd = self.bus.get_object('org.freedesktop.UDisks2',
                        '/org/freedesktop/UDisks2/block_devices/%s'%devname)
        try:
            device = bd.Get(self.BLOCK, 'Device',
                dbus_interface='org.freedesktop.DBus.Properties')
            device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
        except:
            device = None

        if device == device_node_path:
            return bd

        # Enumerate all devices known to UDisks
        devs = self.bus.get_object('org.freedesktop.UDisks2',
                        '/org/freedesktop/UDisks2/block_devices')
        xml = devs.Introspect(dbus_interface='org.freedesktop.DBus.Introspectable')
        for dev in re.finditer(r'name=[\'"](.+?)[\'"]', type('')(xml)):
            bd = self.bus.get_object('org.freedesktop.UDisks2',
                '/org/freedesktop/UDisks2/block_devices/%s2'%dev.group(1))
            try:
                device = bd.Get(self.BLOCK, 'Device',
                    dbus_interface='org.freedesktop.DBus.Properties')
                device = bytearray(device).replace(b'\x00', b'').decode('utf-8')
            except:
                device = None
            if device == device_node_path:
                return bd

        raise ValueError('%r not known to UDisks2'%device_node_path)

    def rescan(self, node_path):
        # Rescan partition table
        import dbus
        mgr = self.bus.get_object('org.freedesktop.UDisks2',
                            '/org/freedesktop/UDisks2/Manager')
        dev_paths = mgr.ResolveDevice({'path': node_path}, {}, dbus_interface='org.freedesktop.UDisks2.Manager')
        for dev in dev_paths:
            bd = self.bus.get_object('org.freedesktop.UDisks2', dev)
            bd.Rescan('', dbus_interface='org.freedesktop.UDisks2.Block')

    def mount(self, device_node_path, remounted=None):
        mp = node_mountpoint(str(device_node_path))
        if mp:
            return mp
        d = self.device(device_node_path)
        mount_options = ['rw', 'noexec', 'nosuid', 'nodev']
        mp = str(d.Mount(
            {
                'auth.no_user_interaction':True,
                'options':','.join(mount_options)
                },
                dbus_interface=self.FILESYSTEM))
        if remounted is not None:
            remounted.append(True)
        return mp

    def unmount(self, device_node_path):
        d = self.device(device_node_path)
        d.Unmount({'force':True, 'auth.no_user_interaction':True},
                dbus_interface=self.FILESYSTEM)

    def drive_for_device(self, device):
        drive = device.Get(self.BLOCK, 'Drive',
            dbus_interface='org.freedesktop.DBus.Properties')
        return self.bus.get_object('org.freedesktop.UDisks2', drive)

    def eject(self, device_node_path):
        drive = self.drive_for_device(self.device(device_node_path))
        drive.Eject({'auth.no_user_interaction':True},
                dbus_interface=self.DRIVE)


def get_udisks(ver=None):
    if ver is None:
        try:
            u = UDisks2()
        except NoUDisks2:
            u = UDisks()
        return u
    return UDisks2() if ver == 2 else UDisks()


def get_udisks1():
    u = None
    try:
        u = UDisks()
    except NoUDisks1:
        try:
            u = UDisks2()
        except NoUDisks2:
            pass
    if u is None:
        raise EnvironmentError('UDisks not available on your system')
    return u


def mount(node_path):
    u = get_udisks1()
    u.mount(node_path)


def eject(node_path):
    u = get_udisks1()
    u.eject(node_path)


def umount(node_path):
    u = get_udisks1()
    u.unmount(node_path)


def rescan(node_path):
    u = get_udisks()
    u.rescan(node_path)

def test_udisks(ver=None):
    import sys
    dev = sys.argv[1]
    print('Testing with node', dev)
    u = get_udisks(ver=ver)
    print('Using Udisks:', u.__class__.__name__)
    print('Mounted at:', u.mount(dev))
    print('Unmounting')
    u.unmount(dev)
    print('Mounting')
    u.mount(dev)
    print('Ejecting:')
    u.eject(dev)

if __name__ == '__main__':
    print('Run test here...')
    # test_udisks()
