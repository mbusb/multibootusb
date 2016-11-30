#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     install.py
# Purpose:  This module contain functions to install ISO files to USB disk non destructively.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import shutil
import sys
import platform
import threading
import subprocess
from .usb import *
from .gen import *
# from .iso import *
from . import iso
from scripts.update_cfg_file import *
from . import config
from . import persistence


def install_distro():
    """
    Install selected ISO to USB disk.
    :return:
    """
    usb_mount = config.usb_mount
    install_dir = os.path.join(usb_mount, "multibootusb", iso_basename(config.iso_link))
    _iso_file_list = iso.iso_file_list(config.iso_link)

    if not os.path.exists(os.path.join(usb_mount, "multibootusb")):
        print("Copying multibootusb directory to ", usb_mount)
        shutil.copytree(resource_path(os.path.join("data", "tools", "multibootusb")),
                        os.path.join(config.usb_mount, "multibootusb"))

    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
        with open(os.path.join(install_dir, "multibootusb.cfg"), "w") as f:
            f.write(config.distro)
        with open(os.path.join(install_dir, "iso_file_list.cfg"), 'w') as f:
            for file_path in _iso_file_list:
                f.write(file_path + "\n")
    print("Installing ", iso_name(config.iso_link), "on", install_dir)

    if config.distro == "opensuse":
        iso.iso_extract_file(config.iso_link, install_dir, 'boot')
        status_text = "Copying ISO..."
        if platform.system() == "Windows":
            subprocess.call(["xcopy", config.iso_link, usb_mount], shell=True)  # Have to use xcopy as python file copy is dead slow.
        elif platform.system() == "Linux":
            print(config.iso_link, usb_mount)
            shutil.copy(config.iso_link, usb_mount)
    elif config.distro == "Windows" or config.distro == "alpine":
        print("Extracting iso to " + usb_mount)
        iso_extract_full(config.iso_link, usb_mount)
    elif config.distro == "trinity-rescue":
        iso.iso_extract_file(config.iso_link, usb_mount, '*trk3')
    elif config.distro == "ipfire":
        iso.iso_extract_file(config.iso_link, usb_mount, '*.tlz')
        iso.iso_extract_file(config.iso_link, usb_mount, 'distro.img')
        iso.iso_extract_file(config.iso_link, install_dir, 'boot')
    elif config.distro == "zenwalk":
        config.status_text = "Copying ISO..."
        iso.iso_extract_file(config.iso_link, install_dir, "kernel")
        copy_iso(config.iso_link, install_dir)
    elif config.distro == "salix-live":
        # iso.iso_extract_file(config.iso_link, install_dir, "boot")
        iso.iso_extract_file(config.iso_link, install_dir, '*syslinux')
        iso.iso_extract_file(config.iso_link, install_dir, '*menus')
        iso.iso_extract_file(config.iso_link, install_dir, '*vmlinuz')
        iso.iso_extract_file(config.iso_link, install_dir, '*initrd*')
        iso.iso_extract_file(config.iso_link, usb_mount, '*modules')
        iso.iso_extract_file(config.iso_link, usb_mount, '*packages')
        iso.iso_extract_file(config.iso_link, usb_mount, '*optional')
        iso.iso_extract_file(config.iso_link, usb_mount, '*liveboot')
        #iso.iso_extract_full(config.iso_link, usb_mount)
        # config.status_text = "Copying ISO..."
        # copy_iso(config.iso_link, install_dir)
    elif config.distro == 'sgrubd2':
        copy_iso(config.iso_link, install_dir)
    elif config.distro == 'alt-linux':
        iso.iso_extract_file(config.iso_link, install_dir, '-xr!*rescue')
        iso.iso_extract_file(config.iso_link, config.usb_mount, 'rescue')
    elif config.distro == "generic":
        #with open(os.path.join(install_dir, "generic.cfg"), "w") as f:
        #    f.write(os.path.join(isolinux_bin_dir(config.iso_link), "generic") + ".bs")
        iso_extract_full(config.iso_link, usb_mount)
    elif config.distro == 'grub4dos':
        iso_extract_full(config.iso_link, usb_mount)
    elif config.distro == 'ReactOS':
        iso_extract_full(config.iso_link, usb_mount)
    else:
        iso.iso_extract_full(config.iso_link, install_dir)

    if platform.system() == 'Linux':
        print('ISO extracted successfully. Sync is in progress...')
        os.system('sync')

    if config.persistence != 0:
        config.status_text = 'Creating Persistence...'
        persistence.create_persistence()

    install_patch()


def copy_iso(src, dst):
    if platform.system() == "Windows":
        subprocess.call("xcopy " + src + " " + dst, shell=True)
    elif platform.system() == "Linux":
        shutil.copy(src, dst)

def install_progress():
    """
    Function to calculate progress percentage of install.
    :return:
    """
    from . import progressbar

    usb_details = details(config.usb_disk)
    usb_mount = usb_details['mount_point']
    usb_size_used = usb_details['size_used']
    thrd = threading.Thread(target=install_distro, name="install_progress")
    # thrd.daemon()
    # install_size = usb_size_used / 1024
    install_size = iso_size(config.iso_link) / 1024
    final_size = (usb_size_used + iso_size(config.iso_link)) + config.persistence
    thrd.start()
    pbar = progressbar.ProgressBar(maxval=100).start()  # bar = progressbar.ProgressBar(redirect_stdout=True)
    while thrd.is_alive():
        current_size = details(config.usb_disk)['size_used']
        percentage = int((current_size / final_size) * 100)
        if percentage > 100:
            percentage = 100
        config.percentage = percentage
        pbar.update(percentage)


def install_patch():
    """
    Function to certain distros which uses makeboot.sh script for making bootable usb disk.
    This is required to make sure that same version (32/64 bit) of modules present is the isolinux directory
    :return:
    """
    if config.distro == 'debian':
        if platform.system() == 'Linux':  # Need to syn under Linux. Otherwise, USB disk becomes random read only.
            os.system('sync')
        iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir")
        isolinux_path = os.path.join(iso_cfg_ext_dir, isolinux_bin_path(config.iso_link))
        iso_linux_bin_dir = isolinux_bin_dir(config.iso_link)
        config.syslinux_version = isolinux_version(isolinux_path)
        iso_file_list = iso.iso_file_list(config.iso_link)
        os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link), isolinux_bin_dir(config.iso_link))
        if any("makeboot.sh" in s.lower() for s in iso_file_list):
            for module in os.listdir(os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link),
                                                  isolinux_bin_dir(config.iso_link))):
                if module.endswith(".c32"):
                    if os.path.exists(os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link),
                                                   isolinux_bin_dir(config.iso_link), module)):
                        try:
                            os.remove(os.path.join(config.usb_mount, "multibootusb",
                                                   iso_basename(config.iso_link), isolinux_bin_dir(config.iso_link), module))
                            print("Copying ", module)
                            print((resource_path(
                                os.path.join(multibootusb_host_dir(), "syslinux", "modules", config.syslinux_version, module)),
                                        os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link),
                                                     isolinux_bin_dir(config.iso_link), module)))
                            shutil.copy(resource_path(
                                os.path.join(multibootusb_host_dir(), "syslinux", "modules", config.syslinux_version, module)),
                                        os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link),
                                                     isolinux_bin_dir(config.iso_link), module))
                        except Exception as err:
                            print(err)
                            print("Could not copy ", module)
        else:
            print('Patch not required...')


if __name__ == '__main__':
    config.iso_link = '../../../DISTROS/2016/slitaz-4.0.iso'
    install_distro()
