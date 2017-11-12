#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Name:     iso.py
# Purpose:  Module to manupulate ISO file
# Authors:  Sundar
# Depends:  isodump3.py (Authored by Johni Lee for MultiBootUSB)
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import re
from .gen import *
from .isodump3 import ISO9660
from . import _7zip


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
        iso_file_list = _7zip.list_iso(iso_link)
        return bool(any("isolinux.bin" in s.lower() for s in iso_file_list))


def iso_size(iso_link):
    return os.path.getsize(iso_link)


def is_readable(iso_link):
    return os.access(iso_link, os.R_OK)


def is_bootable(iso_link):
    """
    Check if an ISO has the ability to boot.
    :return: True if ISO is bootable and False if not.
    """
    try:
        iso9660fs = ISO9660(iso_link)
    except IOError as e:
        log(str(e))
        raise
    isBootable = iso9660fs.checkISOBootable()
    return bool(isBootable)


def isolinux_bin_dir(iso_link):
    """
    Detects "isolinux.bin" directory.
    :return: path of "isolinux.bin" directory as string.
    """
    if os.path.exists(iso_link):
        bin_dir = False
        iso_file_list = _7zip.list_iso(iso_link)
        if any("isolinux.bin" in s.lower() for s in iso_file_list):
            for f in iso_file_list:
                if 'isolinux.bin' in f.lower():
                    if 'efi' not in f.lower():  # Certain distros place their isolinux.bin in to /EFI/BOOT director and we don't want to include them
                        bin_dir = os.path.dirname(f)
                        break

        return bin_dir


def isolinux_bin_path(iso_link):
    """
    Detects pat to "isolinux.bin".
    :return: path of "isolinux.bin" as a string.
    """
    iso_bin_path = False
    if isolinux_bin_exist(iso_link) is not False:
        iso_file_list = _7zip.list_iso(iso_link)
        for f in iso_file_list:
            if 'isolinux.bin' in f.lower():
                iso_bin_path = f
                break

    return iso_bin_path


def iso_menu_lst_path(iso_link):
    """
    Detects pat to "menu.lst" of grub4dos.
    :return: path of "menu.lst" as a string.
    """
    menu_lst_path = False
    iso_file_list = _7zip.list_iso(iso_link)
    for f in iso_file_list:
        if 'menu.lst' in f.lower():
            menu_lst_path = f
            break

    return menu_lst_path


def integrity(iso_link):
    """
    Check the integrity of an ISO.
    :return: True if integrity passes or False if it fails.
    """
    return _7zip.test_iso(iso_link)


def iso_file_list(iso_link):
    """
    Function to return the content of an ISO.
    :return: List of files of an ISO as list.
    """
    return _7zip.list_iso(iso_link)


def isolinux_version(isolinux_bin_path):
    """
    Detect isolinux version shipped by distros.
    :param isolinux_path: Path to "isolinux.bin"
    :return: Version number as string.
    """
    version = ["2", "3", "4", "5", "6"]
    if isolinux_bin_path is not None:
        sl = list(strings(isolinux_bin_path))
        for strin in sl:
            if re.search(r'isolinux ', strin, re.I):
                for number in version:
                    if re.search(r'isolinux ' + number, strin, re.I):
                        log("\nFound syslinux version " + number + "\n")
                        return str(number)


def iso_extract_file(iso_link, dest_dir, _filter):
    """
    Extract the specific file(s) from an ISO
    :param dest_dir: Path to destination directory.
    :param filter: Filter to extract particular file(s)
    :return: Extract file(s) to destination.
    """
    _7zip.extract_iso(iso_link, dest_dir, _filter)


def extract_cfg_file(iso_link):
    """
    Function to extract certain files for auto detecting supported distros
    :param iso_link: Path to ISO file
    :return:
    """
    #_pattern = ['.cfg', '.CFG', '.txt', '.TXT', 'isolinux.bin', 'ISOLINUX.BIN', '.lst']
    _pattern = ['.cfg', '.txt', 'isolinux.bin', '.lst']
    # file_list = iso_file_list(iso_link)
    for ext in _pattern:
        _7zip.extract_iso(iso_link, _iso_cfg_ext_dir, pattern='*' + ext)


def iso_extract_full(iso_link, dest_dir):
    """
    Extract an ISO to destination directory
    :param dest_dir: Destination path as string.
    :return: False if it fails or extract ISO files to destination directory.
    """
    _7zip.extract_iso(iso_link, dest_dir)


def iso_file_path(iso_link, file_name):
    """
    Function to check if file name exist in the ISO
    :param iso_link:Path to ISO file
    :param file_name: file name to be checked
    :return: Path to file as string
    """
    assert iso_link
    assert file_name

    file_path = False
    iso_file_list = _7zip.list_iso(iso_link)
    for f in iso_file_list:
        if file_name in f.lower():
            file_path = f
            break

    return file_path

if __name__ == '__main__':
    #iso_path = '../../../DISTROS/2016/debian-live-8.3.0-amd64-lxde-desktop.iso'
    iso_path = '../../../DISTROS/2015/super_grub2_disk_hybrid_2.02s3.iso'
    test_iso_bin_path = os.path.join('test', 'isolinux', 'isolinux.bin')
    log('iso_name(iso_path) : ', iso_name(iso_path))
    log('iso_basename(iso_path) : ', iso_basename(iso_path))
    log('Integrity of ISO is : ', integrity(iso_path))
    f_list = (iso_file_list(iso_path))
    if f_list:
        for f in f_list:
            log(f)
    log('isolinux_bin_exist(iso_path) : ', isolinux_bin_exist(iso_path))
    #log('is_bootable : ', is_bootable(iso_path))
    log('isolinux_bin_dir() : ', isolinux_bin_dir(iso_path))
    log('isolinux_bin_path(iso_path) : ', isolinux_bin_path(iso_path))
    iso_extract_full(iso_path, 'test')
    iso_extract_file(iso_path, 'test', 'isolinux.bin')
    log(isolinux_version(test_iso_bin_path))
