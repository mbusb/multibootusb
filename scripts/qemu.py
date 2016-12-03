#!/usr/bin/env python
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
from .admin import adminCmd
from PyQt5 import QtWidgets
from .gui.ui_multibootusb import Ui_Dialog
from .gen import *


class Qemu(QtWidgets.QDialog, Ui_Dialog):
    """
    ISO and USB booting using QEMU.
    """
    def on_Qemu_Browse_iso_Click(self):
        """
        Browse and choose an ISO.
        :return:
        """
        self.ui.lineEdit_2.clear()

        qemu = self.check_qemu_exist()

        if not qemu is None:
        
            qemu_iso_link = QtWidgets.QFileDialog.getOpenFileName(self, 'Select an iso...', "",  "ISO Files (*.iso)")[0]
        else:
            print("QEMU does not exist.\nPlease install qemu package to avail this feature.")
            QtWidgets.QMessageBox.information(self, 'No QEMU...', 'Please install qemu package to avail this feature.')
            qemu_iso_link = None

        if not qemu_iso_link is None:
            self.ui.lineEdit_2.insert(qemu_iso_link)
        else:
            print ("File not selected.")
            
    def on_Qemu_Boot_iso_Click(self):
        """
        Main function to boot a selected ISO.
        :return:
        """
        if not self.ui.lineEdit_2.text():
            QtWidgets.QMessageBox.information(self, 'No ISO...', 'No ISO selected.\n\nPlease choose an iso and click Boot ISO.')
        else:
            qemu = self.check_qemu_exist()
            qemu_iso_link = str(self.ui.lineEdit_2.text())
            if qemu is None:
                print("QEMU does not exist.\nPlease install qemu package to avail this feature.")
                QtWidgets.QMessageBox.information(self, 'No QEMU...', 'Please install qemu to avail this feature.')
            else:
                ram = self.qemu_iso_ram()
                if not ram is None:
                    self.ui.lineEdit_2.clear()
                    if platform.system() == "Windows":
                        try:
                            print("Executing ==>  " + qemu + " -cdrom " + str(qemu_iso_link) + " -boot d -m " + ram)
                            subprocess.Popen(qemu + " -cdrom " + str(qemu_iso_link) + " -boot d -m " + ram, shell=True)
                        except:
                            QtWidgets.QMessageBox.information(self, 'Error...', 'Unable to start QEMU.')
                    else:
                        print(qemu + ' -m ' + ram + ' -cdrom ' + str(qemu_iso_link) + ' -boot d')
                        try:
                            print("Executing ==>  " + qemu + " -cdrom " + str(qemu_iso_link) + " -boot d -m " + ram)
                            subprocess.Popen(qemu + " -cdrom " + str(qemu_iso_link) + " -boot d -m " + ram, shell=True)
                        except:
                            QtWidgets.QMessageBox.information(self, 'Error...', 'Error booting ISO\n'
                                                                            'Unable to start QEMU.')
                else:
                    QtWidgets.QMessageBox.information(self, 'No ram...', 'No ram selected.\n\nPlease choose any ram value and click Boot ISO.')


    def on_Qemu_Boot_usb_Click(self, usb_disk):
        """
        Main function to boot a selected USB disk.
        :param usb_disk: Path to usb disk.
        :return:
        """
        qemu = self.check_qemu_exist()

        if qemu is None:
            print("QEMU does not exist.\nPlease install qemu package to avail this feature.")
            QtWidgets.QMessageBox.information(self, 'No QEMU...', 'Please install qemu to avail this feature.')
        else:
            ram = self.qemu_usb_ram()
            if ram is None:
                QtWidgets.QMessageBox.information(self, 'No ram...', 'No ram selected.\n\nPlease choose any ram value and click Boot USB.')
            else:
                if platform.system() == "Windows":
                    disk_number = self.get_physical_disk_number(usb_disk)
                    parent_dir = os.getcwd()
                    os.chdir(resource_path(os.path.join("data", "tools", "qemu")))
                    try:
                        print("Executing ==>  " + qemu + " -L . -boot c -m " + ram + " -hda //./PhysicalDrive" + disk_number)
                        subprocess.Popen("qemu-system-x86_64.exe -L . -boot c -m "  + ram + " -hda //./PhysicalDrive" + disk_number, shell=True)
                    except:
                        QtWidgets.QMessageBox.information(self, 'Error...', 'Error booting USB\n'
                                                                            'Unable to start QEMU.')
                    os.chdir(parent_dir)
                elif platform.system() == "Linux":
                    try:
                        qemu_cmd = qemu + ' -hda ' + usb_disk[:-1] + ' -m ' + ram + ' -vga std'
                        print('Executing ==>', qemu_cmd)
                        # adminCmd([qemu, '-hda', usb_disk[:-1], '-m', ram, '-vga std'], gui=True)
                        subprocess.Popen(qemu_cmd, shell=True)
                        # adminCmd(qemu_cmd, gui=True)
                    except:
                        QtWidgets.QMessageBox.information(self, 'Error...', 'Error booting USB\n\nUnable to start QEMU.')

    def qemu_iso_ram(self):
        """
        Choose a ram size for ISO booting.
        :return: Ram size as string.
        """
        if self.ui.ram_iso_256.isChecked():
            return str(256)
        elif self.ui.ram_iso_512.isChecked():
            return str(512)
        elif self.ui.ram_iso_768.isChecked():
            return str(768)
        elif self.ui.ram_iso_1024.isChecked():
            return str(1024)
        elif self.ui.ram_iso_2048.isChecked():
            return str(2047)
        else:
            return None

    def qemu_usb_ram(self):
        """
        Choose a ram size for USB booting.
        :return: Ram size as string.
        """
        if self.ui.ram_usb_256.isChecked():
            return str(256)
        if self.ui.ram_usb_512.isChecked():
            return str(512)
        if self.ui.ram_usb_768.isChecked():
            return str(768)
        if self.ui.ram_usb_1024.isChecked():
            return str(1024)
        if self.ui.ram_usb_2048.isChecked():
            return str(2047)
        else:
            return None
            
    def check_qemu_exist(self):
        """
        Check if QEMU is available on host system.
        :return: path to QEMU program or None otherwise.
        """
        if platform.system() == "Linux":
            if subprocess.call('which qemu-system-x86_64', shell=True) == 0:
                print("qemu-system-x86_64 exists...")
                qemu = "qemu-system-x86_64"
            elif subprocess.call('which qemu', shell=True) == 0:
                print("qemu exists")
                qemu = "qemu"
            else:
                qemu = None

            if qemu:
                return qemu
            else:
                return None
        elif platform.system() == "Windows":
            print(resource_path(os.path.join("data", "tools", "qemu", "qemu-system-x86_64.exe")))
            return resource_path(os.path.join("data", "tools", "qemu", "qemu-system-x86_64.exe"))


    def get_physical_disk_number(self, usb_disk):
        """
        Get the physical disk number as detected ny Windows.
        :param usb_disk: USB disk (Like F:)
        :return: Disk number.
        """
        import wmi
        c = wmi.WMI ()
        for physical_disk in c.Win32_DiskDrive ():
            for partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
                for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
                    if logical_disk.Caption == usb_disk:
                        """
                        print physical_disk.Caption
                        print partition.Caption
                        print logical_disk.Caption
                        """
                        print("Physical Device Number is " + partition.Caption[6:-14])
                        return str(partition.Caption[6:-14])
