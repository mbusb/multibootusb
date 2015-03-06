#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     install_distro.py
# Purpose:  Module to install selected distro to selected USB disk.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
__author__ = 'sundar'
import os
import sys
import platform
import threading
import shutil
import subprocess
import gen_fun

import config
import iso


class InstallDistro():
    def __init__(self):
        from usb import USB
        self.usb = USB()

    def install(self):
        """
        Install selected ISO to USB disk.
        :return:
        """
        self.iso = iso.ISO(config.iso_link)
        install_dir = os.path.join(config.usb_mount, "multibootusb", self.iso.iso_basename())
        if not os.path.exists(os.path.join(config.usb_mount, "multibootusb")):
            print "Copying multibootusb directory to " + config.usb_mount
            shutil.copytree(gen_fun.resource_path(os.path.join("tools", "multibootusb")),
                            os.path.join(config.usb_mount, "multibootusb"))

        if not os.path.exists(install_dir):
            os.mkdir(install_dir)
            with open(os.path.join(install_dir, "multibootusb.cfg"), "w") as f:
                f.write(config.distro)
            with open(os.path.join(install_dir, "iso_file_list.cfg"), 'w') as f:
                for file_path in self.iso.iso_file_list():
                    f.write(file_path + "\n")
        print "Install dir is " + install_dir

        if config.distro == "opensuse":
            self.iso.iso_extract_file(install_dir, "boot")
            config.status_text = "Copying ISO..."
            if platform.system() == "Windows":
                subprocess.call(["xcopy", config.iso_link, config.usb_mount], shell=True)  # Have to use xcopy as python file copy is dead slow.
            elif platform.system() == "Linux":
                print config.iso_link, config.usb_mount
                shutil.copy(config.iso_link, config.usb_mount)
        elif config.distro == "Windows":
            print "Extracting iso to " + config.usb_mount
            self.iso.iso_extract_full(config.usb_mount)
        elif config.distro == "ipfire":
            self.iso.iso_extract_file(install_dir, "boot")
            self.iso.iso_extract_file(config.usb_mount, ".tlz")
        elif config.distro == "zenwalk":
            self.iso.iso_extract_file(install_dir, "kernel")
            self.iso.iso_extract_file(install_dir, "kernel")
            if platform.system() == "Windows":
                subprocess.call(["xcopy",config.iso_link, install_dir], shell=True)
            elif platform.system() == "Linux":
                shutil.copy(config.iso_link, install_dir)
            elif config.distro == "salix-live":
                self.iso.iso_extract_file(install_dir, "boot")
                config.status_text = "Copying ISO..."
                if platform.system() == "Windows":
                    subprocess.call("xcopy " + config.iso_link + " " + install_dir, shell=True)
                elif platform.system() == "Linux":
                    shutil.copy(config.iso_link, install_dir)
        elif config.distro == "generic":
            with open(os.path.join(install_dir, "generic.cfg"), "w") as f:
                f.write(os.path.join(self.iso.isolinux_bin_dir(), "generic") + ".bs")
            self.iso.iso_extract_full(config.usb_mount)
        else:
            self.iso.iso_extract_full(install_dir)

        if not config.persistence == 0:
            import persistence
            config.status_text = "Extracting persistance file..."
            home = gen_fun.mbusb_dir()
            persistence.persistence_extract(config.distro, str(config.persistence), home, install_dir)

    def install_progress(self):
        """
        Function to get the progress of install function as percentage.
        :return:
        """
        print "\n\ninstall_progress " + config.usb_disk + "\n\n"
        thrd = threading.Thread(target=self.install, name="install_progress")
        #thrd.daemon()
        install_size = self.usb.disk_usage(config.usb_mount).used / 1024
        thrd.start()
        while thrd.is_alive():
            current_size = self.usb.disk_usage(config.usb_mount).used / 1024
            diff_size = abs(int(current_size - install_size))
            config.percentage = round(float(1.0 * diff_size) / config.install_size * 100)
            #print config.percentage