#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     imager.py
# Purpose:  Module to write ISO image to selected USB disk.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
# WARNING : Any boot-able USB made using this module will destroy data stored on USB disk.

import os
import subprocess
import collections
import platform
from PyQt4 import QtGui
from PyQt4 import QtCore
from gui.ui_multibootusb import Ui_Dialog
import iso
from usb import USB
import config

if platform.system() == "Windows":
    import win32com.client

class Imager(QtGui.QDialog, Ui_Dialog):
    """
    Raw write to USB disk using dd.
    """

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.usb = USB()
        self.usb_disk = ""
        self.imager_iso_link = ""
        self.iso_size = ""
        self.process = QtCore.QProcess(self)

    def on_Imager_Browse_iso_Click(self):
        """
        Browse and choose an ISO.
        :return:
        """
        self.ui.lineEdit_3.clear()

        self.imager_iso_link = str(QtGui.QFileDialog.getOpenFileName(self, 'Select an iso...', "",  "ISO Files (*.iso)"))
        if self.imager_iso_link:
            if platform.system() == "Windows":
                if "/" in self.imager_iso_link:
                    self.imager_iso_link = self.imager_iso_link.strip().replace("/", "\\")
            self.ui.lineEdit_3.insert(str(self.imager_iso_link))
            self.iso_imager = iso.ISO(self.imager_iso_link)
            config.imager_iso_link = self.imager_iso_link
            self.add_iso_gui_label_text()
        else:
            print ("File not selected...")

    def add_iso_gui_label_text(self):
        """
        Simple function to add text label to GUI widgets.
        :return:
        """
        print "Testing ISO..."
        if self.iso_imager.is_bootable():
            self.ui.imager_bootable.setText("Bootable ISO :: Yes")
            print "ISO is bootable."
        else:
            self.ui.imager_bootable.setText("Bootable ISO :: No")
            print "ISO is not bootable."

        if os.path.exists(self.imager_iso_link):
            print "Path " + self.imager_iso_link + " is exist..."
            self.iso_size = str(os.path.getsize(self.imager_iso_link) / 1024 / 1024)
            self.ui.imager_iso_size.setText("ISO Size :: " + self.iso_size + " MB")
            print "ISO Size is " + self.iso_size + " MB"

    def imager_list_usb(self, partition=1):
        """
        Function to detect whole USB disk. It uses lsblk package on Linux.
        :param partition: What to return. By default partition is set.
        :return: USB disk/partition as list
        """
        disk = []
        if platform.system() == "Linux":
            output = subprocess.check_output("lsblk -i", shell=True)
            if not partition == 1:
                for line in output.splitlines():
                    line = line.split()
                    if str(line[2].strip()) == "1" and line[5].strip() == "disk":
                        #print line[0].strip()
                        disk.append(str("/dev/" + line[0].strip()))
            elif partition == 1:
                for line in output.splitlines():
                    line = line.split()
                    if str(line[2].strip()) == "1" and line[5].strip() == "part":
                        disk.append(str("/dev/" + line[0].strip()[2:]))
        else:
            if partition == 1 or not partition == 1:
                oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
                oDrives = oFS.Drives
                for drive in oDrives:
                    if drive.DriveType == 1 and drive.IsReady:
                        disk.append(drive)
        return disk

    def imager_usb_detail(self, usb_disk, partition=1):
        """
        Function to detect details of USB disk using lsblk
        :param usb_disk: path to usb disk
        :param partition: by default partition is set (but yet to code for it)
        :return: details of size, type and model as tuples
        """
        _ntuple_diskusage = collections.namedtuple('usage', 'total_size usb_type model')

        if platform.system() == "Linux":
            output = subprocess.check_output("lsblk -ib " + usb_disk, shell=True)
            for line in output.splitlines():
                line = line.split()
                if not partition == 1:
                    if str(line[2].strip()) == "1" and line[5].strip() == "disk":
                        total_size = line[3]
                        if not total_size:
                            total_size = "Unknown"
                        usb_type = "Removable"
                        model = subprocess.check_output("lsblk -in -f -o MODEL " + usb_disk, shell=True)
                        if not model:
                            model = "Unknown"
        else:
            try:
                selected_usb_part = str(usb_disk)
                oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
                d = oFS.GetDrive(oFS.GetDriveName(oFS.GetAbsolutePathName(selected_usb_part)))
                selected_usb_device = d.DriveLetter
                label = (d.VolumeName).strip()
                if not label.strip():
                    label = "No label."
                total_size = d.TotalSize
                usb_type = "Removable"
                model = label
            except:
                print "Error detecting USB details."

        return _ntuple_diskusage(total_size, usb_type, model)

    def get_usb_size(self, usb_disk):
        """
        Function to detect USB disk space. Useful but not used in multibootusb as of now.
        :param usb_disk: USB disk like "/dev/sdb"
        :return: Size of the disk as integer
        """
        if platform.system() == "Linux":
            cat_output = subprocess.check_output("cat /proc/partitions | grep  " + usb_disk[5:], shell=True)
            usb_size = int(cat_output.split()[2]) * 1024
            print usb_size
            return usb_size
        else:
            usb_size = self.usb.disk_usage(self.usb.get_usb(usb_disk).mount).total
            return usb_size

