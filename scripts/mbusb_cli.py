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
        log('\nPlease provide valid integer from the above list.\n')

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

    log('Starting multibootusb from Command line...')
    if usb.is_block(config.usb_disk) is False:
        log(config.usb_disk, 'is not a valid device partition...')
        exit(1)
    #elif integrity(config.image_path) is not True:
    #    log(config.image_path, ' failed to pass integrity check...')
    #    exit(1)
    elif size_not_enough(config.image_path, config.usb_disk) is True:
        log(config.usb_disk + 'does not have enough space...')
    else:
        prepare_mbusb_host_dir()
        extract_cfg_file(config.image_path)
        _distro = distro(iso_cfg_ext_dir(), config.image_path)
        if _distro is not None:
            log('Detected distro type is    :' + _distro)
            log('\nSelected ISO is          :'+ quote(iso_name(config.image_path)))
            log('Selected target device is  :'+ quote(config.usb_disk), '\n')
            log('Please confirm the option.')
            log('Y/y/Yes/yes/YES or N/n/No/no/NO')
            if read_input_yes() is True:
                config.distro = _distro
                copy_mbusb_dir_usb(config.usb_disk)
                install_progress()
                syslinux_distro_dir(config.usb_disk, config.image_path, _distro)
                syslinux_default(config.usb_disk)
                update_distro_cfg_files(config.image_path, config.usb_disk, _distro)
        else:
            log('\n\nSorry ' + iso_name(config.image_path) + ' is not supported at the moment.\n'
                'Please report tissue at https://github.com/mbusb/multibootusb/issues\n')


def cli_uninstall_distro():
    distro_list = install_distro_list()
    if distro_list is not None:
        for index, _distro_dir in enumerate(distro_list):
            log(str(index) + '  --->>  ' + _distro_dir)
        user_input = read_input_uninstall()
        if user_input is not False:
            for index, _distro_dir in enumerate(distro_list):
                if index == user_input:
                    config.uninstall_distro_dir_name = _distro_dir
                    unin_distro()
    else:
        log('No distro installed on', config.usb_disk)
