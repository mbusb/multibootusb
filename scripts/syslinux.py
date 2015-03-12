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
                        print "\nExecuting ==> " + syslinux_path + " --install " + os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb\n")
                        if subprocess.call('echo ' + config.user_password + ' | sudo -S ' + syslinux_path +
                                                   " --install " + os.path.join(self.usb.get_usb(config.usb_disk).mount,
                                                                                "multibootusb"), shell=True) == 0:
                            print "Default Extlinux install is success..."
                            if subprocess.call('echo ' + config.user_password + ' | sudo -S dd bs=440 count=1 conv=notrunc if=' + mbr_bin +
                                                                                    ' of=' + config.usb_disk[:-1], shell=True) == 0:
                                print "mbr install is success..."
                                self.set_boot_flag()
                                return True
                            else:
                                print "Failed to install default extlinux..."
                                return False
                    else:
                        print "\nExecuting ==> " + syslinux_path + " --install " +  os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb\n")
                        if subprocess.call(syslinux_path + " --install " + os.path.join(self.usb.get_usb(config.usb_disk).mount,
                                                                                    "multibootusb"), shell=True) == 0:
                            print "\nExtlinux install on distro directory is success...\n"
                            if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin +
                                                                                    ' of=' + config.usb_disk[:-1], shell=True) == 0:
                                print "\nmbr install is success...\n"
                                self.set_boot_flag()
                                return True
                            else:
                                print "\nFailed to install default extlinux...\n"
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
                            self.set_boot_flag()
                            return True
                        else:
                            print "Failed to install default syslinux..."
                            return False
                else:
                    print "\nExecuting ==> " + syslinux + ' -i -d multibootusb ' + config.usb_disk + "\n"
                    if subprocess.call(syslinux + ' -i -d multibootusb ' + config.usb_disk, shell=True) == 0:
                        print "\nDefault syslinux install is success...\n"
                        if subprocess.call('dd bs=440 count=1 conv=notrunc if=' + mbr_bin + ' of=' + config.usb_disk[:-1],
                                           shell=True) == 0:
                            print "\nmbr install is success...\n"
                            self.set_boot_flag()
                            return True
                        else:
                            print "\nFailed to install default syslinux...\n"
                            return False

            elif platform.system() == "Windows":
                syslinux = gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "bin", "syslinux4.exe"))
                if subprocess.call(syslinux + ' -maf -d multibootusb ' + config.usb_disk, shell=True) == 0:
                    print "Default syslinux install is success..."
                    return True
                else:
                    print "Failed to install default syslinux..."
                    return False

        self.set_boot_flag()

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
                            print "\nExecuting ==> " + 'dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1\n'
                            if subprocess.call('echo ' + config.user_password + ' | sudo -S dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1', shell=True) == 0:
                                print "\nBootsector copy is success..."
                            else:
                                print "\nFailed to install syslinux on distro directory...\n"
                    else:
                        print "Executing ==> " + syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk
                        if subprocess.call(syslinux_path + option + distro_syslinux_install_dir + ' ' + config.usb_disk, shell=True) == 0:
                            print "Syslinux install on distro directory is success..."
                            print 'Executing ==> dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1'
                            if subprocess.call('dd if=' + config.usb_disk + ' ' + 'of=' + distro_sys_install_bs + ' count=1', shell=True) == 0:
                                print "\nBootsector copy is success...\n"
                            else:
                                print "\nFailed to copy boot sector...\n"
                        else:
                            print "\nFailed to install syslinux on distro directory...\n"
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

    def set_boot_flag(self):
        if platform.system() == "Linux":
            print "Checking boot flag on " + config.usb_disk[:-1]
            if config.user_password:
                cmd_out = subprocess.check_output("echo " + config.user_password + " | sudo -S parted -m -s " + config.usb_disk[:-1] + " print", shell=True)
                if "boot" in cmd_out:
                    print "Disk already has boot flag."
                else:
                    print "Executing ==>  parted " + config.usb_disk[:-1] + " set 1 boot on"
                    if subprocess.call('echo ' + config.user_password + ' | sudo -S ' + " parted " + config.usb_disk[:-1]+ " set 1 boot on", shell=True) == 0:
                        print "Boot flag set to bootable on " + config.usb_disk[:-1]
                    else:
                        print "Unable to set boot flag on  " + config.usb_disk[:-1]
            else:
                cmd_out = subprocess.check_output("parted -m -s " + config.usb_disk[:-1] + " print", shell=True)
                if "boot" in cmd_out:
                    print "Disk " + config.usb_disk[:-1] + " already has boot flag."
                else:
                    print "Executing ==>  parted " + config.usb_disk[:-1] + " set 1 boot on"
                    if subprocess.call("parted " + config.usb_disk[:-1]+ " set 1 boot on", shell=True) == 0:
                        print "Boot flag set to bootable " + config.usb_disk[:-1]
                    else:
                        print "Unable to set boot flag on  " + config.usb_disk[:-1]
