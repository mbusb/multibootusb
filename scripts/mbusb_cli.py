#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     mbusb_cli.py
# Purpose:  Module to handle command line options of multibootusb
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import re
import shutil
from . import usb
from . import gen
from .iso import *
from .uninstall_distro import *
from .distro import *
from .syslinux import *
from .install import *


def read_input_uninstall():
    response = False
    try:
        response = int(input("Please enter the number against the distro you need to uninstall: "))
    except ValueError:
        print('\nPlease provide valid integer from the above list.\n')

    return response


def cli_install_distro():
    '''
    if platform.system() == 'Linux':
        if os.getuid() != 0:
            exit("You need to have root privileges to run this script.\nPlease try again using 'sudo'. Exiting.")
    elif platform.system() == 'Windows':

        if admin.isUserAdmin():
            admin.elevate()
    '''

    print('Starting multibootusb from Command line...')
    if usb.is_block(config.usb_disk) is False:
        print(config.usb_disk, 'is not a valid device partition...')
        exit(1)
    elif integrity(config.iso_link) is not True:
        print(config.iso_link, ' failed to pass integrity check...')
        exit(1)
    elif size_not_enough(config.iso_link, config.usb_disk) is True:
        print(config.usb_disk, 'does not have enough space...')
    else:
        prepare_mbusb_host_dir()
        extract_cfg_file(config.iso_link)
        _distro = distro(iso_cfg_ext_dir(), config.iso_link)
        print('Detected distro type is', _distro)
        if _distro is not None:
            print('\nSelected ISO is          :', quote(iso_name(config.iso_link)))
            print('Selected target device is:', quote(config.usb_disk), '\n')
            print('Please confirm the option.')
            print('Y/y/Yes/yes/YES or N/n/No/no/NO')
            if read_input_yes() is True:
                config.distro = _distro
                copy_mbusb_dir_usb(config.usb_disk)
                install_progress()
                syslinux_distro_dir(config.usb_disk, config.iso_link, _distro)
                syslinux_default(config.usb_disk)
                update_distro_cfg_files(config.iso_link, config.usb_disk, _distro)
        else:
            print('Sorry', iso_name(config.iso_link), 'is not supported at the moment\n'
                                                'Please report tissue at https://github.com/mbusb/multibootusb/issues')


def cli_uninstall_distro():
    distro_list = install_distro_list()
    if distro_list is not None:
        for index, _distro_dir in enumerate(distro_list):
            print(index, '--->>', _distro_dir)
        user_input = read_input_uninstall()
        if user_input is not False:
            for index, _distro_dir in enumerate(distro_list):
                if index == user_input:
                    config.uninstall_distro_dir_name = _distro_dir
                    unin_distro()
    else:
        print('No distro installed on', config.usb_disk)
