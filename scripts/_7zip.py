#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     7zip.py
# Purpose:  Wrapper module to list and extract ISO files using 7zip
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import platform
import subprocess
from . import config
from . import gen

if platform.system() == 'Windows':
    _7zip = gen.quote(gen.resource_path(os.path.join('data', 'tools', '7zip', '7z.exe')))
else:
    _7zip = '7z'


def extract_iso(src, dst, pattern=None, suppress_out=True):
    """
    Simple wrapper function to extract ISO file to destination
    :param src: Path to ISO file
    :param dst: Path to directory where the files are to be extracted
    :param patter: The pattern to match the files to be extracted
    :return:
    """
    # 7z x -y -oC:\path_to_directory X:\path_to_iso_file.iso
    # 7z e archive.zip -oC:\path_to_directory *.cfg *.bin -r
    if platform.system() == 'Windows':
        cli_option = ' -ssc- -bb1'  # Linux does not accept this option (may be due to version diff).
        if suppress_out != '':
            # suppress_out = ' 2> nul'
            suppress_out = ''
    else:
        cli_option = ' -ssc- '
        if suppress_out != '':
            suppress_out = ' 2> /dev/null'

    if not os.path.exists(src):
        gen.log('ISO file could not be found on the location specified.')
        return False
    if not os.path.exists(dst):
        os.makedirs(dst, exist_ok=True)

    src = gen.quote(src)
    dst = gen.quote(dst)
    if pattern is None:
        _cmd = _7zip + cli_option + ' x -y -o' + dst + ' ' + src + suppress_out
    else:
        if type(pattern) is str:
            pattern = [pattern]
        pattern_str = ' '.join(gen.quote(s) for s in pattern)
        _cmd = _7zip + cli_option + ' x -y ' + src + \
               ' -o' + dst + ' ' + pattern_str + ' -r' + suppress_out
    gen.log('Executing ==> ' + _cmd)

    config.status_text = 'Status: Extracting ' + os.path.basename(src).strip()
    with open(os.devnull, 'w') as devnull:
        subprocess.call(_cmd, stdin=devnull, stdout=devnull, stderr=devnull, shell=True)


def list_iso(iso_link, suppress_out=True):
    """
    List the content of ISO files. It does'nt work with non 'utf' characters (simply ignores them).
    :param iso_link:Path to ISO link
    :param suppress_out: Option to suppress output to stdout. Default True.
    :return: Path to files and directories as a list
    """
    if platform.system() == 'Windows':
        if suppress_out is True:
            suppress_out = ' 2> nul'
    else:
        if suppress_out is True:
            suppress_out = ' 2> /dev/null'
    if not os.path.exists(iso_link):
        gen.log('Path to ISO link does not exist.')
        return False
    else:
        file_list = []
        _cmd = _7zip + ' l ' + gen.quote(iso_link) + suppress_out
        try:
            _cmd_out = subprocess.check_output(_cmd, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                               shell=True).decode('utf-8', 'ignore').splitlines()
        except Exception as e:
            gen.log(e)
            _cmd_out = ''
        for line in _cmd_out:
            if '...' in line:
                line = line.split()
                _path = line[-1]
                file_list.append(_path)
        return file_list


def test_iso(iso_link, suppress_out=True):
    """
    Function to test if ISO file is corrupted. Relying only on 7zip.
    :param iso_link: Path to ISO file
    :return: True if test is positive
    """
    # 7z t /path/to/iso/file.iso
    # return value : 0 No error
    # return value : 1 Warning (Non fatal error(s))
    # return value : 2 Fatal error
    # return value : 7 Command line error
    # return value : 8 Not enough memory for operation
    # return value : 255 User stopped the process

    if platform.system() == 'Windows':
        if suppress_out is True:
            suppress_out = ' > nul'
    else:
        if suppress_out is True:
            suppress_out = ' > /dev/null'

    _cmd = _7zip + ' t ' + iso_link + suppress_out

    gen.log('Executing ==> ' + _cmd)

    rc = subprocess.call(_cmd, shell=True)

    return bool(rc in [0, 1])

def test_extraction():
    import shutil

    src = 'c:/Users/shinj/Downloads/clonezilla-live-2.5.2-31-amd64.iso'
    tmp_dir = 'c:/Users/shinj/Documents/tmp'
    for subdir, pattern in [
            ('single_string', 'EFI/'),
            ('single_list', ['EFI/']),
            ('multi', ['EFI/', 'syslinux/']),
            ('all', None) ]:
        dest_dir = os.path.join(tmp_dir, subdir)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        os.mkdir(dest_dir)
        args = [src, dest_dir]
        if pattern is not None:
            args.append(pattern)
        print ('Calling extract_iso(%s)' % args)
        extract_iso(*args)

if __name__ == '__main__':
    # slitaz-4.0.iso
    # ubuntu-16.04-desktop-amd64.iso
    # avg_arl_cdi_all_120_160420a12074.iso
    # haiku-nightly.iso
    # Hiren_BootCD.iso
    file_list = list_iso('../../ubuntu_14_04_backup/Downloads/clonezilla-live-2.4.2-32-amd64.iso')
    for f in file_list:
        print(f)
