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
        self.iso = ISO(config.iso_link)
        filesystem = self.usb.get_usb(config.usb_disk).filesystem
        mbr_bin = gen_fun.resource_path(os.path.join("tools", "mbr.bin"))
        config.status_text = "Installing default syslinux..."

        if filesystem == "ext2" or filesystem == "ext3" or filesystem == "ext4" or filesystem == "Btrfs":
            if platform.system() == "Linux":
                    syslinux_path = os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "extlinux4")
                    if os.access(syslinux_path, os.X_OK) is False:
                        subprocess.call('chmod +x ' + syslinux_path, shell=True)
                    if config.user_password:
                        print "Executing ==> " + syslinux_path + " --install " + os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb")
                        if subprocess.call('echo ' + config.user_password + ' | sudo -S ' + syslinux_path +
                                                   " --install " + os.path.join(self.usb.get_usb(config.usb_disk).mount,
                                                                                "multibootusb"), shell=True) == 0:
                            print "Default Extlinux install is success..."
                            if subprocess.call('echo ' + config.user_password + ' | sudo -S dd bs=440 count=1 conv=notrunc if=' + mbr_bin +
                                                                                    ' of=' + config.usb_disk[:-1], shell=True) == 0:
                                print "mbr install is success..."
                                return True
                            else:
                                print "Failed to install default extlinux..."
                                return False
                    else:
                        print "Executing ==> " + syslinux_path + " --install " +  os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb")
                        if subprocess.call(syslinux_path + " --install " + os.path.join(self.usb.get_usb(config.usb_disk).mount,
                                                                                    "multibootusb"), shell=True) == 0:
                            print "Extlinux install on distro directory is success..."
                            if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin +
                                                                                    ' of=' + config.usb_disk[:-1], shell=True) == 0:
                                print "mbr install is success..."
                                return True
                            else:
                                print "Failed to install default extlinux..."
                                return False

        elif filesystem == "vfat" or filesystem == "ntfs" or filesystem == "FAT32":
            if platform.system() == "Linux":
                syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4"))
                if os.access(syslinux, os.X_OK) is False:
                    subprocess.call('chmod +x ' + syslinux, shell=True)
                if config.user_password:
                    print "Executing ==> " + syslinux + ' -i -d multibootusb ' + config.usb_disk
                    if subprocess.call('echo ' + config.user_password + ' | sudo -S ' + syslinux + ' -i -d multibootusb ' +
                                        config.usb_disk, shell=True) == 0:
                        print "Default syslinux install is success..."
                        if subprocess.call('echo ' + config.user_password + ' | sudo -S dd bs=440 count=1 conv=notrunc if=' + mbr_bin +
                                                                                        ' of=' + config.usb_disk[:-1], shell=True) == 0:
                            print "mbr install is success..."
                            return True
                        else:
                            print "Failed to install default syslinux..."
                            return False
                else:
                    print "Executing ==> " + syslinux + ' -i -d multibootusb ' + config.usb_disk
                    if subprocess.call(syslinux + ' -i -d multibootusb ' + config.usb_disk, shell=True) == 0:
                        print "Default syslinux install is success..."
                        if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + config.usb_disk[:-1],
                                           shell=True) == 0:
                            print "mbr install is success..."
                            return True
                        else:
                            print "Failed to install default syslinux..."
                            return False

            elif platform.system() == "Windows":
                syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4.exe"))
                if subprocess.call(syslinux + ' -maf -d multibootusb ' + config.usb_disk, shell=True) == 0:
                    print "Default syslinux install is success..."
                    return True
                else:
                    print "Failed to install default syslinux..."
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
            if config.distro == "generic":
                install_dir = self.usb.get_usb(config.usb_disk).mount
                distro_syslinux_install_dir = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/")).replace(self.usb.get_usb(config.usb_disk).mount, "")
                distro_sys_install_bs = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/"), config.distro + '.bs')
            else:
                install_dir = os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename())
                distro_syslinux_install_dir = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/")).replace(self.usb.get_usb(config.usb_disk).mount, "")
                distro_sys_install_bs = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/"), config.distro + '.bs')

            if filesystem == "vfat" or filesystem == "ntfs" or filesystem == "FAT32":
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
                    if config.user_password:
                        print "Executing ==> " + syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk
                        if subprocess.call('echo ' + config.user_password + ' | sudo -S ' + syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk, shell=True) == 0:
                            print "\nSyslinux install on distro directory is success..."
                            print "Executing ==> " + 'dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1'
                            if subprocess.call('echo ' + config.user_password + ' | sudo -S dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1', shell=True) == 0:
                                print "\nBootsector copy is success..."
                            else:
                                print "Failed to install syslinux on distro directory..."
                    else:
                        print "Executing ==> " + syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk
                        if subprocess.call(syslinux_path + option + distro_syslinux_install_dir + ' ' + self.usb_disk, shell=True) == 0:
                            print "Syslinux install on distro directory is success..."
                            if subprocess.call('dd if=' + self.usb_disk + ' ' + 'of=' + self.usb.get_usb(config.usb_disk).mount + distro_sys_install_bs + ' count=1', shell=True) == 0:
                                print "\nBootsector copy is success..."
                            else:
                                print "Failed to install syslinux on distro directory..."
                elif platform.system() == "Windows":
                    syslinux_path = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin")) + \
                               "\syslinux" + syslinux_version + ".exe"
                    distro_syslinux_install_dir = "/" + distro_syslinux_install_dir.replace("\\", "/")
                    print "Executing ==> " + syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk + ' ' +  \
                          os.path.join(self.usb.get_usb(config.usb_disk).mount, distro_sys_install_bs).replace("\\", "/")
                    if subprocess.call(syslinux_path + option + distro_syslinux_install_dir + ' ' + self.usb_disk + ' '
                        + os.path.join(self.usb.get_usb(config.usb_disk).mount, distro_sys_install_bs).replace("\\", "/"), shell=True) == 0:
                        print "Syslinux install was successful on distro directory..."
                    else:
                        print "Failed to install syslinux on distro directory..."

            elif filesystem == "ext2" or filesystem == "ext3" or filesystem == "ext4" or filesystem == "Btrfs":
                distro_syslinux_install_dir = os.path.join(install_dir, self.iso.isolinux_bin_dir().strip("/"))
                if platform.system() == "Linux":
                    syslinux_path = os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "extlinux") + syslinux_version
                    if os.access(syslinux_path, os.X_OK) is False:
                        subprocess.call('chmod +x ' + syslinux_path, shell=True) == 0
                    if config.user_password:
                        print "Executing ==> " + syslinux_path + " --install " + distro_syslinux_install_dir
                        if subprocess.call('echo ' + config.user_password + ' | sudo -S ' + syslinux_path + " --install " + distro_syslinux_install_dir, shell=True) == 0:
                            print "\nSyslinux install on distro directory is success..."
                            print "Executing ==> " + 'dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1'
                            if subprocess.call('echo ' + config.user_password + ' | sudo -S dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1', shell=True) == 0:
                                print "\nBootsector copy is success..."
                            else:
                                print "Failed to install syslinux on distro directory..."
                    else:
                        print "Executing ==> " + syslinux_path + " --install " + distro_syslinux_install_dir
                        if subprocess.call(syslinux_path + " --install " + distro_syslinux_install_dir, shell=True) == 0:
                            print "Syslinux install on distro directory is success..."
                            if subprocess.call('dd if=' + self.usb_disk + ' ' + 'of=' + self.usb.get_usb(config.usb_disk).mount + distro_sys_install_bs + ' count=1', shell=True) == 0:
                                print "\nBootsector copy is success..."
                            else:
                                print "Failed to install syslinux on distro directory..."