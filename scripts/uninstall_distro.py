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
    usb_details = config.usb_details
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


class UninstallThread(threading.Thread):

    def __init__(self, target_distro, uninstall_distro_dir_name, *args, **kw):
        super(UninstallThread, self).__init__(*args, **kw)
        self.target_distro = target_distro
        self.uninstall_distro_dir_name = uninstall_distro_dir_name

    def run(self):
        do_uninstall_distro(self.target_distro, self.uninstall_distro_dir_name)


def delete_frm_file_list(iso_file_list, uninstall_distro_dir_name):
    """
    Generic way to remove files from USB disk.
    :param config.usb_disk:
    :param iso_file_list: List of files installed in the USB disk
    :param config.uninstall_distro_dir_name: Directory where the distro is installed
    :return:
    """
    usb_details = config.usb_details
    usb_mount = usb_details['mount_point']
    if iso_file_list is not None:
        for f in iso_file_list:
            f = f.replace('\n', '').strip("/")
            if platform.system() == "Windows":
                f = f.replace("/", "\\")
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

        generic_cfg_fullpath = os.path.join(
            usb_mount, "multibootusb", uninstall_distro_dir_name,
            "generic.cfg")
        if os.path.exists(generic_cfg_fullpath):
            with open(generic_cfg_fullpath, "r") as generic_cfg:
                generic = generic_cfg.read().replace('\n', '')
                if platform.system() == "Windows":
                    generic = generic_cfg.read().replace("/", "\\")
                if os.path.exists(os.path.join(usb_mount, generic.strip("/"))):
                    os.remove(os.path.join(usb_mount, generic.strip("/")))
    gen.log('Removed files from ' + uninstall_distro_dir_name)
    if platform.system() == 'Linux':
        gen.log('Syncing....')
        os.sync()




def do_uninstall_distro(target_distro, uninstall_distro_dir_name):
    """
    Uninstall selected distro from selected USB disk.
    :param config.usb_disk: Path of the USB disk
    :param target_distro: Generic name applied to distro to be uninstalled
    :param uninstall_distro_dir_name: Directory where the distro is installed
    :return:
    """
    usb_details = config.usb_details
    usb_mount = usb_details['mount_point']

    if platform.system() == 'Linux':
        os.sync()
        # remove 'immutable' from files on ext2/3/4 fs
        if usb_mount:
            subprocess.call("chattr -i -R %s/* 2>/dev/null" % usb_mount, shell=True)

    uninstall_distro_dir_name_fullpath = os.path.join(
        usb_mount, "multibootusb", uninstall_distro_dir_name)
    uninstall_distro_iso_name = os.path.join(
        usb_mount, uninstall_distro_dir_name) + '.iso'
    filelist_fname = os.path.join(uninstall_distro_dir_name_fullpath,
                                  "iso_file_list.cfg")
    if os.path.exists(filelist_fname):
        with open(filelist_fname, "r") as f:
            iso_file_list = f.readlines()
    else:
        iso_file_list = []

    for path, subdirs, files in os.walk(uninstall_distro_dir_name_fullpath):
        for name in files:
            if name.endswith(('ldlinux.sys', 'ldlinux.c32')):
                os.chmod(os.path.join(path, name), 0o777)
                os.unlink(os.path.join(path, name))

    if target_distro == "opensuse":
        if os.path.exists(uninstall_distro_iso_name):
            os.remove(uninstall_distro_iso_name)
    elif target_distro in ["windows", "alpine", "generic"]:
        # This function will be called anyway after this if/elif block
        # delete_frm_file_list()
        pass
    elif target_distro == "ipfire":
        files = os.listdir(usb_mount)
        for f in files:
            if f.endswith('.tlz'):
                os.remove(os.path.join(usb_mount, f))
        if os.path.exists(os.path.join(usb_mount, "distro.img")):
            os.remove(os.path.join(usb_mount, "distro.img"))
    elif target_distro == "trinity-rescue":
        shutil.rmtree(os.path.join(usb_mount, "trk3"))

    if os.path.exists(uninstall_distro_dir_name_fullpath):
        if platform.system() == 'Linux':
            os.sync()
        shutil.rmtree(uninstall_distro_dir_name_fullpath)

    delete_frm_file_list(iso_file_list, uninstall_distro_dir_name)

    update_sys_cfg_file(uninstall_distro_dir_name)
    update_grub_cfg_file(uninstall_distro_dir_name)

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


