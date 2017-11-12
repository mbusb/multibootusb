#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     install.py
# Purpose:  This module contain functions to install ISO files to USB disk non destructively.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import shutil
import platform
import threading
import subprocess
import time
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
    install_dir = os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path))
    _iso_file_list = iso.iso_file_list(config.image_path)

    if not os.path.exists(os.path.join(usb_mount, "multibootusb")):
        log("Copying multibootusb directory to " + usb_mount)
        shutil.copytree(resource_path(os.path.join("data", "tools", "multibootusb")),
                        os.path.join(config.usb_mount, "multibootusb"))

    if not os.path.exists(install_dir):
        os.makedirs(install_dir)
        with open(os.path.join(install_dir, "multibootusb.cfg"), "w") as f:
            f.write(config.distro)
        with open(os.path.join(install_dir, "iso_file_list.cfg"), 'w') as f:
            for file_path in _iso_file_list:
                f.write(file_path + "\n")
    log("Installing " + iso_name(config.image_path) + " on " + install_dir)

    if config.distro == "opensuse":
        iso.iso_extract_file(config.image_path, install_dir, 'boot')
        config.status_text = "Copying ISO..."
        if platform.system() == "Windows":
            subprocess.call(["xcopy", config.image_path, usb_mount], shell=True)  # Have to use xcopy as python file copy is dead slow.
        elif platform.system() == "Linux":
            log("Copying " + config.image_path + " to " + usb_mount)
            shutil.copy(config.image_path, usb_mount)
    elif config.distro == "Windows" or config.distro == 'pc-unlocker'\
            or config.distro == 'pc-tool' or config.distro == 'grub2only':
        log("Extracting iso to " + usb_mount)
        iso_extract_full(config.image_path, usb_mount)
    elif config.distro == "trinity-rescue":
        iso_extract_full(config.image_path, install_dir)
        if os.path.exists(os.path.join(usb_mount, 'trk3')):
            shutil.rmtree(os.path.join(usb_mount, 'trk3'))
        shutil.move(os.path.join(install_dir, 'trk3'), os.path.join(usb_mount))
    elif config.distro == "ipfire":
        iso.iso_extract_file(config.image_path, usb_mount, '*.tlz')
        iso.iso_extract_file(config.image_path, usb_mount, 'distro.img')
        iso.iso_extract_file(config.image_path, install_dir, 'boot')
    elif config.distro == "zenwalk":
        config.status_text = "Copying ISO..."
        iso.iso_extract_file(config.image_path, install_dir, "kernel")
        copy_iso(config.image_path, install_dir)
    elif config.distro == "salix-live":
        # iso.iso_extract_file(config.image_path, install_dir, "boot")
        iso.iso_extract_file(config.image_path, install_dir, '*syslinux')
        iso.iso_extract_file(config.image_path, install_dir, '*menus')
        iso.iso_extract_file(config.image_path, install_dir, '*vmlinuz')
        iso.iso_extract_file(config.image_path, install_dir, '*initrd*')
        iso.iso_extract_file(config.image_path, usb_mount, '*modules')
        iso.iso_extract_file(config.image_path, usb_mount, '*packages')
        iso.iso_extract_file(config.image_path, usb_mount, '*optional')
        iso.iso_extract_file(config.image_path, usb_mount, '*liveboot')
        #iso.iso_extract_full(config.image_path, usb_mount)
        config.status_text = "Copying ISO..."
        copy_iso(config.image_path, install_dir)
    elif config.distro == "rising-av":
        iso.iso_extract_file(config.image_path, install_dir, '*boot')
        iso.iso_extract_file(config.image_path, usb_mount, '*rising')
    elif config.distro == 'sgrubd2':
        copy_iso(config.image_path, install_dir)
    elif config.distro == 'alt-linux':
        iso.iso_extract_file(config.image_path, install_dir, '-xr!*rescue')
        iso.iso_extract_file(config.image_path, config.usb_mount, 'rescue')
    elif config.distro == "generic":
        #with open(os.path.join(install_dir, "generic.cfg"), "w") as f:
        #    f.write(os.path.join(isolinux_bin_dir(config.image_path), "generic") + ".bs")
        iso_extract_full(config.image_path, usb_mount)
    elif config.distro == 'grub4dos':
        iso_extract_full(config.image_path, usb_mount)
    elif config.distro == 'ReactOS':
        iso_extract_full(config.image_path, usb_mount)
    elif config.distro == 'grub4dos_iso' or config.distro == 'raw_iso' or config.distro == 'memdisk_iso' or \
                    config.distro == 'memdisk_img':
        copy_iso(config.image_path, install_dir)
    elif config.distro == 'Avira-RS':
        iso_extract_full(config.image_path, install_dir)
        # we want following directories on root of the USB drive. Ensure the previous directories are removed before moving.
        if os.path.exists(os.path.join(usb_mount, 'antivir')):
            shutil.rmtree(os.path.join(usb_mount, 'antivir'))
            shutil.move(os.path.join(install_dir, 'antivir'), os.path.join(usb_mount))
        if os.path.exists(os.path.join(usb_mount, 'avupdate')):
            shutil.rmtree(os.path.join(usb_mount, 'avupdate'))
            shutil.move(os.path.join(install_dir, 'avupdate'), os.path.join(usb_mount))
        if os.path.exists(os.path.join(usb_mount, 'system')):
            shutil.rmtree(os.path.join(usb_mount, 'system'))
            shutil.move(os.path.join(install_dir, 'system'), os.path.join(usb_mount))
    elif config.distro == 'alpine':
        iso_extract_full(config.image_path, install_dir)
        if os.path.exists(os.path.join(usb_mount, 'apks')):
            shutil.rmtree(os.path.join(usb_mount, 'apks'))
        shutil.move(os.path.join(install_dir, 'apks'), os.path.join(usb_mount))
    elif config.distro == 'insert':
        iso_extract_full(config.image_path, install_dir)
        if os.path.exists(os.path.join(usb_mount, 'INSERT')):
            shutil.rmtree(os.path.join(usb_mount, 'INSERT'))
        shutil.move(os.path.join(install_dir, 'INSERT'), os.path.join(usb_mount))
    else:
        iso.iso_extract_full(config.image_path, install_dir)

    if platform.system() == 'Linux':
        log('ISO extracted successfully. Sync is in progress...')
        os.sync()

    if config.persistence != 0:
        log('Creating persistence...')
        config.status_text = 'Creating persistence...'
        persistence.create_persistence()

    install_patch()


