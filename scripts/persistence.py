#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     persistence.py
# Purpose:  Module to deal with persistence of a selected distro.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import platform
import tarfile
import subprocess
from . import iso
from . import gen
from . import config

def max_disk_persistence(usb_disk):
    """
    Detect max persistence value for filesystem on usb_disk
    :param usb_disk: Disk filesystem to check
    :return: Max persistence supported (bytes)
    """
    assert usb_disk is not None

    fat_max_size = (4096 * 1024 * 1024)
    usb_details = config.usb_details
    config.usb_uuid = usb_details['uuid']
    config.usb_label = usb_details['label']

    if usb_details['file_system'] in ['vfat', 'FAT32'] and usb_details['size_free'] > fat_max_size:
        _max_size = fat_max_size
    else:
        _max_size = usb_details['size_free']

    return _max_size

def persistence_distro(distro, iso_link):
    """
    Function to detect if distro can have persistence option.
    :param distro: Detected distro name.
    :return: Distro name as string or None otherwise.
    """
    assert distro is not None
    assert iso_link is not None

#     iso_size = iso.iso_size(iso_link)

    if distro in ["ubuntu", "debian", "debian-install", "fedora"]:
        gen.log("Persistence option is available.")
        return distro
    else:
        return None


def create_persistence():
    if config.distro == "ubuntu":
        fs_name = 'casper-rw'
    elif config.distro == 'debian' or config.distro == "debian-install":
        fs_name = 'live-rw'
    elif config.distro == 'fedora':
        fs_name = 'overlay-' + config.usb_label + '-' + config.usb_uuid

    persistence = config.persistence / 1024 / 1024

    if platform.system() == 'Linux':
        mkfs = 'mkfs.ext3'
        dd = 'dd'
        persistence_mkfs_cmd = mkfs + ' -F ' + gen.quote(os.path.join(config.usb_mount, 'multibootusb',
                                                            iso.iso_basename(config.image_path),
                                                            fs_name))
    elif platform.system() == 'Windows':
        mkfs = gen.quote(gen.resource_path(os.path.join("data", "tools", "mkfs", "mke2fs.exe")))
        dd = gen.quote(gen.resource_path(os.path.join("data", "tools", "dd", "dd.exe")))
        persistence_mkfs_cmd = 'echo y|' + mkfs + ' -b 1024 -L ' + fs_name + ' ' + gen.quote(os.path.join(config.usb_mount, 'multibootusb',
                                                            iso.iso_basename(config.image_path), fs_name))

    if config.distro == 'fedora':
        persistence_dd_cmd = dd + ' if=/dev/zero ' \
                                  'of=' + gen.quote(os.path.join(config.usb_mount, 'multibootusb',
                                                       iso.iso_basename(config.image_path), 'LiveOS', fs_name)) + \
                             ' bs=1M count=' + str(int(persistence))
    else:
        persistence_dd_cmd = dd + ' if=/dev/zero of=' + gen.quote(os.path.join(config.usb_mount, 'multibootusb',
                                                   iso.iso_basename(config.image_path), fs_name)) +\
                                ' bs=1M count=' + str(int(persistence))

    gen.log('Executing ==>' + persistence_dd_cmd)
    config.status_text = 'Creating persistence file...'

    if subprocess.call(persistence_dd_cmd, shell=True) == 0:
        gen.log("\nSuccessfully created persistence file...\n")

    if config.distro != 'fedora':
        gen.log('Applying filesystem to persistence file...')
        config.status_text = 'Applying filesystem to persistence file. Please wait...'
        gen.log('Executing ==> ' + persistence_mkfs_cmd)
        config.status_text = 'Applying filesystem to persistence file...'
        if subprocess.call(persistence_mkfs_cmd, shell=True) == 0:
            gen.log("\nSuccessfully applied filesystem...\n")


def extract_file(file_path, install_dir):
    """
    Function to extract persistence files to distro install directory.
    :param file_path: Path to persistence file.
    :param install_dir: Path to distro install directory.
    :return:
    """
    tar = tarfile.open(file_path, "r:bz2")
    tar.extractall(install_dir)
    tar.close()
