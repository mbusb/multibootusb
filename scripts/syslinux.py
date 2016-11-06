#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     syslinux.py
# Purpose:  Module to install syslinux and extlinux on selected USB disk.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import sys
import subprocess
import platform
from .gen import *
from . import usb
from .iso import *
from . import config

extlinux_path = os.path.join(multibootusb_host_dir(), "syslinux", "bin", "extlinux4")
syslinux_path = os.path.join(multibootusb_host_dir(), "syslinux", "bin", "syslinux4")
extlinux_fs = ["ext2", "ext3", "ext4", "Btrfs"]
syslinux_fs = ["vfat", "ntfs", "FAT32", "NTFS"]
mbr_bin = resource_path(os.path.join("data", "tools", "mbr.bin"))


def set_boot_flag(usb_disk):
    if platform.system() == "Linux":
        print("\nChecking boot flag on " + usb_disk[:-1], '\n')
        cmd_out = subprocess.check_output("parted -m -s " + usb_disk[:-1] + " print", shell=True)
        if b'boot' in cmd_out:
            print("\nDisk " + usb_disk[:-1] + " already has boot flag.\n")
            return True
        else:
            print("\nExecuting ==>  parted " + usb_disk[:-1] + " set 1 boot on", '\n')
            if subprocess.call("parted " + usb_disk[:-1] + " set 1 boot on", shell=True) == 0:
                print("\nBoot flag set to bootable " + usb_disk[:-1], '\n')
                return True
            else:
                print("\nUnable to set boot flag on  " + usb_disk[:-1], '\n')
                return False


def syslinux_default(usb_disk, version=4):
    """
    Install Syslinux of a selected drive
    :param usb_disk: '/dev/sdx' on linux and 'E:' on Windows
    :version: Default version is 4. Change it if you wish. But necessary files needs to be copied accordingly
    :return: Bootable USB disk :-)
    """
    usb_details = usb.details(usb_disk)
    usb_fs = usb_details['file_system']
    usb_mount = usb_details['mount_point']
    mbr_install_cmd = 'dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + usb_disk[:-1]
    print(usb_fs)
    if usb_fs in extlinux_fs:
        extlinu_cmd = extlinux_path + ' --install ' + os.path.join(usb_mount, 'multibootusb')
        if os.access(extlinux_path, os.X_OK) is False:
            subprocess.call('chmod +x ' + extlinux_path, shell=True)
        print("\nExecuting ==> " + extlinu_cmd)
        if subprocess.call(extlinu_cmd, shell=True) == 0:
            print("\nDefault Extlinux install is success...\n")
            print('\nExecuting ==> ' + mbr_install_cmd)
            if subprocess.call(mbr_install_cmd, shell=True) == 0:
                print("\nmbr install is success...\n")
                if set_boot_flag(usb_disk) is True:
                    return True

    elif usb_fs in syslinux_fs:

        if platform.system() == "Linux":
            syslinux_cmd = syslinux_path + ' -i -d multibootusb ' + usb_disk
            if os.access(syslinux_path, os.X_OK) is False:
                subprocess.call('chmod +x ' + syslinux_path, shell=True)
            print("\nExecuting ==> " + syslinux_cmd + "\n")
            if subprocess.call(syslinux_cmd, shell=True) == 0:
                print("\nDefault syslinux install is success...\n")
                if subprocess.call(mbr_install_cmd, shell=True) == 0:
                    print("\nmbr install is success...\n")
                    if set_boot_flag(usb_disk) is True:
                        return True
                    else:
                        print("\nFailed to install default syslinux...\n")
                        return False

        elif platform.system() == "Windows":
            syslinux = resource_path(os.path.join(multibootusb_host_dir(), "syslinux", "bin", "syslinux4.exe"))
            print('Executing ==>', syslinux + ' -maf -d multibootusb ' + usb_disk)
            if subprocess.call(syslinux + ' -maf -d multibootusb ' + usb_disk, shell=True) == 0:
                print("\nDefault syslinux install is success...\n")
                return True
            else:
                print("\nFailed to install default syslinux...\n")
                return False


