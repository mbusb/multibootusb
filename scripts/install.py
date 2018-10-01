#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     install.py
# Purpose:  This module contain functions to install ISO files to USB disk non destructively.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import lzma
import os
import platform
import shutil
import subprocess
import threading
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
    install_dir = os.path.join(config.usb_mount, "multibootusb",
                               iso_basename(config.image_path))

    if not os.path.exists(os.path.join(usb_mount, "multibootusb")):
        log("Copying multibootusb directory to " + usb_mount)
        shutil.copytree(
            resource_path(os.path.join("data", "tools", "multibootusb")),
            os.path.join(config.usb_mount, "multibootusb"))

    if not os.path.exists(install_dir):
        _iso_file_list = iso.iso_file_list(config.image_path)
        os.makedirs(install_dir)
        with open(os.path.join(install_dir, "multibootusb.cfg"), "w") as f:
            f.write(config.distro)
        with open(os.path.join(install_dir, "iso_file_list.cfg"), 'w') as f:
            for file_path in _iso_file_list:
                f.write(file_path + "\n")
    else:
        # This path is usually not taken.
        with open(os.path.join(install_dir, "multibootusb.cfg"), "r") as f:
            assert config.distro == f.read()
        with open(os.path.join(install_dir, "iso_file_list.cfg"), 'r') as f:
            _iso_file_list = [s.strip() for s in f.readlines()]

    log("Installing " + iso_name(config.image_path) + " on " + install_dir)

    # Some distros requires certain directories be at the root.
    relocator = DirectoryRelocator(install_dir, usb_mount)

    if config.distro == "opensuse":
        iso.iso_extract_file(config.image_path, install_dir, 'boot')
        config.status_text = "Copying ISO..."
        log("Copying " + config.image_path + " to " + usb_mount)
        copy_iso(config.image_path, usb_mount)
    elif config.distro == "Windows" or config.distro == 'pc-unlocker'\
            or config.distro == 'pc-tool' or config.distro == 'grub2only':
        log("Extracting iso to " + usb_mount)
        iso_extract_full(config.image_path, usb_mount)
    elif config.distro == "trinity-rescue":
        iso_extract_full(config.image_path, install_dir)
        relocator.move(('trk3',))
    elif config.distro == "ipfire":
        iso.iso_extract_file(config.image_path, usb_mount,
                             ['*.tlz', 'distro.img'])
        iso.iso_extract_file(config.image_path, install_dir, 'boot')
    elif config.distro == "zenwalk":
        config.status_text = "Copying ISO..."
        iso.iso_extract_file(config.image_path, install_dir, "kernel")
        copy_iso(config.image_path, install_dir)
    elif config.distro in ["salix-live", 'wifislax']:
        # iso.iso_extract_file(config.image_path, install_dir, "boot")
        iso.iso_extract_file(config.image_path, install_dir,
                             ['*syslinux', '*isolinux', '*system_tools', '*menus', '*vmlinuz', '*initrd*',
                              'EFI'])
        iso.iso_extract_file(config.image_path, usb_mount,
                             ['*modules', '*packages', '*optional',
                              '*liveboot'])
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
        relocator.move(('antivir', 'avupdate', 'system'))
    elif config.distro == 'alpine':
        iso_extract_full(config.image_path, install_dir)
        relocator.move(('apks',))
    elif config.distro == 'insert':
        iso_extract_full(config.image_path, install_dir)
        relocator.move(('INSERT',))
    elif config.distro == 'centos-install' and \
      any(f=='.treeinfo' for f in _iso_file_list):
        # DVD installer
        iso.iso_extract_file(config.image_path, install_dir, '-xr-!Packages')
        log("Copying the source iso file as is.")
        copy_iso(config.image_path, install_dir)
    else:
        iso.iso_extract_full(config.image_path, install_dir)


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
        # Note that xcopy asks if the target is a file or a directory when
        # source filename (or dest filename) contains space(s) and the target
        # does not exist.
        assert os.path.exists(dst)
        subprocess.call(['xcopy', '/Y', src, dst], shell=True)
    elif platform.system() == "Linux":
        shutil.copy(src, dst)


def install_progress():
    """
    Function to calculate progress percentage of install.
    :return:
    """
    from . import progressbar
    try:
        usb_details = details(config.usb_disk)
    except PartitionNotMounted as e:
        log(str(e))
        return

<<<<<<< HEAD
=======
    usb_details = config.usb_details
>>>>>>> upstream/master
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


def replace_syslinux_modules(syslinux_version, under_this_dir):
    # Replace modules files extracted from iso with corresponding
    # version provided by multibootusb.
    modules_src_dir = os.path.join(
        multibootusb_host_dir(), "syslinux", "modules", syslinux_version)

    for dirpath, dirnames, filenames in os.walk(under_this_dir):
        for fname in filenames:
            if not fname.lower().endswith('.c32'):
                continue
            dst_path = os.path.join(under_this_dir, dirpath, fname)
            src_path = os.path.join(modules_src_dir, fname)
            if not os.path.exists(src_path):
                log("Suitable replacement of '%s' is not bundled. "
                    "Trying to unlzma." % fname)
                try:
                    with lzma.open(dst_path) as f:
                        expanded = f.read()
                except lzma.LZMAError:
                    continue
                except (OSError, IOError) as e:
                    log("%s while accessing %s." % (e, dst_path))
                    continue
                with open(dst_path, 'wb') as f:
                    f.write(expanded)
                log("Successfully decompressed %s." % fname)
                continue
            try:
                os.remove(dst_path)
                shutil.copy(src_path, dst_path)
                log("Replaced %s module" % fname)
            except (OSError, IOError) as err:
                log(err)
                log("Could not update " + fname)

def install_patch():
    """
    Function to certain distros which uses makeboot.sh script for making bootable usb disk.
    This is required to make sure that same version (32/64 bit) of modules present is the isolinux directory
    :return:
    """
    isobin_path = isolinux_bin_path(config.image_path)
    if not isobin_path:
        return

    iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(),
                                   "iso_cfg_ext_dir")
    isolinux_path = os.path.join(iso_cfg_ext_dir, isobin_path)
#   iso_linux_bin_dir = isolinux_bin_dir(config.image_path)
    distro_install_dir = os.path.join(
        config.usb_mount, "multibootusb", iso_basename(config.image_path))
    config.syslinux_version = isolinux_version(isolinux_path)

    if config.distro in ['slitaz', 'ubunu']:
        replace_syslinux_modules(config.syslinux_version, distro_install_dir)
    elif config.distro == 'gentoo':
        replace_syslinux_modules(config.syslinux_version, distro_install_dir)
    elif config.distro == 'debian':
        iso_file_list = iso.iso_file_list(config.image_path)
        if not any(s.strip().lower().endswith("makeboot.sh")
                   for s in iso_file_list):
            log('Patch not required...')
            return

        isolinux_bin_dir_ = os.path.join(
            distro_install_dir, isolinux_bin_dir(config.image_path))
        replace_syslinux_modules(config.syslinux_version, isolinux_bin_dir_)


class DirectoryRelocator:
    def __init__(self, src_dir, dst_dir):
        self.src_dir = src_dir
        self.dst_dir = dst_dir

    def move(self, dirs):
        for dir_name in dirs:
            log('Relocating %s from %s to %s' %
                (dir_name, self.src_dir, self.dst_dir))
            src = os.path.join(self.src_dir, dir_name)
            dst = os.path.join(self.dst_dir, dir_name)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(src, dst)

if __name__ == '__main__':
    config.image_path = '../../../DISTROS/2016/slitaz-4.0.iso'
    install_distro()
