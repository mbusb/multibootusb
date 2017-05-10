#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     uninstall_distro.py
# Purpose:  Module to uninstall distros installed by multibootusb
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import re
import shutil
import threading
import platform
from .usb import *
from . import config
from . import gen


def install_distro_list():
    """
    List all distro names installed by previous install
    :return:  List of distro names as list
    """
    usb_details = details(config.usb_disk)
    config.usb_mount = usb_details['mount_point']
    sys_cfg_file = os.path.join(config.usb_mount, "multibootusb", "syslinux.cfg")

    if os.path.exists(sys_cfg_file):
        distro_list = []
        for line in open(sys_cfg_file):
            if "#start " in line:
                distro_list.append(line[7:])
        return distro_list
    else:
        return None


def unin_distro():
    usb_details = details(config.usb_disk)
    usb_mount = usb_details['mount_point']
    config.uninstall_distro_dir_name = config.uninstall_distro_dir_name.replace('\n', '')
    gen.log(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "multibootusb.cfg"))
    if os.path.exists(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "multibootusb.cfg")):
        with open(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "multibootusb.cfg"), "r") as multibootusb_cfg:
            config.distro = multibootusb_cfg.read().replace('\n', '')
        if config.distro:
            uninstall_distro()
    else:
        return ""


def delete_frm_file_list():
    """
    Generic way to remove files from USB disk.
    :param config.usb_disk:
    :param iso_file_list: List of files installed in the USB disk
    :param config.uninstall_distro_dir_name: Directory where the distro is installed
    :return:
    """
    usb_details = details(config.usb_disk)
    usb_mount = usb_details['mount_point']
    if config.iso_file_list is not None:
        for f in config.iso_file_list:
            if platform.system() == "Windows":
                f = f.replace('\n', '').strip("/").replace("/", "\\")
            else:
                f = f.replace('\n', '').strip("/")
            if os.path.exists(os.path.join(usb_mount, "ldlinux.sys")):
                try:
                    os.chmod(os.path.join(usb_mount, "ldlinux.sys"), 0o777)
                    os.unlink(os.path.join(usb_mount, "ldlinux.sys"))
                except:
                    gen.log('Could not remove ldlinux.sys')

            if os.path.exists(os.path.join(usb_mount, f)):

                if os.path.isdir(os.path.join(usb_mount, f)):
                    gen.log("Removing directory " + (os.path.join(usb_mount, f)))
                    shutil.rmtree(os.path.join(usb_mount, f))

                elif os.path.isfile(os.path.join(usb_mount, f)):
                    gen.log("Removing file " + (os.path.join(usb_mount, f)))
                    os.remove(os.path.join(usb_mount, f))

        if os.path.exists(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "generic.cfg")):
            with open(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "generic.cfg"), "r") as generic_cfg:
                if platform.system() == "Windows":
                    generic = generic_cfg.read().replace('\n', '').replace("/", "\\")
                else:
                    generic = generic_cfg.read().replace('\n', '')
                if os.path.exists(os.path.join(usb_mount, generic.strip("/"))):
                    os.remove(os.path.join(usb_mount, generic.strip("/")))
    if platform.system() == 'Linux':
        gen.log('Removed files from ' + config.uninstall_distro_dir_name)
        gen.log('Syncing....')
        os.sync()




def uninstall_distro():
    """
    Uninstall selected distro from selected USB disk.
    :param config.usb_disk: Path of the USB disk
    :param config.uninstall_distro_dir_name: Directory where the distro is installed
    :param _distro: Generic name applied to distro install by multibootusb
    :return:
    """
    usb_details = details(config.usb_disk)
    usb_mount = usb_details['mount_point']

    if platform.system() == 'Linux':
        os.sync()
        # remove 'immutable' from files on ext2/3/4 fs
        if usb_mount:
            subprocess.call("chattr -i -R %s/* 2>/dev/null" % usb_mount, shell=True)

    if os.path.exists(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "iso_file_list.cfg")):
        with open(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "iso_file_list.cfg"), "r") as f:
            config.iso_file_list = f.readlines()

    for path, subdirs, files in os.walk(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name)):
        for name in files:
            if name.endswith('ldlinux.sys') or name.endswith('ldlinux.c32'):
                os.chmod(os.path.join(path, name), 0o777)
                os.unlink(os.path.join(path, name))

    if config.distro == "opensuse":
        if os.path.exists(os.path.join(usb_mount, config.uninstall_distro_dir_name + ".iso")):
            os.remove(os.path.join(usb_mount, config.uninstall_distro_dir_name + ".iso"))
    elif config.distro == "windows" or config.distro == "alpine" or config.distro == "generic":
        delete_frm_file_list()

    if config.distro == "ipfire":
        files = os.listdir(usb_mount)
        for f in files:
            if f.endswith('.tlz'):
                os.remove(os.path.join(usb_mount, f))
        if os.path.exists(os.path.join(usb_mount, "distro.img")):
            os.remove(os.path.join(usb_mount, "distro.img"))
    elif config.distro == "trinity-rescue":
        shutil.rmtree(os.path.join(usb_mount, "trk3"))

    if os.path.exists(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name)):
        if platform.system() == 'Linux':
            os.sync()
        shutil.rmtree(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name))

    delete_frm_file_list()

    update_sys_cfg_file()
    update_grub_cfg_file()

    # Check if bootx64.efi is replaced by distro
    efi_grub_img = os.path.join(config.usb_mount, 'EFI', 'BOOT', 'bootx64.efi')
    if not os.path.exists(efi_grub_img):
        gen.log('EFI image does not exist. Copying now...')
        os.makedirs(os.path.join(config.usb_mount, 'EFI', 'BOOT'), exist_ok=True)
        shutil.copy2(gen.resource_path(os.path.join("data", "EFI", "BOOT", "bootx64.efi")),
                     os.path.join(config.usb_mount, 'EFI', 'BOOT'))
    elif not gen.grub_efi_exist(efi_grub_img):
        gen.log('EFI image overwritten by distro install. Replacing it now...')
        shutil.copy2(gen.resource_path(os.path.join("data", "EFI", "BOOT", "bootx64.efi")),
                     os.path.join(config.usb_mount, 'EFI', 'BOOT'))
    else:
        gen.log('multibootusb EFI image already exist. Not copying...')


