#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui
import string
import re
import sys
import os
import subprocess
import platform
import gen_fun
import config


def detect_distro_isobin(install_dir):
    # Function to detect isolinux.bin path
    if sys.platform.startswith("linux") or platform.system() == "Windows":
        for path, subdirs, files in os.walk(install_dir):
            for name in files:
                if name.endswith('isolinux.bin') or name.endswith('ISOLINUX.BIN'):
                    # return name
                    return os.path.join(path, name)


def strings(filename, min=4):
    # function to extract printable character from binary file. Similar to strings command in linux.
    with open(filename, "rb") as f:
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min:
                yield result
            result = ""


def distro_isolinux_version(isolinu_bin_path):

    # Function to detect version syslinux version shipped by distro developers.
    version = ["3", "4", "5", "6"]
    if not isolinu_bin_path == None:
        sl = list(strings(isolinu_bin_path))
        for strin in sl:
            if re.search(r'isolinux ', strin, re.I):
                for number in version:
                    if re.search(r'isolinux ' + number, strin, re.I):
                        print "\n\nFound syslinux version " + number + "\n\n"
                        config.sys_version = number
                        return str(number)
    """
    elif distro_bin == "":
        print "Distro does not use syslinux"
        return None
    """


def install_default_syslinux(user_password, usb_disk):
    if platform.system() == "Linux":
        syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4"))
        mbr_bin = gen_fun.resource_path(os.path.join("tools", "mbr.bin"))
        if os.access(syslinux, os.X_OK) is False:
            subprocess.call('chmod +x ' + syslinux, shell=True) == 0
        if user_password:
            if subprocess.call('echo ' + user_password + ' | sudo -S ' + syslinux + ' -i -d multibootusb ' +
                                       usb_disk, shell=True) == 0:
                print "Default syslinux install is success..."
                if subprocess.call('echo ' + user_password + ' | sudo -S dd bs=440 count=1 conv=notrunc if=' + mbr_bin +
                                                                                ' of=' + usb_disk[:-1], shell=True) == 0:
                    print "mbr install is success..."
                    return True
                else:
                    print "Failed to install default syslinux..."
                    return False
        else:
            if subprocess.call(syslinux + ' -i -d multibootusb ' + usb_disk, shell=True) == 0:
                print "Default syslinux install is success..."
                if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + usb_disk[:-1],
                                   shell=True) == 0:
                    print "mbr install is success..."
                    return True
                else:
                    print "Failed to install default syslinux..."
                    return False

    elif platform.system() == "Windows":
        syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4.exe"))
        if subprocess.call(syslinux + ' -maf -d multibootusb ' + usb_disk, shell=True) == 0:
            print "Default syslinux install is success..."
            return True
        else:
            print "Failed to install default syslinux..."
            return False


def install_distro_syslinux(distro, iso_link, usb_disk, user_password):
    import iso
    import usb
    usb_details = usb.usb_details(usb_disk)
    usb_mount_path = usb_details['mount']
    usb_filesystem = usb_details['filesystem']

    if usb_filesystem == "vfat" or usb_filesystem == "ntfs" or usb_filesystem == "FAT32":
        if iso.isolinux_bin_dir(iso_link):
            iso.iso_extract_file(iso_link, os.path.join(gen_fun.mbusb_dir(), "iso_cfg_ext_dir"), "isolinux.bin")
            iso.iso_extract_file(iso_link, os.path.join(gen_fun.mbusb_dir(), "iso_cfg_ext_dir"), "ISOLINUX.BIN")
            syslinux_version = distro_isolinux_version(detect_distro_isobin(os.path.join(gen_fun.mbusb_dir(), "iso_cfg_ext_dir")))
            distro_syslinux_install_dir = gen_fun.install_dir(iso_link, usb_mount_path) + iso.isolinux_bin_dir(iso_link)
            distro_syslinux_install_dir = distro_syslinux_install_dir.replace(usb_mount_path, '')
            distro_sys_install_bs = distro_syslinux_install_dir + '/' + distro + '.bs'
            print distro_syslinux_install_dir
            if syslinux_version == str(3):
                    option = " -d "
            else:
                    option = " -i -d "

            if platform.system() == "Linux":
                syslinux = os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux") + syslinux_version
                if os.access(syslinux, os.X_OK) is False:
                    subprocess.call('chmod +x ' + syslinux, shell=True) == 0
                if user_password:
                    if subprocess.call('echo ' + user_password + ' | sudo -S ' + syslinux + option + distro_syslinux_install_dir + ' ' + usb_disk, shell=True) == 0:
                        print "Syslinux install on distro directory is success..."
                        if subprocess.call('echo ' + user_password + ' | sudo -S dd if=' + usb_disk + ' ' + 'of=' + usb_mount_path + distro_sys_install_bs + ' count=1', shell=True) == 0:

                            print "Bootsector copy is success..."
                        else:
                            print "Failed to install syslinux on distro directory..."
                else:
                    if subprocess.call(syslinux + ' -i -d ' + distro_syslinux_install_dir + ' ' + usb_disk, shell=True) == 0:
                        print "Syslinux install on distro directory is success..."
                        if subprocess.call('dd if=' + usb_disk + ' ' + 'of=' + usb_mount_path + distro_sys_install_bs + ' count=1', shell=True) == 0:
                            print "Bootsector copy is success..."
                        else:
                            print "Failed to install syslinux on distro directory..."
            elif platform.system() == "Windows":
                syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin")) + "\syslinux" + syslinux_version + ".exe"
                distro_syslinux_install_dir = "/" + distro_syslinux_install_dir.replace("\\", "/")
                print syslinux + option + distro_syslinux_install_dir + ' ' + usb_disk  + ' ' +  os.path.join(usb_mount_path, distro_sys_install_bs).replace("\\", "/")
                if subprocess.call(syslinux + option + distro_syslinux_install_dir + ' ' + usb_disk + ' ' + os.path.join(usb_mount_path, distro_sys_install_bs).replace("\\", "/"), shell=True) == 0:
                    print "Syslinux install was successful on distro directory..."
                else:
                    print "Failed to install syslinux on distro directory..."