#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Name:     iso.py
# Purpose:  Module to manupulate ISO file
# Authors:  Sundar
# Depends:  isodump3.py (Authored by Johni Lee for MultiBootUSB)
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import sys
import os
import string
import platform
import re
from .gen import *
from .isodump3 import ISO9660

_iso_cfg_ext_dir = iso_cfg_ext_dir()

def iso_name(iso_link):
    """
    Find the name of an ISO.
    :return: Name of an ISO (with extension) as string. Returns If not returns None.
    """
    if os.path.exists(iso_link):
        try:
            name = os.path.basename(str(iso_link))
        except:
            name = None
    else:
        name = None

    return name


def iso_basename(iso_link):
    """
    Find the base name of an ISO.
    :return: Base name (without extension) of a selected ISO as string. If not returns None.
    """
    try:
        dir_name = str(os.path.splitext(os.path.basename(str(iso_link)))[0])
    except:
        dir_name = None

    return dir_name


def isolinux_bin_exist(iso_link):
    """
    Check if an "isolinux.bin" file exist.
    :return: True if "isolinux.bin" file exist of False if not.
    """
    if os.path.exists(iso_link):
        iso9660fs = ISO9660(iso_link)
        iso_file_list = iso9660fs.readDir("/")
        if any("isolinux.bin" in s.lower() for s in iso_file_list):
            return True
        else:
            return False


def iso_size(iso_link):
    return os.path.getsize(iso_link)


def is_bootable(iso_link):
    """
    Check if an ISO has the ability to boot.
    :return: True if ISO is bootable and False if not.
    """
    iso9660fs = ISO9660(iso_link)
    isBootable = iso9660fs.checkISOBootable()
    if isBootable:
        return True
    else:
        return False


def isolinux_bin_dir(iso_link):
    """
    Detects "isolinux.bin" directory.
    :return: path of "isolinux.bin" directory as string.
    """
    iso9660fs = ISO9660(iso_link)
    if os.path.exists(iso_link):
        bin_dir = False
        iso_file_list = iso9660fs.readDir("/")
        if any("isolinux.bin" in s.lower() for s in iso_file_list):
            for f in iso_file_list:
                if 'isolinux.bin' in f.lower():
                    bin_dir = os.path.dirname(f)
                    break

        return bin_dir


def isolinux_bin_path(iso_link):
    """
    Detects pat to "isolinux.bin".
    :return: path of "isolinux.bin" directory as string.
    """
    iso_bin_path = False
    if isolinux_bin_exist(iso_link) is not False:

        iso9660fs = ISO9660(iso_link)
        iso_file_list = iso9660fs.readDir("/")
        for f in iso_file_list:
            if 'isolinux.bin' in f.lower():
                iso_bin_path = f
                break

    return iso_bin_path


def integrity(iso_link):
    """
    Check the integrity of an ISO.
    :return: True if integrity passes or False if it fails.
    """
    if os.path.exists(iso_link):
        iso9660fs = ISO9660(iso_link)
        if iso9660fs.checkIntegrity():
            return True
        else:
            return False


def iso_file_list(iso_link):
    """
    Function to return the content of an ISO.
    :return: List of files of an ISO as list.
    """
    iso9660fs = ISO9660(iso_link)
    iso_file_list = iso9660fs.readDir("/")
    return iso_file_list


def isolinux_version(isolinux_bin_path):
    """
    Detect isolinux version shipped by distros.
    :param isolinux_path: Path to "isolinux.bin"
    :return: Version number as string.
    """
    version = ["3", "4", "5", "6"]
    if isolinux_bin_path is not None:
        sl = list(strings(isolinux_bin_path))
        for strin in sl:
            if re.search(r'isolinux ', strin, re.I):
                for number in version:
                    if re.search(r'isolinux ' + number, strin, re.I):
                        print("\n\nFound syslinux version " + number + "\n\n")
                        return str(number)


def iso_extract_file(iso_link, dest_dir, filter):
    """
    Extract the specific file(s) from an ISO
    :param dest_dir: Path to destination directory.
    :param filter: Filter to extract particular file(s)
    :return: Extract file(s) to destination.
    """
    if os.path.exists(iso_link) and os.path.exists(dest_dir):
        iso9660fs = ISO9660(iso_link)
        iso9660fs.writeDir("/", dest_dir, filter)


def extract_cfg_file(iso_link):
    iso_extract_file(iso_link, _iso_cfg_ext_dir, '.cfg')
    iso_extract_file(iso_link, _iso_cfg_ext_dir, '.CFG')
    iso_extract_file(iso_link, _iso_cfg_ext_dir, '.TXT')
    iso_extract_file(iso_link, _iso_cfg_ext_dir, '.txt')
    iso_extract_file(iso_link, _iso_cfg_ext_dir, 'isolinux.bin')
    iso_extract_file(iso_link, _iso_cfg_ext_dir, 'ISOLINUX.BIN')


def iso_extract_full(iso_link, dest_dir):
    """
    Extract an ISO to destination directory
    :param dest_dir: Destination path as string.
    :return: False if it fails or extract ISO files to destination directory.
    """
    iso9660fs = ISO9660(iso_link)
    try:
        iso9660fs.writeDir("/", dest_dir)
    except:
        print("ISO extraction failed.")
        return False


if __name__ == '__main__':
    #iso_path = '../../../DISTROS/2016/debian-live-8.3.0-amd64-lxde-desktop.iso'
    iso_path = '../../../DISTROS/2015/super_grub2_disk_hybrid_2.02s3.iso'
    test_iso_bin_path = os.path.join('test', 'isolinux', 'isolinux.bin')
    print('iso_name(iso_path) : ', iso_name(iso_path))
    print('iso_basename(iso_path) : ', iso_basename(iso_path))
    print('Integrity of ISO is : ', integrity(iso_path))
    f_list = (iso_file_list(iso_path))
    if f_list:
        for f in f_list:
            print(f)
    print('isolinux_bin_exist(iso_path) : ', isolinux_bin_exist(iso_path))
    #print('is_bootable : ', is_bootable(iso_path))
    print('isolinux_bin_dir() : ', isolinux_bin_dir(iso_path))
    print('isolinux_bin_path(iso_path) : ', isolinux_bin_path(iso_path))
    iso_extract_full(iso_path, 'test')
    iso_extract_file(iso_path, 'test', 'isolinux.bin')
    print(isolinux_version(test_iso_bin_path))

