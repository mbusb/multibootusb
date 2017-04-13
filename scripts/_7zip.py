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
        cli_option = ' -bb1'  # Linux does not accept this option (may be due to version diff).
        if suppress_out != '':
            # suppress_out = ' 2> nul'
            suppress_out = ''
    else:
        cli_option = ''
        if suppress_out != '':
            suppress_out = ' 2> /dev/null'

    if not os.path.exists(src):
        gen.log('ISO file could not be found on the location specified.')
        return False
    if not os.path.exists(dst):
        os.makedirs(dst, exist_ok=True)

    if pattern is None:
        _cmd = _7zip + cli_option + ' x -y -o' + gen.quote(dst) + ' ' + gen.quote(src) + suppress_out
    else:
        _cmd = _7zip + ' -y x ' + gen.quote(src) + ' -o' + dst + ' ' + gen.quote(pattern) + ' -r' + suppress_out
    gen.log('Executing ' + _cmd)
    _7zip_process = subprocess.Popen(_cmd, universal_newlines=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE, shell=True)
    config.status_text = 'Status: Extracting ' + os.path.basename(src).strip()
    while True:
        line = _7zip_process.stdout.readline()
        # gen.log(line)
        if line.startswith('- '):
            config.status_text = 'Status: Extracting ' + line[2:].strip()
        elif platform.system() == 'Linux': # line.startswith('Extracting'):  # Under Linux it prints directly all the process (may be due to version diff).
            config.status_text = 'Status: ' + line.strip()
        if line == '' and _7zip_process.poll() != None:
            break


def list_iso(iso_link, suppress_out=True):
    """
    List the content of ISO files. It does'nt work with non 'utf' characters (simply ignores them).
    :param iso_link:Path to ISO link
    :param suppress_out: Option to suppress output to stdout. Default True.
    :return: Path to files as a list
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
        _cmd_out = subprocess.check_output(_cmd, stderr=subprocess.PIPE, shell=True).decode('utf-8', 'ignore').splitlines()
        for line in _cmd_out:
            line = line.split()
            if '.....' in line:
                if gen.has_digit(line[2]) or gen.has_digit(line[4]):
                    if len(line) > 6:
                        f_path = " ".join(line[5:len(line)])
                        file_list.append(f_path)
                    else:
                        f_path = line[-1]
                        file_list.append(f_path)
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

    # gen.log('Executing', _cmd)

    rc = subprocess.call(_cmd, shell=True)

    if rc == 0 or rc == 1:
        return True
    else:
        return False


if __name__ == '__main__':
    # slitaz-4.0.iso
    # ubuntu-16.04-desktop-amd64.iso
    # avg_arl_cdi_all_120_160420a12074.iso
    # haiku-nightly.iso
    # Hiren_BootCD.iso
    file_list = list_iso('../../ubuntu_14_04_backup/Downloads/clonezilla-live-2.4.2-32-amd64.iso')
    for f in file_list:
        print(f)
