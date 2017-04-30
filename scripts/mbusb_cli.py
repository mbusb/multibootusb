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
        log(config.usb_disk + ' is not a valid device partition...')
        exit(1)
    #elif integrity(config.image_path) is not True:
    #    log(config.image_path + ' failed to pass integrity check...')
    #    exit(1)
    else:
        usb_details = details(config.usb_disk)
        config.usb_mount = usb_details['mount_point']
        config.usb_uuid = usb_details['uuid']
        config.usb_label = usb_details['label']
        prepare_mbusb_host_dir()
        if isinstance(config.image_path, str) is True:
            iso_install(config.image_path)
        elif isinstance(config.image_path, list) is True:
            # Transfer the list to other variable and loop through iso image
            iso_list = config.image_path
            for config.image_path in iso_list:
                iso_install(config.image_path)


def iso_install(iso_image):
    """
    Script for installing iso image to a disk. This can be called by other script for auto install of many distros
    :param iso_image: Path to ISO image
    :return: 
    """
    if size_not_enough(iso_image, config.usb_disk) is True:
        log(config.usb_disk + ' does not have enough space...')
    else:
        clean_iso_cfg_ext_dir(os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir"))  # Need to be cleaned everytime
        extract_cfg_file(iso_image)
        _distro = distro(iso_cfg_ext_dir(), iso_image)
        if _distro is not None:
            log('Initiating installation process for ' + iso.iso_basename(iso_image))
            if config.yes is not True:
                log('Detected distro type is    :' + _distro)
                log('\nSelected ISO is          :' + quote(iso_name(iso_image)))
                log('Selected target device is  :' + quote(config.usb_disk), '\n')
                log('Please confirm the option.')
                log('Y/y/Yes/yes/YES or N/n/No/no/NO')
                if read_input_yes() is True:
                    config.distro = _distro
                    copy_mbusb_dir_usb(config.usb_disk)
                    install_progress()
                    syslinux_distro_dir(config.usb_disk, iso_image, _distro)
                    syslinux_default(config.usb_disk)
                    update_distro_cfg_files(iso_image, config.usb_disk, _distro)
                    log('Finished installing ' + iso.iso_basename(iso_image))
                else:
                    log('Not proceeding. User cancelled the operation.')
            else:
                log('Skipping user confirmation for ' + iso_image)
                config.distro = _distro
                copy_mbusb_dir_usb(config.usb_disk)
                install_progress()
                syslinux_distro_dir(config.usb_disk, iso_image, _distro)
                syslinux_default(config.usb_disk)
                update_distro_cfg_files(iso_image, config.usb_disk, _distro)
                log('Finished installing ' + iso.iso_basename(iso_image))

        else:
            log('\n\nSorry ' + iso_name(iso_image) + ' is not supported at the moment.\n'
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
        log('No distro installed on ' + config.usb_disk)
