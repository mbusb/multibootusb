#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     iso.py
# Purpose:  Module to manupulate iso image
# Authors:  Sundar
# Depends:  isodump.py is authored by Johni Lee for MultiBootUSB
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import string
import platform
import re
from isodump import ISO9660
import config


class ISO():
    """
    Get ISO details of an ISO file. Support only for ISO9660 format.
    """
    def __init__(self, iso_link):
        """
        Parameter
        -----------
        iso_link : string and it is a path to iso file.
        """
        self.iso_link = iso_link
        self.iso9660fs = ISO9660(self.iso_link)

    def iso_name(self):
        """
        Find the name of an ISO.
        :return: Name of an ISO (with extension) as string. Returns If not returns None.
        """
        try:
            name = os.path.basename(str(self.iso_link))
        except:
            name = None

        return name

    def iso_basename(self):
        """
        Find the base name of an ISO.
        :return: Base name (without extension) of a selected ISO as string. If not returns None.
        """
        try:
            dir_name = str(os.path.splitext(os.path.basename(str(config.iso_link)))[0])
        except:
            dir_name = None

        return dir_name

    def isolinux_bin_exist(self):
        """
        Check if an "isolinux.bin" file exist.
        :return: True if "isolinux.bin" file exist of False if not.
        """
        if os.path.exists(self.iso_link):
            iso_file_list = self.iso9660fs.readDir("/")
            if any("isolinux.bin" in s.lower() for s in iso_file_list):
                result = True
            else:
                result = False

            return result

    def is_bootable(self):
        """
        Check if an ISO has the ability to boot.
        :return: True if ISO is bootable and False if not.
        """
        isBootable = self.iso9660fs.checkISOBootable()
        if isBootable:
            return True
        else:
            return False

    def isolinux_bin_dir(self):
        """
        Detects "isolinux.bin" directory.
        :return: path of "isolinux.bin" directory as string.
        """
        if os.path.exists(self.iso_link):
            iso_file_list = self.iso9660fs.readDir("/")
            if any("isolinux.bin" in s.lower() for s in iso_file_list):
                for f in iso_file_list:
                    if 'isolinux.bin' in f.lower():
                        bin_dir = os.path.dirname(f)
            else:
                bin_dir = False

            return bin_dir

    def isolinux_bin_path(self, path_to_dir):
        """
        Detects pat to "isolinux.bin".
        :return: path of "isolinux.bin" directory as string.
        """
        for dirpath, dirnames, filenames in os.walk(path_to_dir):
            for f in filenames:
                if f.endswith("isolinux.bin") or f.endswith("ISOLINUX.CFG"):
                    isolinux_bin_path = os.path.join(dirpath, f)
                    return isolinux_bin_path

    def integrity(self):
        """
        Check the integrity of an ISO.
        :return: True if integrity passes or False if it fails.
        """
        if os.path.exists(self.iso_link):
            if self.iso9660fs.checkIntegrity():
                print "ISO passed."
                result = True
            else:
                print "ISO failed."
                result = False
            return result

    def iso_extract_file(self, dest_dir, filter):
        """
        Extract the specific file(s) from an ISO
        :param dest_dir: Path to destination directory.
        :param filter: Filter to extract particular file(s)
        :return: Extract file(s) to destination.
        """
        if os.path.exists(self.iso_link) and os.path.exists(dest_dir):
            self.iso9660fs.writeDir("/", dest_dir, filter)

    def iso_extract_full(self, dest_dir):
        """
        Extract an ISO to destination directory
        :param dest_dir: Destination path as string.
        :return: False if it fails or extract ISO files to destination directory.
        """
        try:
            self.iso9660fs.writeDir("/", dest_dir)
        except:
            print "ISO extraction failed."
            return False

    def distro(self, iso_cfg_ext_dir):
        """
        Detect if distro is supported by multibootusb.
        :param iso_cfg_ext_dir: Directory where *.cfg files are extracted.
        :return: Detected distro name as string.
        """
        if platform.system() == "Linux" or platform.system() == "Windows":
            for path, subdirs, files in os.walk(iso_cfg_ext_dir):
                for name in files:
                    if name.endswith('.cfg') or name.endswith('.CFG'):
                        try:
                            string = open(os.path.join(path, name)).read()
                        except IOError:
                            return "Read Error."
                        else:
                            if re.search(r'ubcd', string, re.I):
                                return "ubcd"
                            elif re.search(r'hbcd', string, re.I):
                                return "hbcd"
                            elif re.search(r'systemrescuecd', string, re.I):
                                return "systemrescuecd"
                            elif re.search(r'pmagic|partedmagic', string, re.I):
                                return "parted-magic"
                            elif re.search(r'mgalive', string,re.I):  # mounting fat filesystem hard coded in to initrd.
                                                                        # Can be modified only under linux.
                                return "mageialive"
                            elif re.search(r'archisolabel|misolabel', string, re.I):
                                return "arch"
                            elif re.search(r'chakraisolabel', string, re.I):
                                return "chakra"
                            elif re.search(r'boot=live', string, re.I):
                                return "debian"
                            elif re.search(r'solydx', string, re.I):
                                return "solydx"
                            elif re.search(r'knoppix', string, re.I):
                                return "knoppix"
                            elif re.search(r'root=live', string, re.I):
                                return "fedora"
                            elif re.search(r'redhat', string, re.I):
                                return "redhat"
                            #elif re.search(r'suse', string, re.I):
                            #   return "suse"
                            elif re.search(r'opensuse', string,
                                           re.I):
                                return "opensuse"
                            elif re.search(
                                    r'slitaz|dban|ophcrack|tinycore|rescue.cpi|xpud|untangle|4mlinux|partition wizard|'
                                    r'riplinux|lebel dummy',string, re.I):
                                return "slitaz"
                            elif re.search(r'boot=casper', string, re.I):
                                return "ubuntu"
                            elif re.search(r'wifislax', string, re.I):
                                return "wifislax"
                            elif re.search(r'slax', string, re.I):
                                return "slax"
                            elif re.search(r'sms|vector|autoexec', string, re.I):
                                return "sms"
                            elif re.search(r'antix', string, re.I):
                                return "antix"
                            elif re.search(r'porteus', string, re.I):
                                return "porteus"
                            elif re.search(r'livecd=livecd|PCLinuxOS', string, re.I):
                                return "pclinuxos"
                            elif re.search(r'looptype=squashfs', string, re.I):
                                return "gentoo"
                            elif re.search(r'finnix', string, re.I):
                                return "finnix"
                            elif re.search(r'wifiway', string, re.I):
                                return "wifiway"
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
                            elif re.search(r'ubuntu server', string, re.I):
                                return "ubuntu-server"
                            elif re.search(r'Welcome to CentOS', string, re.I):
                                return "centos-net-minimal"
                            elif re.search(r'Trinity Rescue Kit', string, re.I):
                                return "trinity-rescue"

            distro = self.detect_iso_from_file_list()
            if distro:
                return distro
                # FIXME: See the below comments.
                '''
                else:
                    # FIXME: The idea of detecting as generic is to work like a unetbootin if other methods fails.
                    #  This simply extracts distro to root of the USB and install syslinux on isolinux.bin directory.
                    #  All works fine but unable to boot the distro successfully. Also, see the generic section from
                    #  syslinux, update_cfg and install_distro modules.
                    if self.isolinux_bin_exist():
                        return "generic"
                '''
            else:
                return None

    def detect_iso_from_file_list(self):
        """
        Fallback detection script from the content of an ISO.
        :return:
        """
        if os.path.exists(self.iso_link):
            print "ISO exist."
            iso_file_list = self.iso9660fs.readDir("/")
            if any("sources" in s.lower() for s in iso_file_list):
                return "Windows"
            elif any("config.isoclient" in s.lower() for s in iso_file_list):
                return "opensuse"
            elif any("dban" in s.lower() for s in iso_file_list):
                return "slitaz"
            else:
                print iso_file_list

    def iso_file_list(self):
        """
        Function to return the content of an ISO.
        :return: List of files of an ISO as list.
        """
        iso_file_list = self.iso9660fs.readDir("/")
        return iso_file_list

    def strings(self, filename, min=4):
        """
        Similar to strings command in Linux.
        :param filename: Path to file as string.
        :param min: Printable character of a file. Default is 4.
        :return: All printable character of a file.
        """
        with open(filename, "rb") as f:
            result = ""
            for c in f.read():
                if c in string.printable:
                    result += c
                    continue
                if len(result) >= min:
                    yield result
                result = ""

    def isolinux_version(self, isolinux_bin_path):
        """
        Detect isolinux version shipped by distros.
        :param isolinux_path: Path to "isolinux.bin"
        :return: Version number as string.
        """
        version = ["3", "4", "5", "6"]
        if not isolinux_bin_path == None:
            sl = list(self.strings(isolinux_bin_path))
            for strin in sl:
                if re.search(r'isolinux ', strin, re.I):
                    for number in version:
                        if re.search(r'isolinux ' + number, strin, re.I):
                            print "\n\nFound syslinux version " + number + "\n\n"
                            config.sys_version = number
                            return str(number)
