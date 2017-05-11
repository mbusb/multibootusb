#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     qemu.py
# Purpose:  Module to boot ISO and USB disks using QEMU.
# Depends:  QEMU must be installed under Linux for availing this feature. For windows, QEMU package is shipped
#           along with executable file
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import subprocess
import platform
from PyQt5 import QtWidgets
from .gui.ui_multibootusb import Ui_MainWindow
from .gen import *
from . import config


class Qemu(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    ISO and USB booting using QEMU.
    """

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

    def on_Qemu_Boot_iso_Click(self):
        """
        Main function to boot a selected ISO.
        :return:
        """
#         if not self.ui.lineEdit_2.text():
        if not config.image_path:
            QtWidgets.QMessageBox.information(self, 'No ISO...', 'No ISO selected.\n\nPlease choose an ISO first.')
        else:
            qemu = self.check_qemu_exist()
            qemu_iso_link = config.image_path
            if not qemu:
                log("ERROR: ISO Boot: qemu not found!")
                QtWidgets.QMessageBox.information(self, 'No QEMU...', 'Please install qemu to use this feature.')
            else:
                ram = self.qemu_iso_ram()
                if ram:
                    ram = " -m " + ram
                else:
                    ram = ""

                cmd = qemu + ram + ' -boot d' + ' -cdrom "' + str(qemu_iso_link) + '"'
                try:
                    log("Executing ==> " + cmd)
                    subprocess.Popen(cmd, shell=True)
                except:
                    QtWidgets.QMessageBox.information(self, 'Error...', 'Error booting ISO\n'
                                                                    'Unable to start QEMU.')


    def on_Qemu_Boot_usb_Click(self):
        """
        Main function to boot a selected USB disk.
        :param usb_disk: Path to usb disk.
        :return:
        """
        qemu = self.check_qemu_exist()

        if not config.usb_disk:
            QtWidgets.QMessageBox.information(self, 'No disk...', 'No USB disk selected.\n\nPlease choose a disk first.')
        else:
            qemu = self.check_qemu_exist()
            if platform.system() == 'Linux' and config.usb_disk[-1].isdigit() is True:
                qemu_usb_disk = config.usb_disk[:-1]
            else:
                qemu_usb_disk = config.usb_disk

            if qemu is None:
                log("ERROR: USB Boot: qemu not found!")
                QtWidgets.QMessageBox.information(self, 'No QEMU...', 'Please install qemu to use this feature.')
            else:
                ram = self.qemu_usb_ram()
                if ram:
                    ram = " -m " + ram
                else:
                    ram = ""

                if platform.system() == "Windows":
                    disk_number = self.get_physical_disk_number(qemu_usb_disk)
                    parent_dir = os.getcwd()
                    os.chdir(resource_path(os.path.join("data", "tools", "qemu")))
                    cmd = quote(qemu) + ' -L . -boot c' + ram + ' -hda //./PhysicalDrive' + disk_number

                    try:
                        log("Executing ==>  " + cmd)
                        subprocess.Popen(cmd, shell=True)
                    except:
                        QtWidgets.QMessageBox.information(self, 'Error...', 'Error booting USB\nUnable to start QEMU.')
                    os.chdir(parent_dir)

                elif platform.system() == "Linux":
                    cmd = qemu + ' -hda "' + qemu_usb_disk + '"' + ram + ' -vga std'
                    try:
                        log('Executing ==> ' + cmd)
                        subprocess.Popen(cmd, shell=True)
                    except:
                        QtWidgets.QMessageBox.information(self, 'Error...', 'Error booting USB\n\nUnable to start QEMU.')

    def qemu_iso_ram(self):
        """
        Choose a ram size for ISO booting.
        :return: Ram size as string.
        """
        selected_ram = self.ui.combo_iso_boot_ram.currentText()
        log("QEMU: ISO RAM = " + selected_ram)

        if selected_ram == "Default":
            return None
        else:
            return selected_ram

    def qemu_usb_ram(self):
        """
        Choose a ram size for USB booting.
        :return: Ram size as string.
        """
        selected_ram = self.ui.combo_usb_boot_ram.currentText()
        log("QEMU: USB RAM = " + selected_ram)

        if selected_ram == "Default":
            return None
        else:
            return selected_ram

    @staticmethod
    def check_qemu_exist():
        """
        Check if QEMU is available on host system.
        :return: path to QEMU program or None otherwise.
        """
        if platform.system() == "Linux":
            if subprocess.call('which qemu-system-x86_64', shell=True) == 0:
                qemu = "qemu-system-x86_64"
            elif subprocess.call('which qemu', shell=True) == 0:
                qemu = "qemu"
            else:
                qemu = ""

        elif platform.system() == "Windows":
            qemu = resource_path(os.path.join("data", "tools", "qemu", "qemu-system-x86_64.exe"))
            log(qemu)

        if qemu:
            log("QEMU: using " + qemu)
        else:
            log("QEMU: ERROR: not found!")

        return qemu

    @staticmethod
    def get_physical_disk_number(usb_disk):
        """
        Get the physical disk number as detected ny Windows.
        :param usb_disk: USB disk (Like F:)
        :return: Disk number.
        """
        import wmi
        c = wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
                for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                    if logical_disk.Caption == usb_disk:
#                         log physical_disk.Caption
#                         log partition.Caption
#                         log logical_disk.Caption
                        log("Physical Device Number is " + partition.Caption[6:-14])
                        return str(partition.Caption[6:-14])
