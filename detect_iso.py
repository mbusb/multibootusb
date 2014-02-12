#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module to detect distros.
"""

import os, sys, re, platform, var, glob
from PyQt4 import QtGui
from multibootusb_ui import Ui_Dialog


class AppGui(QtGui.QDialog, Ui_Dialog):
    def detect_iso(self, iso_cfg_ext_dir):
        if sys.platform.startswith("linux") or platform.system() == "Windows":
            for path, subdirs, files in os.walk(iso_cfg_ext_dir):
                for name in files:
                    if name.endswith('.cfg'):
                        try:
                            string = open(os.path.join(path, name)).read()
                        except IOError:
                            var.cfg_read_err = "yes"
                        else:
                            if re.search(r'ubcd', string, re.I):
                                return "ubcd"
                            elif re.search(r'hbcd', string, re.I):
                                return "hbcd"
                            elif re.search(r'pmagic|partedmagic', string, re.I):
                                return "parted-magic"
                            elif re.search(r'mgalive', string,
                                           re.I):  # mounting fat filesystem hard coded in to initrd. Can be modifed only under linux.
                                return "mageialive"
                            elif re.search(r'archisolabel|misolabel', string, re.I):
                                return "arch"
                            elif re.search(r'chakraisolabel', string, re.I):
                                return "chakra"
                            elif re.search(r'boot=live', string, re.I):
                                return "debian"
                            elif re.search(r'knoppix', string, re.I):
                                return "knoppix"
                            elif re.search(r'root=live', string, re.I):
                                return "fedora"
                            elif re.search(r'redhat', string, re.I):
                                return "redhat"
                            elif re.search(r'suse', string, re.I):
                                return "suse"
                            elif re.search(r'opensuse', string,
                                           re.I):  # or re.search(r'config.isoclient', var.iso_file_content, re.I):
                                return "opensuse"
                            elif re.search(
                                    r'slitaz|ophcrack|tinycore|rescue.cpi|xpud|untangle|4mlinux|partition wizard|riplinux|lebel dummy',
                                    string, re.I):
                                return "slitaz"
                            elif re.search(r'systemrescuecd', string, re.I):
                                return "systemrescuecd"
                            elif re.search(r'boot=casper', string, re.I):
                                return "ubuntu"
                            elif re.search(r'slax', string, re.I):
                                return "slax"
                            elif re.search(r'sms|vector|autoexec', string, re.I):
                                return "sms"
                            elif re.search(r'antix', string, re.I):
                                return "antix"
                            elif re.search(r'porteus', string, re.I):
                                return "porteus"
                            elif re.search(r'wifislax', string, re.I):
                                return "wifislax"
                            elif re.search(r'livecd=livecd|unity', string, re.I):
                                return "pclinuxos"
                            elif re.search(r'looptype=squashfs', string, re.I):
                                return "gentoo"
                            elif re.search(r'finnix', string, re.I):
                                return "finnix"
                            elif re.search(r'wifiway', string, re.I):
                                return "wifiway"
                            #elif re.search(r'slack|salix', string, re.I):
                            #	return "salix"
                            elif re.search(r'puppy', string, re.I):
                                return "puppy"
                            elif re.search(r'ipcop', string, re.I):
                                return "ipcop"
                            elif re.search(r'ipfire', string, re.I):
                                return "ipfire"
                            elif re.search(r'zenwalk|slack|salix', string, re.I) and re.search(r'live', string, re.I):
                                return "salix-live"
                            elif re.search(r'zenwalk|slack|salix', string, re.I):
                                return "zenwalk"


    def detect_iso_zip_info(self):

        if re.search(r'sources', var.iso_file_content, re.I):
            return "windows"
        elif re.search(r'0.img', var.iso_file_content, re.I):
            return "opensuse"