def syslinux_distro_dir(usb_disk, iso_link, distro):
    """
    Install syslinux/extlinux on distro specific isolinux directory.
    :param usb_disk: '/dev/sdx' on linux and 'E:' on Windows
    :param iso_link: Path to ISO file
    :return:
    """
    usb_details = usb.details(usb_disk)
    usb_fs = usb_details['file_system']
    usb_mount = usb_details['mount_point']
    isolinux_bin_dir(iso_link)
    if isolinux_bin_exist(iso_link) is False:
        print('Distro does not use isolinux for booting ISO.')
    else:
        iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir")
        isolinux_path = os.path.join(iso_cfg_ext_dir, isolinux_bin_path(iso_link)[1:])
        iso_linux_bin_dir = isolinux_bin_dir(iso_link)
        config.syslinux_version = isolinux_version(isolinux_path)

        if distro == "generic" or distro == "alpine":
            install_dir = usb_mount
            distro_syslinux_install_dir = os.path.join(usb_mount, iso_linux_bin_dir[1:].strip("/")).replace(usb_mount, "")
            distro_sys_install_bs = os.path.join(install_dir, iso_linux_bin_dir[1:].strip("/"), distro + '.bs')
        else:
            install_dir = os.path.join(usb_mount, "multibootusb", iso_basename(iso_link))
            distro_syslinux_install_dir = os.path.join(install_dir, iso_linux_bin_dir[1:].strip("/")).replace(usb_mount, "")
            distro_sys_install_bs = os.path.join(install_dir, iso_linux_bin_dir[1:].strip("/"), distro + '.bs')
            print(distro_sys_install_bs)
            print(distro_syslinux_install_dir)

        if usb_fs in syslinux_fs:
            if config.syslinux_version == str(3):
                if distro == "generic" and iso_linux_bin_dir == "/":
                    option = ""
                else:
                    option = " -d "
            else:
                if distro == "generic" and iso_linux_bin_dir == "/":
                    option = " -i "
                else:
                    option = " -i -d "

            if platform.system() == "Linux":
                syslinux_path = os.path.join(multibootusb_host_dir(), "syslinux", "bin", "syslinux") + config.syslinux_version
                if os.access(syslinux_path, os.X_OK) is False:
                    subprocess.call('chmod +x ' + syslinux_path, shell=True) == 0
                sys_cmd = syslinux_path + option + quote(distro_syslinux_install_dir) + ' ' + usb_disk
                dd_cmd = 'dd if=' + usb_disk + ' ' + 'of=' + quote(distro_sys_install_bs) + ' count=1'
                print("Executing ==> ", sys_cmd)
                if subprocess.call(sys_cmd, shell=True) == 0:
                    print("\nSyslinux install on distro directory is success...\n")
                    print('Executing ==> ', dd_cmd, '\n')
                    if subprocess.call(dd_cmd, shell=True) == 0:
                        print("\nBootsector copy is success...\n")
                    else:
                        print("\nFailed to copy boot sector...\n")
                else:
                    print("\nFailed to install syslinux on distro directory...\n")
            elif platform.system() == "Windows":
                syslinux_path = resource_path(os.path.join(multibootusb_host_dir(), "syslinux", "bin")) + \
                                "\syslinux" + config.syslinux_version + ".exe"
                distro_syslinux_install_dir = "/" + distro_syslinux_install_dir.replace("\\", "/")
                distro_sys_install_bs = distro_sys_install_bs.replace("/", "\\")
                sys_cmd = syslinux_path + option + distro_syslinux_install_dir + ' ' + usb_disk + ' ' + \
                          distro_sys_install_bs
                print("\nExecuting ==> ", sys_cmd, '\n')
                if subprocess.call(sys_cmd, shell=True) == 0:
                    print("\nSyslinux install was successful on distro directory...\n")
                else:
                    print("\nFailed to install syslinux on distro directory...\n")
        elif usb_fs in extlinux_fs:
            if platform.system() == "Linux":
                distro_syslinux_install_dir = os.path.join(install_dir, iso_linux_bin_dir.strip("/"))
                syslinux_path = os.path.join(multibootusb_host_dir(), "syslinux", "bin", "extlinux") + config.syslinux_version
                ext_cmd = syslinux_path + " --install " + distro_syslinux_install_dir
                dd_cmd = 'dd if=' + usb_disk + ' ' + 'of=' + usb_mount + quote(distro_sys_install_bs) + ' count=1'
                if os.access(syslinux_path, os.X_OK) is False:
                    subprocess.call('chmod +x ' + syslinux_path, shell=True) == 0
                print("Executing ==> ", ext_cmd)
                if subprocess.call(ext_cmd, shell=True) == 0:
                    print("\nSyslinux install on distro directory is success...\n")
                    print('Executing ==> ', dd_cmd, '\n')
                    if subprocess.call(dd_cmd, shell=True) == 0:
                        print("\nBootsector copy is success...\n")
                    else:
                        print("\nFailed to install syslinux on distro directory...\n")

if __name__ == '__main__':
    if os.geteuid() != 0:
        print('Please running this script with sudo/root/admin privilage.')
        exit(1)
    else:
        syslinux_distro_dir('/dev/sdb1', '../../../DISTROS/2016/debian-live-8.3.0-amd64-lxde-desktop.iso', 'debian')
        syslinux_default('/dev/sdb1')
