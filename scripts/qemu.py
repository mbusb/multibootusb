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
import platform
import subprocess
import traceback
from PyQt5 import QtWidgets
from .gui.ui_multibootusb import Ui_MainWindow
from .gen import *
from . import config
from . import usb

class Qemu(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    ISO and USB booting using QEMU.
    """

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

    def run_qemu(self, ram_size, qemu_more_params,
                 qemu_not_found_log_msg,
                 exec_error_title, exec_error_msg):

        qemu = self.find_qemu()
        if not qemu:
            log(qemu_not_found_log_msg)
            QtWidgets.QMessageBox.information(
                self, 'No QEMU...',
                'Please install qemu to use this feature.')
            return
        options = [] # '-bios', 'OVMF.fd']
        if ram_size:
            options.extend(['-m', ram_size])
        if getattr(config, 'qemu_use_haxm', False):
            options.extend(['-accel', 'hax'])
        bios = getattr(config, 'qemu_bios', None)
        if bios:
            options.extend(['-bios', bios])
        if platform.system()=='Linux' and getattr(config,'use_kvm', True):
            options.append('-enable-kvm')

        cmd = [qemu] + options + qemu_more_params
        try:
            new_wd = os.path.split(qemu)[0]
            if new_wd:
                old_wd = os.getcwd()
                os.chdir(new_wd)
            try:
                with usb.UnmountedContext(config.usb_disk,
                                        config.update_usb_mount):
                    log("Executing ==> %s" % cmd)
                    out = subprocess.check_output(cmd)
                    if out:
                        log('%s => %s' % (cmd, out))
            finally:
                if new_wd:
                    os.chdir(old_wd)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            traceback.print_exc()
            QtWidgets.QMessageBox.information(
                self, exec_error_title, exec_error_msg)


    def on_Qemu_Boot_iso_Click(self):
        """
        Main function to boot a selected ISO.
        :return:
        """
        if not config.image_path:
            QtWidgets.QMessageBox.information(
                self, 'No ISO...',
                'No ISO selected.\n\nPlease choose an ISO first.')
            return
        self.run_qemu(
            self.qemu_iso_ram(), ['-boot', 'd','-cdrom', config.image_path],
            "ERROR: ISO Boot: qemu not found!",
            'Error...', 'Error booting ISO\nUnable to start QEMU.')

    def on_Qemu_Boot_usb_Click(self):
        """
        Main function to boot a selected USB disk.
        :param usb_disk: Path to usb disk.
        :return:
        """
        if not config.usb_disk:
            QtWidgets.QMessageBox.information(
                self, 'No disk...',
                'No USB disk selected.\n\nPlease choose a disk first.')
            return
        if platform.system() == "Windows":
            disk_number = get_physical_disk_number(config.usb_disk)
            qemu_more_params = ['-L', '.', '-boot', 'c', '-hda', 
                                '//./PhysicalDrive' + str(disk_number)]
        elif platform.system() == "Linux":
            qemu_more_params = ['-hda', config.usb_disk.rstrip('0123456789'),
                                '-vga', 'std']
        else:
            assert False, "Unknown platform '%s'" % platform.system()
        self.run_qemu(self.qemu_usb_ram(), qemu_more_params,
                      "ERROR: USB Boot: qemu not found!",
                      'Error...', 'Error booting USB\nUnable to start QEMU.')

    def qemu_ram_size(self, combo, log_msg):
        selected_ram = combo.currentText()
        log(log_msg % selected_ram)
        return selected_ram != 'Default' and selected_ram or None

    def qemu_iso_ram(self):
        """
        Choose a ram size for ISO booting.
        :return: Ram size as string.
        """
        return self.qemu_ram_size(self.ui.combo_iso_boot_ram,
                                  "QEMU: ISO RAM = %s")
    def qemu_usb_ram(self):
        """
        Choose a ram size for USB booting.
        :return: Ram size as string.
        """
        return self.qemu_ram_size(self.ui.combo_usb_boot_ram,
                                  "QEMU: USB RAM = %s")

    @staticmethod
    def find_qemu():
        """
        Check if QEMU is available on host system and return path of the binary
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
            qemu = find_qemu_exe()

        if qemu:
            log("QEMU: using " + qemu)
        else:
            log("QEMU: ERROR: not found!")

        return qemu

def find_qemu_exe():
    exe_name = 'qemu-system-x86_64.exe'
    if hasattr(config, 'qemu_exe_path'):
        return config.qemu_exe_path
    if not getattr(config, 'qemu_use_builtin', True):
        for wellknown_path in [
                r'c:\Program Files\qemu',
                r'd:\Program Files\qemu',
                r'e:\Program Files\qemu',
                ]:
            exe_path = os.path.join(wellknown_path, exe_name)
            if os.path.exists(exe_path):
                return exe_path
    return resource_path(os.path.join("data", "tools", "qemu", exe_name))
