#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     update_cfg_file.py
# Purpose:  Module to manipulate distro specific and main config files.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import re
import shutil
from .usb import *
from .gen import *
from .iso import *
from . import config


def update_distro_cfg_files(iso_link, usb_disk, distro, persistence=0):
    """
    Main function to modify/update distro specific strings on distro config files.
    :return:
    """
    usb_details = details(usb_disk)
    usb_mount = usb_details['mount_point']
    usb_uuid = usb_details['uuid']
    usb_label = usb_details['label']
    patch = None
    iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir")
    if isolinux_bin_exist(config.iso_link):
        isolinux_path = os.path.join(iso_cfg_ext_dir, isolinux_bin_path(iso_link)[1:])
    config.status_text = "Updating config files..."
    install_dir = os.path.join(usb_mount, "multibootusb", iso_basename(iso_link))
    print('Updating distro specific config files...')
    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            if f.endswith(".cfg") or f.endswith('.CFG') or f.endswith('.lst'):
                cfg_file = os.path.join(dirpath, f)
                try:
                    string = open(cfg_file, errors='ignore').read()
                except IOError:
                    print("Unable to read ", cfg_file)
                else:
                    if not distro == "generic":
                        replace_text = r'\1/multibootusb/' + iso_basename(iso_link) + '/'
                        string = re.sub(r'([ \t =,])/', replace_text, string)
                if distro == "ubuntu":
                    string = re.sub(r'boot=casper',
                                    'boot=casper cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid '
                                    'ignore_bootid root=UUID=' + usb_uuid + ' live-media-path=/multibootusb/'
                                    + iso_basename(iso_link) + '/casper', string)
                    string = re.sub(r'ui gfxboot', '#ui gfxboot', string)
                    if not persistence == 0:
                        string = re.sub(r'boot=casper', 'boot=casper persistent persistent-path=/multibootusb/' +
                                        iso_basename(iso_link) + "/", string)

                elif distro == "debian" or distro == "debian-install":
                    string = re.sub(r'boot=live', 'boot=live ignore_bootid live-media-path=/multibootusb/' +
                                    iso_basename(iso_link) + '/live', string)
                    if not persistence == 0:
                        string = re.sub(r'boot=live', 'boot=live persistent persistent-path=/multibootusb/' +
                                        iso_basename(iso_link) + "/", string)

                elif distro == "ubuntu-server":
                    string = re.sub(r'file',
                                    'cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid ignore_bootid root=UUID=' +
                                    usb_uuid + ' file', string)
                elif distro == "fedora":
                    string = re.sub(r'root=\S*', 'root=UUID=' + usb_uuid, string)
                    if re.search(r'liveimg', string, re.I):
                        string = re.sub(r'liveimg', 'liveimg live_dir=/multibootusb/' +
                                        iso_basename(iso_link) + '/LiveOS', string)
                    elif re.search(r'rd.live.image', string, re.I):
                        string = re.sub(r'rd.live.image', 'rd.live.image rd.live.dir=/multibootusb/' +
                                        iso_basename(iso_link) + '/LiveOS', string)
                    if not persistence == 0:
                        if re.search(r'liveimg', string, re.I):
                            string = re.sub(r'liveimg',
                                            'liveimg overlay=UUID=' + usb_uuid, string)
                        elif re.search(r'rd.live.image', string, re.I):
                            string = re.sub(r'rd.live.image', 'rd.live.image rd.live.overlay=UUID=' + usb_uuid, string)
                        string = re.sub(r' ro ', ' rw ', string)
                elif distro == 'kaspersky':
                    if not os.path.exists(os.path.join(usb_mount, 'multibootusb', iso_basename(iso_link), 'kaspersky.cfg')):
                        shutil.copyfile(resource_path(os.path.join('data', 'multibootusb', 'syslinux.cfg')),
                                        os.path.join(usb_mount, 'multibootusb', iso_basename(iso_link), 'kaspersky.cfg'))
                        config_string = kaspersky_config('kaspersky')
                        config_string = config_string.replace('$INSTALL_DIR', '/multibootusb/' + iso_basename(iso_link))
                        config_string = re.sub(r'root=live:UUID=', 'root=live:UUID=' + usb_uuid, config_string)
                        with open(os.path.join(usb_mount, 'multibootusb', iso_basename(iso_link), 'kaspersky.cfg'), "a") as f:
                            f.write(config_string)
                elif distro == "parted-magic":
                    if re.search(r'append', string, re.I):
                        string = re.sub(r'append', 'append directory=/multibootusb/' + iso_basename(iso_link), string,
                                        flags=re.I)
                    string = re.sub(r'initrd=', 'directory=/multibootusb/' + iso_basename(iso_link) + '/ initrd=',
                                    string)
                elif distro == "ubcd":
                    string = re.sub(r'iso_filename=\S*', 'directory=/multibootusb/' + iso_basename(iso_link),
                                    string, flags=re.I)
                elif distro == 'f4ubcd':
                    if not 'multibootusb' in string:
                        string = re.sub(r'/HBCD', '/multibootusb/' + iso_basename(iso_link) + '/HBCD', string)
                    if not 'multibootusb' in string:
                        string = re.sub(r'/F4UBCD', '/multibootusb/' + iso_basename(iso_link) + '/F4UBCD', string)
                elif distro == "ipcop":
                    string = re.sub(r'ipcopboot=cdrom\S*', 'ipcopboot=usb', string)
                elif distro == "puppy":
                    string = re.sub(r'pmedia=cd\S*',
                                    'pmedia=usbflash psubok=TRUE psubdir=/multibootusb/' + iso_basename(iso_link) + '/',
                                    string)
                elif distro == "slax":
                    string = re.sub(r'initrd=',
                                    r'from=/multibootusb/' + iso_basename(iso_link) + '/slax fromusb initrd=', string)
                elif distro == "knoppix":
                    string = re.sub(r'(append)',
                                    r'\1  knoppix_dir=/multibootusb/' + iso_basename(iso_link) + '/KNOPPIX',
                                    string)
                elif distro == "gentoo":
                    string = re.sub(r'append ',
                                    'append real_root=' + usb_disk + ' slowusb subdir=/multibootusb/' +
                                    iso_basename(iso_link) + '/ ', string, flags=re.I)
                elif distro == "systemrescuecd":
                    rows = []
                    subdir = '/multibootusb/' + iso_basename(iso_link) + '/'
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
                elif distro == "arch" or distro == "chakra":
                    string = re.sub(r'isolabel=\S*',
                                    'isodevice=/dev/disk/by-uuid/' + usb_uuid, string, flags=re.I)
                    string = re.sub(r'isobasedir=',
                                    'isobasedir=/multibootusb/' + iso_basename(iso_link) + '/', string, flags=re.I)
                    string = re.sub(r'ui gfxboot', '# ui gfxboot', string)  # Bug in the isolinux package
                    if 'manjaro' in string:
                        if not os.path.exists(os.path.join(usb_mount, '.miso')):
                            with open(os.path.join(usb_mount, '.miso'), "w") as f:
                                f.write('')
                elif distro == "suse" or distro == "opensuse":
                    if re.search(r'opensuse_12', string, re.I):
                        string = re.sub(r'append',
                                        'append loader=syslinux isofrom_system=/dev/disk/by-uuid/' + usb_uuid + ":/" +
                                        iso_name(iso_link), string, flags=re.I)
                    else:
                        string = re.sub(r'append',
                                        'append loader=syslinux isofrom_device=/dev/disk/by-uuid/' + usb_uuid +
                                        ' isofrom_system=/multibootusb/' + iso_basename(iso_link) + '/' + iso_name(iso_link),
                                        string, flags=re.I)
                elif distro == "pclinuxos":
                    string = re.sub(r'livecd=',
                                    'fromusb livecd=' + '/multibootusb/' + iso_basename(iso_link) + '/',
                                    string)
                    string = re.sub(r'prompt', '#prompt', string)
                    string = re.sub(r'ui gfxboot.com', '#ui gfxboot.com', string)
                    string = re.sub(r'timeout', '#timeout', string)
                elif distro == "porteus" or distro == "wifislax":
                    string = re.sub(r'initrd=',
                                    'from=' + '/multibootusb/' + iso_basename(iso_link) + ' initrd=', string)
                elif distro == "hbcd":
                    if not 'multibootusb' in string:
                        string = re.sub(r'/HBCD', '/multibootusb/' + iso_basename(iso_link) + '/HBCD', string)
                elif distro == "zenwalk":
                    string = re.sub(r'initrd=',
                                    'from=/multibootusb/' + iso_basename(iso_link) + '/' + iso_name(iso_link) + ' initrd=',
                                    string)
                elif distro == "mageialive":
                    string = re.sub(r'LABEL=\S*', 'LABEL=' + usb_label, string)
                elif distro == "antix":
                    string = re.sub(r'APPEND', 'image_dir=/multibootusb/' + iso_basename(iso_link), string)
                elif distro == "solydx":
                    string = re.sub(r'live-media-path=', 'live-media-path=/multibootusb/' + iso_basename(iso_link),
                                    string)
                elif distro == "salix-live":
                    string = re.sub(r'iso_path', '/multibootusb/' + iso_basename(iso_link) + '/' + iso_name(iso_link),
                                    string)

                config_file = open(cfg_file, "w")
                config_file.write(string)
                config_file.close()

    update_mbusb_cfg_file(iso_link, usb_uuid, usb_mount, distro)


