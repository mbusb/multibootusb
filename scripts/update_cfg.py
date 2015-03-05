#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     update_cfg.py
# Purpose:  Module to manipulate distro specific and main config files.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import re
import config
from usb import USB
from iso import ISO
import shutil
import gen_fun

class UpdateCfgFile():
    """
    Update distro and multibootusb congig file(s).
    """
    def __init__(self):
        self.usb_disk = config.usb_disk
        self.usb = USB()


    def distro_cfg_files(self):
        """
        Main function to modify/update distro specific strings on distro config files.
        :return:
        """
        #self.usb = USB()
        self.iso = ISO(config.iso_link)
        config.status_text = "Updating config files..."
        install_dir = os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename())
        for dirpath, dirnames, filenames in os.walk(install_dir):
            for f in filenames:
                if f.endswith(".cfg"):
                    cfg_file = os.path.join(dirpath, f)
                    try:
                        string = open(cfg_file).read()
                    except IOError:
                        print "Unable to read " + cfg_file
                    else:
                        if not config.distro == "generic":
                            replace_text = r'\1/multibootusb/' + self.iso.iso_basename() + '/'
                            string = re.sub(r'([ \t =,])/', replace_text, string)
                    if config.distro == "ubuntu":
                        string = re.sub(r'boot=casper',
                                        'boot=casper cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid ignore_bootid root=UUID=' + self.usb.get_usb(config.usb_disk).uuid + ' live-media-path=/multibootusb/' +
                                        self.iso.iso_basename() + '/casper', string)
                        if not config.persistence == 0:
                            string = re.sub(r'boot=casper', 'boot=casper persistent persistent-path=/multibootusb/' +
                                            self.iso.iso_basename() + "/", string)
                    elif config.distro == "debian":
                        string = re.sub(r'boot=live', 'boot=live ignore_bootid live-media-path=/multibootusb/' +
                                        self.iso.iso_basename() + '/live', string)
                        if not config.persistence == 0:
                            string = re.sub(r'boot=live', 'boot=live persistent persistent-path=/multibootusb/' +
                                                      self.iso.iso_basename() + "/", string)

                    elif config.distro == "ubuntu-server":
                        string = re.sub(r'file', 'cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid ignore_bootid root=UUID=' + self.usb.get_usb(config.usb_disk).uuid + ' file', string)
                    elif config.distro == "fedora":
                        string = re.sub(r'root=\S*', 'root=UUID=' + self.usb.get_usb(config.usb_disk).uuid, string)
                        if re.search(r'liveimg', string, re.I):
                            string = re.sub(r'liveimg', 'liveimg live_dir=/multibootusb/' +
                                                     self.iso.iso_basename() + '/LiveOS', string)
                        elif re.search(r'rd.live.image', string, re.I):
                            string = re.sub(r'rd.live.image', 'rd.live.image rd.live.dir=/multibootusb/' +
                                                     self.iso.iso_basename() + '/LiveOS', string)
                        if not config.persistence == 0:
                            if re.search(r'liveimg', string, re.I):
                                string = re.sub(r'liveimg', 'liveimg overlay=UUID=' + self.usb.get_usb(config.usb_disk).uuid, string)
                            elif re.search(r'rd.live.image', string, re.I):
                                string = re.sub(r'rd.live.image', 'rd.live.image rd.live.overlay=UUID=' + self.usb.get_usb(config.usb_disk).uuid, string)
                            string = re.sub(r' ro ', ' rw ', string)
                    elif config.distro == "parted-magic":
                        if re.search(r'append', string, re.I):
                            string = re.sub(r'append ', 'append directory=/multibootusb/' + self.iso.iso_basename(), string, flags=re.I)
                        string = re.sub(r'initrd=', 'directory=/multibootusb/' + self.iso.iso_basename() + '/ initrd=',
                                        string)
                    elif config.distro == "ubcd":
                        string = re.sub(r'iso_filename=\S*', 'directory=/multibootusb/' + self.iso.iso_basename(),
                                        string, flags=re.I)
                    elif config.distro == "ipcop":
                        string = re.sub(r'ipcopboot=cdrom\S*', 'ipcopboot=usb', string)
                    elif config.distro == "puppy":
                        string = re.sub(r'pmedia=cd\S*',
                                        'pmedia=usbflash psubok=TRUE psubdir=/multibootusb/' + self.iso.iso_basename() + '/',
                                        string)
                    elif config.distro == "slax":
                        string = re.sub(r'initrd=', r'from=/multibootusb/' + self.iso.iso_basename() + '/slax fromusb initrd=', string)
                    elif config.distro == "knoppix":
                        string = re.sub(r'(append)',
                                        r'\1  knoppix_dir=/multibootusb/' + self.iso.iso_basename() + '/KNOPPIX',
                                        string)
                    elif config.distro == "gentoo":
                        string = re.sub(r'append ', 'append real_root=' + config.usb_disk + ' slowusb subdir=/multibootusb/' +
                                        self.iso.iso_basename() + '/ ', string, flags=re.I)
                    elif config.distro == "systemrescuecd":
                        rows = []
                        subdir = '/multibootusb/' + self.iso.iso_basename() + '/'
                        for line in string.splitlines(True):
                            addline = True
                            if re.match(r'append.*--.*', line, flags=re.I):
                                line = re.sub(r'(append)(.*)--(.*)', r'\1\2subdir=' + subdir + r' --\3 subdir=' + subdir,
                                       line, flags=re.I)
                            elif re.match(r'append', line, flags=re.I):
                                    line = re.sub(r'(append)', r'\1 subdir=' + subdir, line, flags=re.I)
                            elif re.match(r'label rescue(32|64)_1', line, flags=re.I):
                                rows.append(line)
                                rows.append('append subdir=%s\n' % (subdir,))
                                addline = False

                            if addline:
                                rows.append(line)

                        string = ''.join(rows)
                    elif config.distro == "arch" or config.distro == "chakra":
                        string = re.sub(r'isolabel=\S*', 'isodevice=/dev/disk/by-uuid/' + self.usb.get_usb(config.usb_disk).uuid, string,
                                        flags=re.I)
                        string = re.sub(r'isobasedir=',
                                        'isobasedir=/multibootusb/' + self.iso.iso_basename() + '/', string,
                                        flags=re.I)
                    elif config.distro == "suse" or config.distro == "opensuse":
                        if re.search(r'opensuse_12', string, re.I):
                            string = re.sub(r'append', 'append loader=syslinux isofrom_system=/dev/disk/by-uuid/' + self.usb.get_usb(config.usb_disk).uuid + ":/" + self.iso.iso_name(), string, flags=re.I)
                        else:
                            string = re.sub(r'append', 'append loader=syslinux isofrom_device=/dev/disk/by-uuid/' + self.usb.get_usb(config.usb_disk).uuid + ' isofrom_system=/multibootusb/' + self.iso.iso_basename() + '/'+ self.iso.iso_name(), string, flags=re.I)
                    elif config.distro == "pclinuxos":
                        string = re.sub(r'livecd=',
                                        'fromusb livecd=' + '/multibootusb/' + self.iso.iso_basename() + '/',
                                        string)
                        string = re.sub(r'prompt', '#prompt', string)
                        string = re.sub(r'ui gfxboot.com', '#ui gfxboot.com', string)
                        string = re.sub(r'timeout', '#timeout', string)
                    elif config.distro == "porteus" or config.distro == "wifislax":
                        string = re.sub(r'initrd=',
                                        'from=' + '/multibootusb/' + self.iso.iso_basename() + ' initrd=', string)
                    elif config.distro == "hbcd":
                        string = re.sub(r'/HBCD', '/multibootusb/' + self.iso.iso_basename() + '/HBCD', string)
                    elif config.distro == "zenwalk":
                        string = re.sub(r'initrd=', 'from=/multibootusb/' + self.iso.iso_basename() + '/' + self.iso.iso_name() + ' initrd=', string)
                    elif config.distro == "mageialive":
                        string = re.sub(r'LABEL=\S*', 'LABEL=' + self.usb.get_usb(config.usb_disk).label, string)
                    elif config.distro == "antix":
                        string = re.sub(r'APPEND', 'image_dir=/multibootusb/' + self.iso.iso_basename(), string)
                    elif config.distro == "solydx":
                        string = re.sub(r'live-media-path=', 'live-media-path=/multibootusb/' + self.iso.iso_basename(), string)
                    elif config.distro == "salix-live":
                        string = re.sub(r'iso_path', '/multibootusb/' + self.iso.iso_basename() + '/' + self.iso.iso_name(), string)

                    config_file = open(cfg_file, "wb")
                    config_file.write(string)
                    config_file.close()

        # Patch for Ubuntu 14.10 and above which uses syslinux version 6
        if config.distro == "ubuntu" and config.sys_version == "6":
            print "Applying Ubuntu patch..."
            for module in os.listdir(os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename(), "isolinux")):
                if module.endswith(".c32"):
                    if os.path.exists(os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename(), "isolinux", module)):
                        try:
                            os.remove(os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename(), "isolinux", module))
                            print "Copying " + module
                            shutil.copy(gen_fun.resource_path(os.path.join(gen_fun.mbusb_dir(), "syslinux", "modules", "ubuntu_patch", module)),
                                    os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename(), "isolinux", module))
                        except:
                            print "Could not copy " + module

        self.main_cfg_file()

    def main_cfg_file(self):
        """
        Update main multibootusb suslinux.cfg file after distro is installed.
        :return:
        """
        #self.usb = USB()
        self.iso = ISO(config.iso_link)
        sys_cfg_file = os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", "syslinux.cfg")
        install_dir = os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", self.iso.iso_basename())
        print "Updating main syslinux config file..."
        if os.path.exists(sys_cfg_file):

            if config.distro == "hbcd":
                if os.path.exists(os.path.join(self.usb.get_usb(config.usb_disk).mount,  "multibootusb", "menu.lst")):
                    config_file = open(os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb", "menu.lst"), "wb")
                    string = re.sub(r'/HBCD', '/multibootusb/' + self.iso.iso_basename() + '/HBCD', config_file)
                    config_file.write(string)
                    config_file.close()

            if config.distro == "Windows":
                if os.path.exists(sys_cfg_file):
                    config_file = open(sys_cfg_file, "a")
                    config_file.write("#start " + self.iso.iso_basename() + "\n")
                    config_file.write("LABEL " + self.iso.iso_basename() + "\n")
                    config_file.write("MENU LABEL " + self.iso.iso_basename() + "\n")
                    config_file.write("KERNEL chain.c32 hd0 1 ntldr=/bootmgr" + "\n")
                    config_file.write("#end " + self.iso.iso_basename() + "\n")
                    config_file.close()

            else:
                config_file = open(sys_cfg_file, "a")
                config_file.write("#start " + self.iso.iso_basename() + "\n")
                config_file.write("LABEL " + self.iso.iso_basename() + "\n")
                config_file.write("MENU LABEL " + self.iso.iso_basename() + "\n")
                if config.distro == "salix-live":
                    config_file.write(
                        "LINUX " + '/multibootusb/' + self.iso.iso_basename() + '/boot/grub2-linux.img' + "\n")
                elif config.distro == "pclinuxos":
                    config_file.write("kernel " + '/multibootusb/' + self.iso.iso_basename() + '/isolinux/vmlinuz' + "\n")
                    config_file.write("append livecd=livecd root=/dev/rd/3 acpi=on vga=788 keyb=us vmalloc=256M nokmsboot "
                                      "fromusb root=UUID=" + self.usb.get_usb(config.usb_disk).uuid + " bootfromiso=/multibootusb/" +
                                      self.iso.iso_basename() +"/" + self.iso.iso_name() + " initrd=/multibootusb/"
                                      + self.iso.iso_basename() + '/isolinux/initrd.gz' + "\n")
                else:
                    if config.distro == "ubuntu" and config.sys_version == "6":
                        config_file.write("CONFIG " + "/multibootusb/" + self.iso.iso_basename() +
                                          "/isolinux/isolinux.cfg" + "\n")
                        config_file.write("APPEND " + "/multibootusb/" + self.iso.iso_basename() +
                                          "/isolinux" + "\n")
                    else:
                        if config.distro == "generic":
                            distro_syslinux_install_dir = self.iso.isolinux_bin_dir()
                            if not self.iso.isolinux_bin_dir() == "/":
                                distro_sys_install_bs = os.path.join(self.usb.get_usb(config.usb_disk).mount, self.iso.isolinux_bin_dir()) + '/' + config.distro + '.bs'
                            else:
                                distro_sys_install_bs = '/' + config.distro + '.bs'
                        else:
                            distro_syslinux_install_dir = install_dir
                            distro_syslinux_install_dir = distro_syslinux_install_dir.replace(self.usb.get_usb(config.usb_disk).mount, '')
                            distro_sys_install_bs = distro_syslinux_install_dir + self.iso.isolinux_bin_dir() + '/' + config.distro + '.bs'

                        distro_sys_install_bs = "/" + distro_sys_install_bs.replace("\\", "/")  #  Windows path issue.
                        config_file.write("BOOT " + distro_sys_install_bs.replace("//", "/") + "\n")
                config_file.write("#end " + self.iso.iso_basename() + "\n")
                config_file.close()

        for dirpath, dirnames, filenames in os.walk(install_dir):
            for f in filenames:
                if f.endswith("isolinux.cfg"):
                    shutil.copy2(os.path.join(dirpath, f), os.path.join(dirpath, "syslinux.cfg"))