def update_sys_cfg_file(uninstall_distro_dir_name):
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
        string = re.sub(r'#start ' + re.escape(uninstall_distro_dir_name)
                        + '.*?' + '#end '
                        + re.escape(uninstall_distro_dir_name)
                        + r'\s*', '', string, flags=re.DOTALL)
        config_file = open(sys_cfg_file, "w")
        config_file.write(string)
        config_file.close()


def update_grub_cfg_file(uninstall_distro_dir_name):
    """
    Main function to remove uninstall distro name from the grub.cfg file.
    :return:
    """
    if platform.system() == 'Linux':
        os.sync()

    grub_cfg_file = os.path.join(config.usb_mount, "multibootusb",
                                 "grub", "grub.cfg")
    if not os.path.exists(grub_cfg_file):
        gen.log("grub.cfg file not found for updating changes.")
    else:
        gen.log("Updating grub.cfg file...")
        string = open(grub_cfg_file).read()
        string = re.sub(r'#start ' + re.escape(uninstall_distro_dir_name)
                        + '.*?' + '#end '
                        + re.escape(uninstall_distro_dir_name)
                        + r'\s*', '', string, flags=re.DOTALL)
        config_file = open(grub_cfg_file, "w")
        config_file.write(string)
        config_file.close()


def uninstall_progress():
    """
    Start another thread that does the actual uninstallation work
    and continuously calculate uninstall progress percentage.
    This is the entry point for the uninstallation thread spawned
    in GuiUninstallProgress.__init__.
    :return:
    """
    from . import progressbar
    usb_details = config.usb_details
    usb_mount = usb_details['mount_point']
    if platform.system() == 'Linux':
        os.sync()

    uninstall_distro_dir_name = config.uninstall_distro_dir_name \
                                .replace('\n', '')

    drive_relative_mbcfg_path = os.path.join(
        "multibootusb", uninstall_distro_dir_name, "multibootusb.cfg")
    mbcfg_fullpath = os.path.join(usb_mount, drive_relative_mbcfg_path)
    if os.path.exists(mbcfg_fullpath):
        with open(mbcfg_fullpath,"r") as multibootusb_cfg:
            target_distro = multibootusb_cfg.read().replace('\n', '')
    else:
        target_distro = ""
    gen.log("Installed distro type is " +  target_distro or "unknown")

    if target_distro == "opensuse":
        iso_fullpath = os.path.join(usb_mount, uninstall_distro_dir_name) \
                       + ".iso"
        if os.path.exists(iso_fullpath):
            folder_size_to_remove = os.path.getsize(iso_fullpath)
        else:
            folder_size_to_remove = 0
        folder_size_to_remove += disk_usage(str(usb_mount) + "/multibootusb/" + uninstall_distro_dir_name).used
    elif target_distro == "windows" or target_distro == "Windows":
        if os.path.exists(os.path.join(usb_mount, "SOURCES")):
            folder_size_to_remove = disk_usage(str(usb_mount) + "/SOURCES").used
        else:
            folder_size_to_remove = disk_usage(str(usb_mount) + "/SSTR").used
    elif target_distro == "ipfire":
        folder_size_to_remove = disk_usage(str(usb_mount) + "/multibootusb/" + uninstall_distro_dir_name).used
        files = os.listdir(os.path.join(str(usb_mount)))
        for f in files:
            if f.endswith('.tlz'):
                folder_size_to_remove += os.path.getsize(os.path.join(config.usb_mount, f))
    elif target_distro == "trinity-rescue":
        folder_size_to_remove = disk_usage(os.path.join(usb_mount, "trk3")).used
        folder_size_to_remove += disk_usage(usb_mount + "/multibootusb/" + uninstall_distro_dir_name).used
    else:

        folder_size_to_remove = disk_usage(os.path.join(usb_mount, "multibootusb", uninstall_distro_dir_name)).used

    thrd = UninstallThread(target_distro, uninstall_distro_dir_name,
                           name="uninstall_progress")
    initial_usb_size = disk_usage(usb_mount).used
    thrd.start()
    config.status_text = "Uninstalling " + uninstall_distro_dir_name
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