def copy_iso(src, dst):
    """
    A simple wrapper for copying larger files. This is necessary as
    shutil copy files is much slower under Windows platform
    :param src: Path to source file
    :param dst: Destination directory
    :return:
    """
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
    config.usb_mount = usb_details['mount_point']
    usb_size_used = usb_details['size_used']
    thrd = threading.Thread(target=install_distro, name="install_progress")
    # thrd.daemon()
    # install_size = usb_size_used / 1024
#     install_size = iso_size(config.image_path) / 1024
    final_size = (usb_size_used + iso_size(config.image_path)) + config.persistence
    thrd.start()
    pbar = progressbar.ProgressBar(maxval=100).start()  # bar = progressbar.ProgressBar(redirect_stdout=True)
    while thrd.is_alive():
        current_size = shutil.disk_usage(usb_details['mount_point'])[1]
        percentage = int((current_size / final_size) * 100)
        if percentage > 100:
            percentage = 100
        config.percentage = percentage
        pbar.update(percentage)
        time.sleep(0.1)


def install_patch():
    """
    Function to certain distros which uses makeboot.sh script for making bootable usb disk.
    This is required to make sure that same version (32/64 bit) of modules present is the isolinux directory
    :return:
    """
    if config.distro == 'debian':
        if platform.system() == 'Linux':  # Need to syn under Linux. Otherwise, USB disk becomes random read only.
            os.sync()
        iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir")
        isolinux_path = os.path.join(iso_cfg_ext_dir, isolinux_bin_path(config.image_path))
#         iso_linux_bin_dir = isolinux_bin_dir(config.image_path)
        config.syslinux_version = isolinux_version(isolinux_path)
        iso_file_list = iso.iso_file_list(config.image_path)
        os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path), isolinux_bin_dir(config.image_path))
        if any("makeboot.sh" in s.lower() for s in iso_file_list):
            for module in os.listdir(os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path),
                                                  isolinux_bin_dir(config.image_path))):
                if module.endswith(".c32"):
                    if os.path.exists(os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path),
                                                   isolinux_bin_dir(config.image_path), module)):
                        try:
                            os.remove(os.path.join(config.usb_mount, "multibootusb",
                                                   iso_basename(config.image_path), isolinux_bin_dir(config.image_path), module))
                            log("Copying " +  module)
                            log((resource_path(
                                os.path.join(multibootusb_host_dir(), "syslinux", "modules", config.syslinux_version, module)),
                                        os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path),
                                                     isolinux_bin_dir(config.image_path), module)))
                            shutil.copy(resource_path(
                                os.path.join(multibootusb_host_dir(), "syslinux", "modules", config.syslinux_version, module)),
                                        os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path),
                                                     isolinux_bin_dir(config.image_path), module))
                        except Exception as err:
                            log(err)
                            log("Could not copy " + module)
        else:
            log('Patch not required...')


if __name__ == '__main__':
    config.image_path = '../../../DISTROS/2016/slitaz-4.0.iso'
    install_distro()
