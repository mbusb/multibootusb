#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string, re, sys, os, var, subprocess, platform
from PyQt4 import QtGui
from multibootusb_ui import Ui_Dialog


class AppGui(QtGui.QDialog, Ui_Dialog):
    def detect_distro_isobin(self, install_dir):
        # Function to detect isolinux.bin path
        print install_dir
        if sys.platform.startswith("linux") or platform.system() == "Windows":
            for path, subdirs, files in os.walk(install_dir):
                for name in files:
                    if name.endswith('isolinux.bin'):
                        #return name
                        return os.path.join(path, name)

    def strings(self, filename, min=4):
        # function to extract printable character from binary file.
        with open(filename, "rb") as f:
            result = ""
            for c in f.read():
                if c in string.printable:
                    result += c
                    continue
                if len(result) >= min:
                    yield result
                result = ""

    def distro_syslinux_version(self, distro_bin):
        # Function to detect version syslinux version shipped by distro developers.
        version = ["3", "4", "5", "6"]
        if not distro_bin == None:
            sl = list(self.strings(distro_bin))
            for strin in sl:
                if re.search(r'isolinux ', strin, re.I):
                    #print strin
                    for number in version:
                        if re.search(r'isolinux ' + number, strin, re.I):
                            print "Found syslinux version " + number
                            return number
        """
        elif distro_bin == "":
            print "Distro does not use syslinux"
            return None
        """

    def install_syslinux_distro_dir(self, distro_syslinux_dir_path, usb_device, mbr_bin, usb_mount, syslinux_version, syslinux_options):
        print distro_syslinux_dir_path
        if var.usb_file_system == "vfat" or var.usb_file_system == "ntfs" or var.usb_file_system == "FAT32":
            if sys.platform.startswith("linux"):
                if distro_syslinux_dir_path == "multibootusb":
                    if var.password == "":
                        syslinux_version = syslinux_version + ""
                    else:
                        syslinux_version = 'echo ' + var.password + ' | sudo -S ' + syslinux_version
                    if subprocess.call(syslinux_version + syslinux_options + distro_syslinux_dir_path + ' ' + usb_device, shell=True) == 0:
                        print "Syslinux install was successful..."
                        if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + usb_device[:-1], shell=True) == 0:
                            print "mbr install was success..."
                            if var.sys_tab == "yes":
                                QtGui.QMessageBox.information(self, 'Installation Completed...',
                                                                'Syslinux has been successfully installed on' + str(
                                                                    usb_device))

                elif not var.distro_syslinux_dir_path == "multibootusb":
                    #var.syslinux_version = var.distro_syslinux_version
                    if var.password == "":
                        syslinux_version = syslinux_version + ""
                    else:
                        syslinux_version = 'echo ' + var.password + ' | sudo -S ' + syslinux_version
                    var.distro_sys_install_bs = os.path.join(os.path.dirname(var.distro_isolinux_bin_path), var.distro) + '.bs'
                    if subprocess.call(syslinux_version + syslinux_options + distro_syslinux_dir_path + ' ' + usb_device, shell=True) == 0:
                        print "Syslinux install was successful on distro directory..."
                        if subprocess.call('dd if=' + usb_device + ' ' + 'of=' + var.distro_sys_install_bs + ' count=1', shell=True) == 0:
                            print "Boot sector has been successfully copied..."
                        else:
                            print "Boot sector copy failed..."
                    else:
                            print "Syslinux install on distro directory failed..."
            # Syslinux install under Linux ends here.

            else:
                if distro_syslinux_dir_path == "multibootusb":
                    syslinux_options = " -maf -d "
                    print syslinux_version + syslinux_options + distro_syslinux_dir_path + ' ' + usb_device + ":"
                    if subprocess.call(syslinux_version + syslinux_options + distro_syslinux_dir_path + ' ' + usb_device + ":", shell=True) == 0:
                        print "Syslinux install was successful..."
                        if var.sys_tab == "yes":
                                QtGui.QMessageBox.information(self, 'Installation Completed...',
                                                                'Syslinux has been successfully installed on' + str(
                                                                    usb_device + ":"))
                    else:
                        print "Syslinux install was fail..."
                else:
                    var.distro_sys_install_bs = os.path.join(os.path.dirname(var.distro_isolinux_bin_path), var.distro) + '.bs'
                    distro_syslinux_dir_path = "/" + distro_syslinux_dir_path.replace("\\", "/")
                    print syslinux_version + syslinux_options + distro_syslinux_dir_path + ' ' + usb_device + ": " + var.distro_sys_install_bs
                    if subprocess.call(syslinux_version + syslinux_options + distro_syslinux_dir_path + ' ' + usb_device + ": " + var.distro_sys_install_bs, shell=True) == 0:
                        var.distro_sys_install_bs = "/" + os.path.join(os.path.dirname(var.distro_isolinux_bin_path), var.distro) + '.bs'
                        print "Syslinux install was successful on distro directory..."
                    else:
                        print "Syslinux install on distro directory failed..."