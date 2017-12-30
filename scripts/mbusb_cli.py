#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     mbusb_cli.py
# Purpose:  Module to handle command line options of multibootusb
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import ctypes
import platform
from . import usb
from . import gen
from .iso import *
from .uninstall_distro import *
from .distro import *
from .syslinux import *
from .install import *
from . import imager
from . import syslinux


def read_input_uninstall():
    response = False
    try:
        response = int(input("Please enter the number against the distro you need to uninstall: "))
    except ValueError:
        log('\nPlease provide valid integer from the above list.\n')

    return response


def check_admin():
    """
    Check if user has admin rights
    :return: 
    """
    if platform.system() == 'Linux':
        if os.getuid() != 0:
            exit("You need to have root privileges to run this application."
                 "\nPlease try again using 'sudo'. Exiting.")
    elif platform.system() == 'Windows':
        if ctypes.windll.shell32.IsUserAnAdmin() != 1:
            exit("You need to have admin privileges to run this application."
                 "\nPlease open command window with admin rights. Exiting.")

    return False

def cli_install_distro():
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
        # Get the GPT status of the disk and store it on a variable
        usb.gpt_device(config.usb_disk)
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
            log('Detected distro type is    :' + _distro)
            log('\nSelected ISO is          :' + quote(iso_name(iso_image)))
            log('Selected target device is  :' + quote(config.usb_disk), '\n')
            if config.yes is not True:
                log('Please confirm the option.')
                log('Y/y/Yes/yes/YES or N/n/No/no/NO')
                if read_input_yes() is True:
                    config.distro = _distro
                    copy_mbusb_dir_usb(config.usb_disk)
                    install_progress()
                    syslinux_distro_dir(config.usb_disk, iso_image, _distro)
                    syslinux_default(config.usb_disk)
                    replace_grub_binary()
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
                replace_grub_binary()
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


def cli_dd():
    """
    Function to write ISO image directly to USB disk using dd
    :return: 
    """
    if platform.system() == 'Linux':
        if config.usb_disk[-1].isdigit() is True:
            log('Selected USB is a disk partition. Please select the whole disk eg. \'/dev/sdb\'')
            sys.exit(2)

    if not os.path.exists(config.image_path):
        log('ISO image path does not exist. Please correct the path.')
        sys.exit(2)
    else:
        if config.yes is not True:
            log('Initiating destructive writing process for ' + iso.iso_basename(config.image_path))
            log('\nSelected ISO is          :' + quote(iso_name(config.image_path)))
            log('Selected target device is  :' + quote(config.usb_disk))
            log('Writing ISO directly to target USB disk ' + quote(config.usb_disk) + ' will DESTROY ALL DATA.' + '\n')
            log('Please confirm the option.')
            log('Y/y/Yes/yes/YES or N/n/No/no/NO')
            if read_input_yes() is True:
                if platform.system() == 'Linux':
                        imager.dd_linux()
                else:
                    imager.dd_win()
            else:
                log('Operation cancelled by user. Exiting...')
                sys.exit(2)
        else:
            log('\nAuto install is not recommended in direct writing method. Please choose without \'-y\' option.\n')
            sys.exit(2)


def cli_install_syslinux():
    """
    Install syslinux on a target USB disk. It will be installed on 'multibootusb' directory
    :return: 
    """
    usb.gpt_device(config.usb_disk)
    if platform.system() == 'Linux':
        if config.usb_disk[-1].isdigit() is not True:
            log('Selected USB disk is not a partition. Please enter the partition eg. \'/dev/sdb1\'')
            sys.exit(2)

    if config.yes is not True:
        log('\nInitiating process for installing syslinux on ' + config.usb_disk)
        log('Selected target device is  : ' + quote(config.usb_disk))
        log('Syslinux install directory :  ' + quote('multibootusb'))
        log('Please confirm the option.')
        log('Y/y/Yes/yes/YES or N/n/No/no/NO')
        if read_input_yes() is True:
            if syslinux.syslinux_default(config.usb_disk) is True:
                log('Syslinux successfully installed on ' + config.usb_disk)
            else:
                log('Failed to install syslinux on ' + config.usb_disk)
        else:
            log('Operation cancelled by user. Exiting...')
            sys.exit(2)
    else:
        log('\nSkipping user input and installing syslinux on ' + config.usb_disk)
        if syslinux.syslinux_default(config.usb_disk) is True:
            log('Syslinux successfully installed on ' + config.usb_disk)
        else:
            log('Failed to install syslinux on ' + config.usb_disk)
        sys.exit(2)