def update_mbusb_cfg_file(iso_link, usb_uuid, usb_mount, distro):
    """
    Update main multibootusb suslinux.cfg file after distro is installed.
    :return:
    """
    print('Updating multibootusb config file...')
    sys_cfg_file = os.path.join(usb_mount, "multibootusb", "syslinux.cfg")
    install_dir = os.path.join(usb_mount, "multibootusb", iso_basename(iso_link))
    if os.path.exists(sys_cfg_file):

        if distro == "hbcd":
            if os.path.exists(os.path.join(usb_mount, "multibootusb", "menu.lst")):
                _config_file = os.path.join(usb_mount, "multibootusb", "menu.lst")
                config_file = open(_config_file,"w")
                string = re.sub(r'/HBCD', '/multibootusb/' + iso_basename(iso_link) + '/HBCD', _config_file)
                config_file.write(string)
                config_file.close()

        elif distro == "Windows":
            if os.path.exists(sys_cfg_file):
                config_file = open(sys_cfg_file, "a")
                config_file.write("#start " + iso_basename(iso_link) + "\n")
                config_file.write("LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("MENU LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("KERNEL chain.c32 hd0 1 ntldr=/bootmgr" + "\n")
                config_file.write("#end " + iso_basename(iso_link) + "\n")
                config_file.close()
        elif distro == 'f4ubcd':
            if os.path.exists(sys_cfg_file):
                config_file = open(sys_cfg_file, "a")
                config_file.write("#start " + iso_basename(iso_link) + "\n")
                config_file.write("LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("MENU LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("KERNEL grub.exe" + "\n")
                config_file.write('APPEND --config-file=/multibootusb/' + iso_basename(config.iso_link) + '/menu.lst' + "\n")
                config_file.write("#end " + iso_basename(iso_link) + "\n")
                config_file.close()
        elif distro == 'kaspersky':
            if os.path.exists(sys_cfg_file):
                config_file = open(sys_cfg_file, "a")
                config_file.write("#start " + iso_basename(iso_link) + "\n")
                config_file.write("LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("MENU LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("CONFIG " + '/multibootusb/' + iso_basename(config.iso_link) + '/kaspersky.cfg' + "\n")
                config_file.write("#end " + iso_basename(iso_link) + "\n")
                config_file.close()
        else:
            # admin.adminCmd(["mount", "-o", "remount,rw", config.usb_disk])
            config_file = open(sys_cfg_file, "a")
            config_file.write("#start " + iso_basename(iso_link) + "\n")
            config_file.write("LABEL " + iso_basename(iso_link) + "\n")
            config_file.write("MENU LABEL " + iso_basename(iso_link) + "\n")
            if distro == "salix-live":
                config_file.write(
                    "LINUX " + '/multibootusb/' + iso_basename(iso_link) + '/boot/grub2-linux.img' + "\n")
            elif distro == "pclinuxos":
                config_file.write("kernel " + '/multibootusb/' + iso_basename(iso_link) + '/isolinux/vmlinuz' + "\n")
                config_file.write("append livecd=livecd root=/dev/rd/3 acpi=on vga=788 keyb=us vmalloc=256M nokmsboot "
                                  "fromusb root=UUID=" + usb_uuid + " bootfromiso=/multibootusb/" +
                                  iso_basename(iso_link) + "/" + iso_name(iso_link) + " initrd=/multibootusb/"
                                  + iso_basename(iso_link) + '/isolinux/initrd.gz' + "\n")
            elif distro == "mentest":
                config_file.write("kernel " + '/multibootusb/' + iso_basename(iso_link) + '/BOOT/MEMTEST.IMG\n')

            elif distro == "sgrubd2":
                config_file.write("LINUX memdisk\n")
                config_file.write("INITRD " + "/multibootusb/" + iso_basename(iso_link) + '/' + iso_name(iso_link) + '\n')
                config_file.write("APPEND iso\n")
            else:
                if distro == "generic":
                    distro_syslinux_install_dir = isolinux_bin_dir(iso_link)
                    if not isolinux_bin_dir(iso_link) == "/":
                        distro_sys_install_bs = os.path.join(usb_mount, isolinux_bin_dir(iso_link)) + '/' + distro + '.bs'
                    else:
                        distro_sys_install_bs = '/' + distro + '.bs'
                else:
                    distro_syslinux_install_dir = install_dir
                    distro_syslinux_install_dir = distro_syslinux_install_dir.replace(usb_mount, '')
                    distro_sys_install_bs = distro_syslinux_install_dir + '/' + isolinux_bin_dir(iso_link) + '/' + distro + '.bs'

                distro_sys_install_bs = "/" + distro_sys_install_bs.replace("\\", "/")  # Windows path issue.

                if config.syslinux_version == '3':
                    config_file.write("CONFIG /multibootusb/" + iso_basename(iso_link) + '/' + isolinux_bin_dir(iso_link).replace("\\", "/") + '/isolinux.cfg\n')
                    config_file.write("APPEND /multibootusb/" + iso_basename(iso_link) + '/' + isolinux_bin_dir(iso_link).replace("\\", "/") + '\n')
                else:
                    config_file.write("BOOT " + distro_sys_install_bs.replace("//", "/") + "\n")

            config_file.write("#end " + iso_basename(iso_link) + "\n")
            config_file.close()

    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            if f.endswith("isolinux.cfg") or f.endswith("ISOLINUX.CFG"):
                shutil.copy2(os.path.join(dirpath, f), os.path.join(dirpath, "syslinux.cfg"))

            '''
            else:
                if distro == "ubuntu" and config.sys_version == "6":
                    config_file.write("CONFIG " + "/multibootusb/" + iso_basename(iso_link) +
                                      "/isolinux/isolinux.cfg" + "\n")
                    config_file.write("APPEND " + "/multibootusb/" + iso_basename(iso_link) +
                                      "/isolinux" + "\n")
            '''

def kaspersky_config(distro):
    if distro == 'kaspersky':
        return """
menu label Kaspersky Rescue Disk
  kernel $INSTALL_DIR/boot/rescue
  append root=live:UUID= live_dir=$INSTALL_DIR/rescue/LiveOS/ subdir=$INSTALL_DIR/rescue/LiveOS/ looptype=squashfs rootfstype=auto vga=791 init=/linuxrc loop=$INSTALL_DIR/rescue/LiveOS/squashfs.img initrd=$INSTALL_DIR/boot/rescue.igz lang=en udev liveimg splash quiet doscsi nomodeset
label text
  menu label Kaspersky Rescue Disk - Text Mode
  kernel $INSTALL_DIR/boot/rescue
  append root=live:UUID= live_dir=$INSTALL_DIR/rescue/LiveOS/ subdir=$INSTALL_DIR/rescue/LiveOS/ rootfstype=auto vga=791 init=/linuxrc loop=/multiboot/rescue/LiveOS/squashfs.img initrd=$INSTALL_DIR/boot/rescue.igz SLUG_lang=en udev liveimg quiet nox shell noresume doscsi nomodeset
label hwinfo
  menu label Kaspersky Hardware Info
  kernel $INSTALL_DIR/boot/rescue
  append root=live:UUID= live_dir=$INSTALL_DIR/rescue/LiveOS/ subdir=$INSTALL_DIR/rescue/LiveOS/ rootfstype=auto vga=791 init=/linuxrc loop=$INSTALL_DIR/rescue/LiveOS/squashfs.img initrd=$INSTALL_DIR/boot/rescue.igz SLUG_lang=en udev liveimg quiet softlevel=boot nox hwinfo noresume doscsi nomodeset """
