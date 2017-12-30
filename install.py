#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     install.py
# Purpose:  Script to install multibootusb from source on different linux distros. This also pulls in dependencies.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import subprocess

if not os.getuid() == 0:
    print("You must run this file with admin privilege.")
    print("Try sudo ./install.py")
    sys.exit(0)


class Install():

    def mbusb(self):
        try:
#             from PyQt5 import QtGui
            if subprocess.call("python3 setup.py install --record ./.install_files.txt", shell=True) == 0:
                    print("Installation finished.")
                    print("Find multibootusb under system menu or run from terminal  using the following command...")
                    print("\nmultibootusb\n")
                    print("You can uninstall multibootusb at any time using follwing command (with root/sudo previlage)")
                    print("\n./uninstall.sh\n")
        except:
            print("Installing missing package.")
            if self.supported_pac_manager() is not True:
                print("Unsupported package manager.")
                print("Please install parted, util-linux and python3-pyqt5/PyQt5, mtools and python3-dbus\n"
                      "Whatever the package name is applicable to your distro and rerun this script.")
                sys.exit(0)
            elif self.internet_on() is False:
                print("Unable to connect to internet.")
                print("Please install parted, util-linux and python3-pyqt5/PyQt5, pkexec, mtools and python3-dbus \n"
                      "Whatever the package name is applicable to your distro and rerun this script.")
                sys.exit(0)
            elif self.internet_on() is True:
                if self.install_dependency_package() is not True:
                    print("Error installing dependency packages.")
                else:
                    if subprocess.call("python3 setup.py install --record ./.install_files.txt", shell=True) == 0:
                        print("Installation finished.")
                        print("Find multibootusb under system menu or run from terminal  using the following command...")
                        print("\nmultibootusb\n")
                        print("You can uninstall multibootusb at any time using follwing command (with root/sudo previlage)")
                        print("\nsudo ./uninstall.sh\n")

    @staticmethod
    def internet_on():
        try:
            ret = urllib.request.urlopen('https://www.google.com', timeout=1)
            print("Interconnection exist.")
            result = True

        except urllib.error.URLError:
            print("Interconnection does not exist.")
            result = False

        return result

    @staticmethod
    def supported_pac_manager():
        pac_managers = ["pacman", "yum", "apt-get", "zypper", "urpmi"]
        result = "0"
        for pac_man in pac_managers:
            if subprocess.call("which " + pac_man, shell=True) == 0:
                result = "1"
                return True

        if not result == "1":
            return False


    @staticmethod
    def install_dependency_package():
        if subprocess.call("which pacman", shell=True) == 0:
            subprocess.call("pacman -Sy --noconfirm", shell=True)
            # Thank you Neitsab for "--needed"  argument.
            if subprocess.call("pacman -S --needed --noconfirm p7zip python-pyqt5 mtools python3-six parted util-linux python-dbus") == 0:
                result = True
        elif subprocess.call("which yum", shell=True) == 0:
            subprocess.call("yum check-update", shell=True)
            if subprocess.call("dnf install mtools python3-PyQt5 util-linux python3-six parted p7zip p7zip-plugins python3-pyudev python3-dbus -y", shell=True) == 0:
                result = True
        elif subprocess.call("which apt-get", shell=True) == 0:
            subprocess.call("apt-get -q update", shell=True)
            if subprocess.call("apt-get -q -y install python3-pyqt5 p7zip-full parted util-linux python3-pyudev mtools python3-dbus", shell=True) == 0:
                result = True
        elif subprocess.call("which zypper", shell=True) == 0:
            subprocess.call("zypper refresh", shell=True)
            if subprocess.call("zypper install -y mtools python3-qt5 p7zip python3-pyudev python3-six util-linux parted", shell=True) == 0:
                result = True
        elif subprocess.call("which urpmi", shell=True) == 0:
            subprocess.call("urpmi.update -a", shell=True)
            if subprocess.call("urpmi install -auto mtools util-linux p7zip python3-pyudev python3-six parted python3-qt5", shell=True) == 0:
                result = True

        return bool(result)

install = Install()

install.mbusb()
