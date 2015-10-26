#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Name:     syslinux.py
# Purpose:  Module to install syslinux and extlinux on selected USB disk.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
import os
import subprocess
import platform
import gen_fun
import config
import admin
from iso import ISO
from usb import USB


class Syslinux():
    """
    Main Syslinux class.
    """
    def __init__(self):
        self.usb_disk = config.usb_disk
        self.usb = USB()

    def install_default(self):
        """
        Install default syslinux/extlinux (version 4) on selected USB disk.
        """
        if config.iso_link:
            self.iso = ISO(config.iso_link)
        filesystem = self.usb.get_usb(config.usb_disk).filesystem
        mbr_bin = gen_fun.resource_path(os.path.join("tools", "mbr.bin"))
        config.status_text = "Installing default syslinux..."

        if filesystem == "ext2" or filesystem == "ext3" or filesystem == "ext4" or filesystem == "Btrfs" or filesystem == "ntfs":
            if platform.system() == "Linux":
                    syslinux_path = os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "extlinux4")
                    if os.access(syslinux_path, os.X_OK) is False:
                        subprocess.call('chmod +x ' + syslinux_path, shell=True)
                    path = os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb")
                    quoted_exe = "\"" + syslinux_path.replace('"', '\\"') + "\""
                    quoted_path = "\"" + path.replace('"', '\\"') + "\""
                    long_cmd = [quoted_exe, "--install", quoted_path,
                            "&&", "echo", "Default Extlinux install is success...",
                            "&&", "dd", "bs=440", "count=1", "conv=notrunc", "\"if=" + mbr_bin + "\"", "of=" + config.usb_disk[:-1],
                            "&&", "echo", "mbr install is success...",
                            "&&"] + self.set_boot_flag_cmd()
                    return admin.adminCmd(long_cmd) == 0

        elif filesystem == "vfat" or filesystem == "FAT32":
            if platform.system() == "Linux":
                syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4"))
                if os.access(syslinux, os.X_OK) is False:
                    subprocess.call(['chmod', '+x', syslinux])
                quoted_exe = "\"" + syslinux.replace('"', '\\"') + "\""
                long_cmd = [quoted_exe, "-i", "-d", "multibootusb", config.usb_disk,
                        "&&", "echo", "Default syslinux install is success...",
                        "&&", "dd", "bs=440", "count=1", "conv=notrunc", "\"if=" + mbr_bin + "\"", "of=" + config.usb_disk[:-1],
                        "&&", "echo", "mbr install is success...",
                        "&&"] + self.set_boot_flag_cmd()
                return admin.adminCmd(long_cmd) == 0

            elif platform.system() == "Windows":
                syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4.exe"))
                if subprocess.call(syslinux + ' -maf -d multibootusb ' + config.usb_disk, shell=True) == 0:
                    print "\nDefault syslinux install is success...\n"
                    return True
                else:
                    print "\nFailed to install default syslinux...\n"
                    return False

    def install_distro(self):
        """
        Install syslinux/extlinux on distro isolinux directory.
        """
        self.iso = ISO(config.iso_link)
        filesystem = self.usb.get_usb(config.usb_disk).filesystem
        config.status_text = "Installing distro specific syslinux..."
        if self.iso.isolinux_bin_exist() is not True:
            print "Distro doesnot use isolinux/syslinux for booting ISO."
        else:
            self.iso.iso_extract_file(os.path.join(gen_fun.mbusb_dir(), "iso_cfg_ext_dir"), "isolinux.bin")
            self.iso.iso_extract_file(os.path.join(gen_fun.mbusb_dir(), "iso_cfg_ext_dir"), "ISOLINUX.BIN")
            syslinux_version = self.iso.isolinux_version(self.iso.isolinux_bin_path(os.path.join(gen_fun.mbusb_dir(), "iso_cfg_ext_dir")))
            if config.distro == "generic" or config.distro == "alpine":
                install_dir = self.usb.get_usb(config.usb_disk).mount
                distro_syslinux_install_dir = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/")).replace(self.usb.get_usb(config.usb_disk).mount, "")
                distro_sys_install_bs = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/"), config.distro + '.bs')
            else:
                install_dir = os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename())
                distro_syslinux_install_dir = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/")).replace(self.usb.get_usb(config.usb_disk).mount, "")
                distro_sys_install_bs = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/"), config.distro + '.bs')

            if filesystem == "vfat" or filesystem == "FAT32":
                if syslinux_version == str(3):
                    if config.distro == "generic" and self.iso.isolinux_bin_dir() == "/":
                        option = ""
                    else:
                        option = " -d "
                else:
                    if config.distro == "generic" and self.iso.isolinux_bin_dir() == "/":
                        option = " -i "
                    else:
                        option = " -i -d "
                print "distro_syslinux_install_dir is " + distro_syslinux_install_dir
                print "distro_sys_install_bs is " + distro_sys_install_bs
                if platform.system() == "Linux":
                    syslinux_path = os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux") + syslinux_version
                    if os.access(syslinux_path, os.X_OK) is False:
                        subprocess.call('chmod +x ' + syslinux_path, shell=True) == 0
                    quoted_exe = "\"" + syslinux_path.replace('"', '\\"') + "\""
                    quoted_install_dir = distro_syslinux_install_dir.replace('"', '\\"')
                    quoted_bs = "of=\"" + distro_sys_install_bs.replace('"', '\\"') + "\""
                    long_cmd = [quoted_exe, option, quoted_install_dir, config.usb_disk,
                            "&&", "dd", "count=1", "if=" + config.usb_disk, quoted_bs]
                    return admin.adminCmd(long_cmd) == 0
                elif platform.system() == "Windows":
                    syslinux_path = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin")) + \
                               "\syslinux" + syslinux_version + ".exe"
                    distro_syslinux_install_dir = "/" + distro_syslinux_install_dir.replace("\\", "/")
                    distro_sys_install_bs = distro_sys_install_bs.replace("/", "\\")
                    print "\nExecuting ==> " + syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk + ' ' +  \
                          distro_sys_install_bs + "\n"
                    if subprocess.call(syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk + ' '
                        + distro_sys_install_bs, shell=True) == 0:
                        print "\nSyslinux install was successful on distro directory...\n"
                    else:
                        print "\nFailed to install syslinux on distro directory...\n"

            elif filesystem == "ext2" or filesystem == "ext3" or filesystem == "ext4" or filesystem == "Btrfs" or filesystem == "ntfs":
                distro_syslinux_install_dir = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/"))
                if platform.system() == "Linux":
                    syslinux_path = os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "extlinux") + syslinux_version
                    if os.access(syslinux_path, os.X_OK) is False:
                        subprocess.call('chmod +x ' + syslinux_path, shell=True) == 0
                    quoted_exe = "\"" + syslinux_path.replace('"', '\\"') + "\""
                    quoted_install_dir = distro_syslinux_install_dir.replace('"', '\\"')
                    quoted_bs = "of=\"" + distro_sys_install_bs.replace('"', '\\"') + "\""
                    long_cmd = [quoted_exe, "--install", quoted_install_dir,
                            "&&", "dd", "count=1", "if=" + config.usb_disk, quoted_bs]
                    return admin.adminCmd(long_cmd) == 0

    def set_boot_flag_cmd(self):
        disk = config.usb_disk[:-1]
        return ["echo", "Checking boot flag on " + disk,
                "&&", "if", "parted", "-m", "-s", disk, "print", "|", "grep", "-q", "boot", ";", "then",
                    "echo", "Disk already has boot flag.",
                ";", "else",
                    "echo", "Disk has no boot flag.", ";",
                    "if", "parted", disk, "set", "1", "boot", "on", ";", "then",
                        "echo", "Boot flag set to bootable on " + disk,
                    ";", "else",
                        "echo", "Unable to set boot flag on  " + disk,
                    ";", "fi",
                ";", "fi"]
