#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'sundar'
import os
import sys
import urllib2
import subprocess


if not os.getuid() == 0:
    print "You must run this file with admin privilege."
    print "Try sudo ./install.py"
    sys.exit(1)


class Install():

    def mbusb(self):
        try:
            from PyQt4 import QtGui
            if subprocess.call("python2.7 setup.py install --record ./.install_files.txt", shell=True) == 0:
                    print "Installation finished."
                    print "Find multibootusb under system menu or run from terminal  using the following command..."
                    print "\nmultibootusb\n"
                    print "You can uninstall multibootusb at any time using follwing command (with root/sudo previlage)"
                    print "\n./uninstall.sh\n"
        except:
            print "Installing missing package."
            if self.supported_pac_manager() is not None:
                print "Unsupported package manager."
                print "Please install python2-pyqt4/PyQt4 or python-qt4 \nwhichever is applicable to your distro and rerun this script."
            elif self.internet_on() is False:
                print "Unable to connect to internet."
                print "Please install python2-pyqt4/PyQt4 or python-qt4 \nwhichever is applicable to your distro and rerun this script."
            elif self.internet_on() is True:
                if subprocess.call("python2.7 setup.py install --record ./.install_files.txt", shell=True) == 0:
                    print "Installation finished."
                    print "Find multibootusb under system menu or run from terminal  using the following command..."
                    print "\nmultibootusb\n"
                    print "You can uninstall multibootusb at any time using follwing command (with root/sudo previlage)"
                    print "\n./uninstall.sh\n"

    def internet_on(self):
        try:
            ret = urllib2.urlopen('https://www.google.com', timeout=1)
            result = True

        except urllib2.URLError:
            result = False

        return result


    def supported_pac_manager(self):
        pac_managers = ["pacman", "yum", "apt-get", "zypper", "urpmi"]
        for pac_man in pac_managers:
            if subprocess.call("which " + pac_man, shell=True) == 0:
                return True

        return False

    def install_dependency_package(self):
        if subprocess.call("which pacman", shell=True) == 0:
            package = "python2-pyqt4"
            subprocess.call("pacman -Sy --noconfirm")
            if subprocess.call("pacman -S --needed --noconfirm python2-pyqt4") == 0:  #  # Thank you Neitsab for "--needed"  argument.
                result = True
        elif subprocess.call("which yum", shell=True) == 0:
            package = "PyQt4"
            subprocess.call("yum check-update")
            if subprocess.call("yum install PyQt4 -y") == 0:
                result = True
        elif subprocess.call("which apt-get", shell=True) == 0:
            package = "python-qt4"
            subprocess.call("apt-get -q update")
            if subprocess.call("apt-get -q -y install python-qt4") == 0:
                result = True
        elif subprocess.call("which zypper", shell=True) == 0:
            package = "python-qt4"
            subprocess.call("zypper refresh")
            if subprocess.call("zypper install -y python-qt4") == 0:
                result = True
        elif subprocess.call("which urpmi", shell=True) == 0:
            package = "python-qt4"
            subprocess.call("urpmi.update -a")
            if subprocess.call("urpmi install -auto python-qt4") == 0:
                result = True

        if result is not True:
            return False
        else:
            result

install = Install()

install.mbusb()
