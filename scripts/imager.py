#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     imager.py
# Purpose:  Module to write ISO image to selected USB disk. Uses dd as backend.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
# WARNING : Any boot-able USB made using this module will destroy data stored on USB disk.

import os
import subprocess
import collections
import platform
import signal
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from .gui.ui_multibootusb import Ui_Dialog
from .gen import *
from . import iso
from . import usb
from . import config
from . import progressbar

if platform.system() == "Windows":
    import win32com.client


def dd_linux():
    import time
    input = "if=" + config.imager_iso_link
    in_file_size = float(os.path.getsize(config.imager_iso_link))
    output = "of=" + config.imager_usb_disk
    os.system("umount " + config.imager_usb_disk + "1")
    command = ['dd', input, output, "bs=1M", "oflag=sync"]
    log("Executing ==> " + " ".join(command))
    dd_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    pbar = progressbar.ProgressBar(maxval=100).start()  # bar = progressbar.ProgressBar(redirect_stdout=True)
    while dd_process.poll() is None:
        time.sleep(1)  # If this time delay is not given, the Popen does not execute the actual command
        dd_process.send_signal(signal.SIGUSR1)
        dd_process.stderr.flush()
        while True:
            out_error = dd_process.stderr.readline().decode()
            if out_error:
                if 'bytes' in out_error:
                    copied = int(out_error.split(' ', 1)[0])
                    config.imager_percentage = round((float(copied) / float(in_file_size) * 100))
                    pbar.update(config.imager_percentage)
                    break

    if dd_process.poll() is not None:
        log("Executing ==> sync")
        os.system("sync")
        log("ISO has been written to USB disk...")
        return


def dd_win():

    windd = resource_path(os.path.join("data", "tools", "dd", "dd.exe"))
    if os.path.exists(resource_path(os.path.join("data", "tools", "dd", "dd.exe"))):
        log("dd exist")
    input = "if=" + config.imager_iso_link
    in_file_size = float(os.path.getsize(config.imager_iso_link) / 1024 / 1024)
    output = "of=\\\.\\" + config.imager_usb_disk
    command = [windd, input, output, "bs=1M", "--progress"]
    log("Executing ==> " + " ".join(command))
    dd_process = subprocess.Popen(command, universal_newlines=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                  shell=False)
    while dd_process.poll() is None:
        for line in iter(dd_process.stderr.readline, ''):
            line = line.strip()
            if 'error' in line.lower() or 'invalid' in line.lower():
                log("Error writing to disk...")
                break
            if line and line[-1] == 'M':
                copied = float(line.strip('M').replace(',', ''))
                config.imager_percentage = round((copied / float(in_file_size) * 100))

        log("ISO has been written to USB disk...")

        return


class Imager(QtWidgets.QDialog, Ui_Dialog):
    """
    Raw write to USB disk using dd.
    """

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def on_Imager_Browse_iso_Click(self):
        """
        Browse and choose an ISO.
        :return:
        """
        self.ui.lineEdit_3.clear()
        config.imager_iso_link = QtWidgets.QFileDialog.getOpenFileName(self, 'Select an iso...', "",  "ISO Files (*.iso)")[0]
        if config.imager_iso_link:
            if platform.system() == "Windows":
                if "/" in config.imager_iso_link:
                    config.imager_iso_link = config.imager_iso_link.strip().replace("/", "\\")
            self.ui.lineEdit_3.insert(str(config.imager_iso_link))
            self.add_iso_gui_label_text()
        else:
            log("File not selected...")

    def add_iso_gui_label_text(self):
        """
        Simple function to add text label to GUI widgets.
        :return:
        """
        log("Testing ISO...")
        self.ui.imager_bootable.setVisible(True)
        if iso.is_bootable(config.imager_iso_link) is True:
            self.ui.imager_bootable.setText("Bootable ISO: Yes")
            log("ISO is bootable.")
        else:
            self.ui.imager_bootable.setText("Bootable ISO: No")
            log("ISO is not bootable.")

        if os.path.exists(config.imager_iso_link):
            log("Path " + config.imager_iso_link + " exists...")
            self.iso_size = str(round(os.path.getsize(config.imager_iso_link) / 1024 / 1024))
            self.ui.imager_iso_size.setVisible(True)
            self.ui.imager_iso_size.setText("ISO Size: " + self.iso_size + " MB")
            log("ISO Size is " + self.iso_size + " MB")

    def onImagerComboChange(self):
        config.imager_usb_disk = str(self.ui.comboBox_2.currentText())
        if bool(config.imager_usb_disk):
            self.ui.imager_disk_label.setText(self.imager_usb_detail(config.imager_usb_disk, partition=0).usb_type)
            self.ui.imager_total_size.setText(usb.bytes2human(int(self.imager_usb_detail(config.imager_usb_disk, partition=0).total_size)))

            if platform.system() == "Linux":
                self.ui.label_imager_uuid.setText("Disk Model:")
                self.ui.imager_uuid.setText(str(self.imager_usb_detail(config.imager_usb_disk, partition=0).model))
            else:
                self.ui.imager_uuid.setText(self.imager_usb_detail(config.imager_usb_disk, partition=0).model)

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
                    if (line[2].strip()) == b'1' and (line[5].strip()) == b'disk':
                        disk.append(str("/dev/" + str(line[0].strip().decode())))
            elif partition == 1:
                for line in output.splitlines():
                    line = line.split()
                    if (line[2].strip()) == b'1' and line[5].strip() == b'part':
                        disk.append(str("/dev/" + str(line[0].strip()[2:])))
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
                    if line[2].strip() == b'1' and line[5].strip() == b'disk':
                        total_size = line[3]
                        if not total_size:
                            total_size = "Unknown"
                        usb_type = "Removable"
                        model = subprocess.check_output("lsblk -in -f -o MODEL " + usb_disk, shell=True).decode().strip()
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
                log("Error detecting USB details.")

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
            # log(usb_size)
            return usb_size
        else:
            usb_size = self.usb.disk_usage(self.usb.get_usb(usb_disk).mount).total
            return usb_size