def update_sys_cfg_file():
    """
    Main function to remove uninstall distro specific operations.
    :return:
    """
    if platform.system() == 'Linux':
        os.sync()

    sys_cfg_file = os.path.join(config.usb_mount, "multibootusb", "syslinux.cfg")
    if not os.path.exists(sys_cfg_file):
        gen.log("syslinux.cfg file not found for updating changes.")
    else:
        gen.log("Updating syslinux.cfg file...")
        string = open(sys_cfg_file).read()
        string = re.sub(r'#start ' + config.uninstall_distro_dir_name + '.*?' + '#end ' + config.uninstall_distro_dir_name + '\s*', '', string, flags=re.DOTALL)
        config_file = open(sys_cfg_file, "w")
        config_file.write(string)
        config_file.close()


def update_grub_cfg_file():
    """
    Main function to remove uninstall distro name from the grub.cfg file.
    :return:
    """
    if platform.system() == 'Linux':
        os.sync()

    grub_cfg_file = os.path.join(config.usb_mount, "multibootusb", "grub", "grub.cfg")
    if not os.path.exists(grub_cfg_file):
        gen.log("grub.cfg file not found for updating changes.")
    else:
        gen.log("Updating grub.cfg file...")
        string = open(grub_cfg_file).read()
        string = re.sub(r'#start ' + config.uninstall_distro_dir_name + '.*?' + '#end ' + config.uninstall_distro_dir_name + '\s*', '', string, flags=re.DOTALL)
        config_file = open(grub_cfg_file, "w")
        config_file.write(string)
        config_file.close()


def uninstall_progress():
    """
    Calculate uninstall progress percentage.
    :return:
    """
    from . import progressbar
    usb_details = details(config.usb_disk)
    usb_mount = usb_details['mount_point']
    if platform.system() == 'Linux':
        os.sync()

    if os.path.exists(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "multibootusb.cfg")):
        with open(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name, "multibootusb.cfg"),
                  "r") as multibootusb_cfg:
            config.distro = multibootusb_cfg.read().replace('\n', '')
    else:
        config.distro = ""
    gen.log("Installed distro type is " +  config.distro)

    if config.distro == "opensuse":
        if os.path.exists(os.path.join(usb_mount, config.uninstall_distro_dir_name) + ".iso"):
            folder_size_to_remove = os.path.getsize(os.path.join(usb_mount, config.uninstall_distro_dir_name) + ".iso")
        else:
            folder_size_to_remove = 0
        folder_size_to_remove += disk_usage(str(usb_mount) + "/multibootusb/" + config.uninstall_distro_dir_name).used
    elif config.distro == "windows" or config.distro == "Windows":
        if os.path.exists(os.path.join(usb_mount, "SOURCES")):
            folder_size_to_remove = disk_usage(str(usb_mount) + "/SOURCES").used
        else:
            folder_size_to_remove = disk_usage(str(usb_mount) + "/SSTR").used
    elif config.distro == "ipfire":
        folder_size_to_remove = disk_usage(str(usb_mount) + "/multibootusb/" + config.uninstall_distro_dir_name).used
        files = os.listdir(os.path.join(str(usb_mount)))
        for f in files:
            if f.endswith('.tlz'):
                folder_size_to_remove += os.path.getsize(os.path.join(config.usb_mount, f))
    elif config.distro == "trinity-rescue":
        folder_size_to_remove = disk_usage(os.path.join(usb_mount, "trk3")).used
        folder_size_to_remove += disk_usage(usb_mount + "/multibootusb/" + config.uninstall_distro_dir_name).used
    else:

        folder_size_to_remove = disk_usage(os.path.join(usb_mount, "multibootusb", config.uninstall_distro_dir_name)).used

    thrd = threading.Thread(target=unin_distro, name="uninstall_progress")
    initial_usb_size = disk_usage(usb_mount).used
    thrd.start()
    config.status_text = "Uninstalling " + config.uninstall_distro_dir_name
    pbar = progressbar.ProgressBar(maxval=100).start()  # bar = progressbar.ProgressBar(redirect_stdout=True)
    while thrd.is_alive():
        current_size = disk_usage(usb_mount).used
        diff_size = int(initial_usb_size - current_size)
        config.percentage = round(float(diff_size) / folder_size_to_remove * 100)
        if config.percentage > 100:
            config.percentage = 100

        pbar.update(config.percentage)

    if not thrd.is_alive():
        config.persistence = 0
        config.status_text = ""
