#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     iso.py
# Purpose:  Module to manupulate iso image
# Authors:  Sundar
# Depends:  isodump.py is authored by Johni Lee for MultiBootUSB
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import re
import shutil
import threading

from usb import USB
import config


class UnInstall():
    """
    Main class related to uninstalling distro.
    """
    def __init__(self):
        self.usb = USB()

    def uninstall_distro(self):
        """
        Uninstall selected distro from selected USB disk.
        :return:
        """
        print os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "multibootusb.cfg")
        if os.path.exists(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "multibootusb.cfg")):
            with open(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "multibootusb.cfg"), "r") as multibootusb_cfg:
                distro = multibootusb_cfg.read().replace('\n', '')
                print "Uninstall distro type is " + distro
        else:
            distro = ""

        if os.path.exists(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "iso_file_list.cfg")):
            with open(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "iso_file_list.cfg"), "r") as f:
                iso_file_list = f.readlines()
                #print iso_file_list

        for path, subdirs, files in os.walk(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro)):
            for name in files:
                if name.endswith('ldlinux.sys'):
                    os.chmod(os.path.join(path, name), 0777)
                    os.unlink(os.path.join(path, name))
        if distro == "opensuse":
            if os.path.exists(os.path.join(config.usb_mount, config.uninstall_distro + ".iso")):
                os.remove(os.path.join(config.usb_mount, config.uninstall_distro + ".iso"))
        elif distro == "windows":
            windows_files = ["SOURCES", "BOOT", "[BOOT]", "EFI", "SUPPORT", "UPGRADE", "AUTORUN.INF", "BOOTMGR", "README.TXT", "SETUP.EXE"]
            for f in windows_files:
                if os.path.isfile(os.path.join(config.usb_mount, f)):
                    os.remove(os.path.join(config.usb_mount, f))
                elif os.path.isdir(os.path.join(config.usb_mount, f)):
                    shutil.rmtree(os.path.join(config.usb_mount, f))
        if distro == "ipfire":
            files = os.listdir(config.usb_mount)
            for f in files:
                if f.endswith('.tlz'):
                    os.remove(os.path.join(config.usb_mount, f))
            if os.path.exists(os.path.join(config.usb_mount, "distro.img")):
                os.remove(os.path.join(config.usb_mount, "distro.img"))
        elif distro == "trinity-rescue":
            shutil.rmtree(os.path.join(config.usb_mount, "trk3"))
        elif distro == "generic":
            for f in iso_file_list:
                if os.path.isfile(os.path.join(config.usb_mount, f.replace('\n', '').strip("/"))):
                    os.remove(os.path.join(config.usb_mount, f.replace('\n', '').strip("/")))
                elif os.path.isdir(os.path.join(config.usb_mount, f.replace('\n', '').strip("/"))):
                    shutil.rmtree(os.path.join(config.usb_mount, f.replace('\n', '').strip("/")))
            if os.path.exists(os.path.join(config.usb_mount, "ldlinux.sys")):
                os.chmod(os.path.join(config.usb_mount, "ldlinux.sys"), 0777)
                os.unlink(os.path.join(config.usb_mount, "ldlinux.sys"))
            with open(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "generic.cfg"), "r") as generic_cfg:
                generic = generic_cfg.read().replace('\n', '')
            os.remove(os.path.join(config.usb_mount, generic.strip("/")))

        if os.path.exists(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro)):
            shutil.rmtree(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro))

    def update_sys_cfg_file(self):
        """
        Main function to remove uninstall distro specific operations.
        :return:
        """
        sys_cfg_file = os.path.join(config.usb_mount,  "multibootusb",  "syslinux.cfg")
        if not os.path.exists(sys_cfg_file):
            print "syslinux.cfg file not found for updating changes."
        else:
            print "Updating syslinux.cfg file..."
            string = open(sys_cfg_file).read()
            string = re.sub(r'#start ' + config.uninstall_distro + '.*?' + '#end ' + config.uninstall_distro + '\s*', '', string, flags=re.DOTALL)
            config_file = open(sys_cfg_file, "w")
            config_file.write(string)
            config_file.close()

    def uninstall_progress(self):
        """
        Calculate uninstall progress percentage.
        :return:
        """
        if os.path.exists(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "multibootusb.cfg")):
            with open(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro, "multibootusb.cfg"), "r") as multibootusb_cfg:
                distro = multibootusb_cfg.read().replace('\n', '')
        else:
            distro = ""
        print "Installed distro type is " + distro

        if distro == "opensuse":
            if os.path.exists(os.path.join(config.usb_mount, config.uninstall_distro) + ".iso"):
                folder_size_to_remove = os.path.getsize(os.path.join(config.usb_mount, config.uninstall_distro) + ".iso")
            else:
                folder_size_to_remove = 0
            folder_size_to_remove += self.usb.disk_usage(str(config.usb_mount) + "/multibootusb/" + config.uninstall_distro).used
        elif distro == "windows" or distro == "Windows":
            folder_size_to_remove = self.usb.disk_usage(str(config.usb_mount) + "/SOURCES").used
        elif distro == "ipfire":
            folder_size_to_remove = self.usb.disk_usage(str(config.usb_mount) + "/multibootusb/" + config.uninstall_distro).used
            files = os.listdir(os.path.join(str(config.usb_mount)))
            for f in files:
                if f.endswith('.tlz'):
                    folder_size_to_remove += os.path.getsize(os.path.join(config.usb_mount, f))
        elif distro == "trinity-rescue":
            folder_size_to_remove = self.usb.disk_usage(os.path.join(config.usb_mount, "trk3")).used
            folder_size_to_remove += self.usb.disk_usage(config.usb_mount + "/multibootusb/" + config.uninstall_distro).used
        else:

            folder_size_to_remove = self.usb.disk_usage(os.path.join(config.usb_mount, "multibootusb", config.uninstall_distro)).used

        thrd = threading.Thread(target=self.uninstall_distro, name="uninstall_progress")
        initial_usb_size = self.usb.disk_usage(config.usb_mount).used
        thrd.start()
        while thrd.is_alive():
            config.status_text = "Uninstalling " + config.uninstall_distro
            current_size = self.usb.disk_usage(config.usb_mount).used
            diff_size = int(initial_usb_size - current_size)
            config.percentage = round(float(diff_size)/folder_size_to_remove*100)

        if not thrd.is_alive():
            config.persistence = 0
            config.status_text = ""
            self.update_sys_cfg_file()
            print ("Distro directory has been removed successfully...")