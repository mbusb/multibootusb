#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     imager.py
# Purpose:  Module to write ISO image to selected USB disk. Uses dd as backend.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
# WARNING : Any boot-able USB made using this module will destroy data stored on USB disk.

import collections
import io
import os
import platform
import signal
import time
import subprocess
import traceback

from PyQt5 import QtWidgets
from .gui.ui_multibootusb import Ui_MainWindow
from .gen import *
from . import config
from . import iso
from . import osdriver
from . import progressbar
from . import osdriver
from . import usb


if platform.system() == "Windows":
    import win32com.client

def dd_iso_image(dd_progress_thread):
    try:
        _dd_iso_image(dd_progress_thread)
    except:
        # config.imager_return = False
        o = io.StringIO()
        traceback.print_exc(None, o)
        log(o.getvalue())
        dd_progress_thread.set_error(o.getvalue())

def _dd_iso_image(dd_progress_thread):
    pbar = progressbar.ProgressBar(
            maxval=100,
            widgets=[
                ' ',
                progressbar.widgets.Bar(marker='=', left='[', right=']'),
                ' ',
                progressbar.widgets.Percentage()
            ]
    ).start()


    def gui_update(percentage):
        config.imager_percentage = percentage
        pbar.update(percentage)

    def status_update(text):
        config.status_text = text

    mounted_partitions = osdriver.find_mounted_partitions_on(config.usb_disk)
    really_unmounted = []
    try:
        for x in mounted_partitions:
            partition_dev, mount_point = x[:2]
            c = usb.UnmountedContext(partition_dev, config.update_usb_mount)
            c.__enter__()
            really_unmounted.append((c, partition_dev))
        error = osdriver.dd_iso_image(
            config.image_path, config.usb_disk, gui_update, status_update)
        if error:
            dd_progress_thread.set_error(error)
            log('Error writing iso image...')
            # config.imager_return = False
        else:
            log('ISO has been written to USB disk...')
            # config.imager_return = True
    finally:
        for c, partition_dev in really_unmounted:
                c.__exit__(None, None, None)


class Imager(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Raw write to USB disk using dd.
    """

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


    def add_iso_gui_label_text(self):
        """
        Simple function to add text label to GUI widgets.
        :return:
        """
        log("Testing ISO...")
        self.ui.imager_bootable.setVisible(True)
        if iso.is_bootable(config.image_path) is True:
            self.ui.imager_bootable.setText("Bootable ISO: Yes")
            log("ISO is bootable.")
        else:
            self.ui.imager_bootable.setText("Bootable ISO: No")
            log("ISO is not bootable.")

        if os.path.exists(config.image_path):
            log("Path " + config.image_path + " exists...")
            self.iso_size = str(round(os.path.getsize(config.image_path) / 1024 / 1024))
            self.ui.imager_iso_size.setVisible(True)
            self.ui.imager_iso_size.setText("ISO Size: " + self.iso_size + " MB")
            log("ISO Size is " + self.iso_size + " MB")

    @staticmethod
    def imager_list_usb(partition=1):
        """
        Function to detect whole USB disk. It uses lsblk package on Linux.
        :param partition: What to return. By default partition is set.
        :return: USB disk/partition as list
        """
        disk = []
        if platform.system() == "Linux":
            output = subprocess.check_output("lsblk -i", shell=True)
            if partition != 1:
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
            oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
            oDrives = oFS.Drives
            for drive in oDrives:
                if drive.DriveType == 1 and drive.IsReady:
                    disk.append(drive)
        return disk

    @staticmethod
    def imager_usb_detail(usb_disk, partition=1):
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
                if partition != 1:
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
#                 selected_usb_device = d.DriveLetter
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
