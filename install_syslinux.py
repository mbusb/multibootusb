#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string, re, sys, os, var, subprocess
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

    def install_syslinux_distro_dir(self, syslinux_dir_path, usb_device, mbr_bin, usb_mount, default_install):
        self.ui.status.setText("Installing syslinux on distro directory...")

        if default_install == 1:
            syslinux_dir_path = "multibootusb"
            var.syslinux_version = var.defautl_syslinux_version

        if var.usb_file_system == "vfat" or var.usb_file_system == "ntfs" or var.usb_file_system == "FAT32":
            if sys.platform.startswith("linux"):
                var.distro_sys_install_bs = os.path.join(os.path.dirname(var.distro_isolinux_bin_path),
                                                         var.distro) + '.bs'
                print var.distro_sys_install_bs
                if var.password == "":
                    if subprocess.call(var.syslinux_version + ' -i -d ' + syslinux_dir_path + ' ' + usb_device,
                                       shell=True) == 0:
                        print "Syslinux install on distro directory was successful..."
                        sys_ins_succ = "yes"
                    else:
                        print "Syslinux install on distro directory was fail..."
                        sys_ins_succ = "no"

                elif not var.password == "":
                    if subprocess.call(
                                                                                    'echo ' + var.password + ' | sudo -S ' + var.syslinux_version + ' -i -d ' + syslinux_dir_path + ' ' + usb_device,
                                                                                    shell=True) == 0:
                        print "Syslinux install on distro directory was successful..."
                        sys_ins_succ = "yes"
                    else:
                        print "Syslinux install on distro directory was fail..."
                        sys_ins_succ = "no"

                if sys_ins_succ == "yes" and default_install == 0:
                    if subprocess.call('dd if=' + usb_device + ' ' + 'of=' + var.distro_sys_install_bs + ' count=1',
                                       shell=True) == 0:
                        print "Boot sector has been successfully copied..."

                if sys.platform.startswith("linux") and default_install == 1:
                    if var.password == "":
                        if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + usb_device[:-1],
                                           shell=True) == 0:
                            print "mbr install was success..."
                    elif not var.password == "":
                        if subprocess.call(
                                                                        'echo ' + var.password + ' | sudo -S dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + usb_device[
                                                                                                                                                                      :-1],
                                                                        shell=True) == 0:
                            print "mbr install was success..."
                            if var.sys_tab == "yes":
                                QtGui.QMessageBox.information(self, 'Installation Completed...',
                                                              'Syslinux has been successfully installed on' + str(
                                                                  usb_device))
                                #else:
