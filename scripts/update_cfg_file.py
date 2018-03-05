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
from . import grub
from . import menus


def update_distro_cfg_files(iso_link, usb_disk, distro, persistence=0):
    """
    Main function to modify/update distro specific strings on distro config files.
    :return:
    """
    usb_details = details(usb_disk)
    usb_mount = usb_details['mount_point']
    usb_uuid = usb_details['uuid']
    usb_label = usb_details['label']
#     iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir")
    config.status_text = "Updating config files..."
    install_dir = os.path.join(usb_mount, "multibootusb", iso_basename(iso_link))
    log('Updating distro specific config files...')
    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            if f.endswith(".cfg") or f.endswith('.CFG') or f.endswith('.lst') or f.endswith('.conf'):
                cfg_file = os.path.join(dirpath, f)
                try:
                    string = open(cfg_file, errors='ignore').read()
                except IOError:
                    log("Unable to read ", cfg_file)
                else:
                    if not distro == "generic":
                        replace_text = r'\1/multibootusb/' + iso_basename(iso_link) + '/'
                        string = re.sub(r'([ \t =,])/', replace_text, string)
                        string = re.sub(r'linuxefi', 'linux', string)
                        string = re.sub(r'initrdefi', 'initrd', string)
                if distro == "ubuntu":
                    string = re.sub(r'boot=casper',
                                    'boot=casper cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid '
                                    'ignore_bootid root=UUID=' + usb_uuid + ' live-media-path=/multibootusb/'
                                    + iso_basename(iso_link) + '/casper', string)
                    # Point to correct .seed file
                    string = re.sub(r'/cdrom/preseed', '/preseed', string)
                    string = re.sub(r'live-media=\S*', 'live-media=/dev/disk/by-uuid/' + usb_uuid, string)
                    string = re.sub(r'ui gfxboot', '#ui gfxboot', string)
                    if persistence != 0:
                        string = re.sub(r'boot=casper', 'boot=casper persistent persistent-path=/multibootusb/' +
                                        iso_basename(iso_link) + "/", string)

                elif distro in ["debian", "debian-install"]:
                    string = re.sub(r'boot=live', 'boot=live ignore_bootid live-media-path=/multibootusb/' +
                                    iso_basename(iso_link) + '/live', string)
                    if persistence != 0:
                        string = re.sub(r'boot=live', 'boot=live persistent persistent-path=/multibootusb/' +
                                        iso_basename(iso_link) + "/", string)
                elif distro == 'grml':
                    string = re.sub(r'live-media-path=', 'ignore_bootid live-media-path=', string)
                elif distro == "ubuntu-server":
                    string = re.sub(r'file',
                                    'cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid ignore_bootid root=UUID=' +
                                    usb_uuid + ' file', string)
                elif distro == "fedora":
                    string = re.sub(r'root=\S*', 'root=live:UUID=' + usb_uuid, string)
                    if re.search(r'liveimg', string, re.I):
                        string = re.sub(r'liveimg', 'liveimg live_dir=/multibootusb/' +
                                        iso_basename(iso_link) + '/LiveOS', string)
                    elif re.search(r'rd.live.image', string, re.I):
                        string = re.sub(r'rd.live.image', 'rd.live.image rd.live.dir=/multibootusb/' +
                                        iso_basename(iso_link) + '/LiveOS', string)
                    elif re.search(r'Solus', string, re.I):
                        string = re.sub(r'initrd=', 'rd.live.dir=/multibootusb/' + iso_basename(iso_link) +
                                        '/LiveOS initrd=', string)

                    if persistence != 0:
                        if re.search(r'liveimg', string, re.I):
                            string = re.sub(r'liveimg', 'liveimg overlay=UUID=' + usb_uuid, string)
                        elif re.search(r'rd.live.image', string, re.I):
                            string = re.sub(r'rd.live.image', 'rd.live.image rw rd.live.overlay=UUID=' + usb_uuid, string)
                        string = re.sub(r' ro ', '', string)
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
                    string = re.sub(r'linux_64=\"', 'linux_64=\"/multibootusb/' + iso_basename(iso_link), string,
                                        flags=re.I)
                    string = re.sub(r'linux_32=\"', 'linux_32=\"/multibootusb/' + iso_basename(iso_link), string,
                                        flags=re.I)
                    string = re.sub(r'initrd_img=\"', 'initrd_img=\"/multibootusb/' + iso_basename(iso_link), string,
                                        flags=re.I)
                    string = re.sub(r'initrd_img32=\"', 'initrd_img32=\"/multibootusb/' + iso_basename(iso_link), string,
                                        flags=re.I)
                    string = re.sub(r'default_settings=\"', 'default_settings=\"directory=/multibootusb/' + iso_basename(iso_link) + ' ', string,
                                        flags=re.I)
                    string = re.sub(r'live_settings=\"', 'live_settings=\"directory=/multibootusb/' + iso_basename(iso_link) + ' ', string,
                                        flags=re.I)
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
                    if 'pmedia=cd' in string:
                        string = re.sub(r'pmedia=cd\S*',
                                        'pmedia=usbflash psubok=TRUE psubdir=/multibootusb/' + iso_basename(iso_link) + '/',
                                        string)
                    elif 'rootfstype' in string:
                        string = re.sub(r'rootfstype',
                                        'pmedia=usbflash psubok=TRUE psubdir=/multibootusb/' + iso_basename(iso_link) + '/ rootfstype',
                                        string)
                elif distro == "slax":
                    string = re.sub(r'initrd=',
                                    r'from=/multibootusb/' + iso_basename(iso_link) + '/slax fromusb initrd=', string)
                elif distro == "finnix":
                    string = re.sub(r'initrd=',
                                    r'finnixdir=/multibootusb/' + iso_basename(iso_link) + '/finnix initrd=', string)
                elif distro == "knoppix":
                    string = re.sub(r'initrd=', 'knoppix_dir=/multibootusb/' + iso_basename(iso_link) + '/KNOPPIX initrd=', string)
                elif distro == "gentoo":
                    string = re.sub(r'append ',
                                    'append real_root=' + usb_disk + ' slowusb subdir=/multibootusb/' +
                                    iso_basename(iso_link) + '/ ', string, flags=re.I)
                    string = re.sub(r'slowusb', 'slowusb loop=/multibootusb/' +
                                    iso_basename(iso_link) + '/liberte/boot/root-x86.sfs', string, flags=re.I)
                    string = re.sub(r'cdroot_hash=\S*', '', string, flags=re.I)

                elif distro == "systemrescuecd":
                    rows = []
                    subdir = '/multibootusb/' + iso_basename(iso_link)
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
                elif distro in ["arch", "chakra"]:
                    string = re.sub(r'isolabel=\S*',
                                    'isodevice=/dev/disk/by-uuid/' + usb_uuid, string, flags=re.I)
                    string = re.sub(r'isobasedir=',
                                    'isobasedir=/multibootusb/' + iso_basename(iso_link) + '/', string, flags=re.I)
                    string = re.sub(r'ui gfxboot', '# ui gfxboot', string)  # Bug in the isolinux package
                    if 'manjaro' in string:
                        if not os.path.exists(os.path.join(usb_mount, '.miso')):
                            with open(os.path.join(usb_mount, '.miso'), "w") as f:
                                f.write('')
                elif distro == "kaos":
                    string = re.sub(r'kdeosisolabel=\S*',
                                    'kdeosisodevice=/dev/disk/by-uuid/' + usb_uuid, string, flags=re.I)
                    string = re.sub(r'append',
                                    'append kdeosisobasedir=/multibootusb/' + iso_basename(iso_link) + '/kdeos/', string, flags=re.I)
                    string = re.sub(r'ui gfxboot', '# ui gfxboot', string)  # Bug in the isolinux package
                elif distro in ["suse", "opensuse"]:
                    if re.search(r'opensuse_12', string, re.I):
                        string = re.sub(r'append',
                                        'append loader=syslinux isofrom_system=/dev/disk/by-uuid/' + usb_uuid + ":/" +
                                        iso_name(iso_link), string, flags=re.I)
                    else:
                        string = re.sub(r'append',
                                        'append loader=syslinux isofrom_device=/dev/disk/by-uuid/' + usb_uuid +
                                        ' isofrom_system=/multibootusb/' + iso_basename(iso_link) + '/' + iso_name(iso_link),
                                        string, flags=re.I)
                elif distro == 'opensuse-install':
                    string = re.sub(r'splash=silent', 'splash=silent install=hd:/dev/disk/by-uuid/'
                                    + config.usb_uuid + '/multibootusb/' + iso_basename(iso_link), string)
                elif distro == "pclinuxos":
                    string = re.sub(r'livecd=',
                                    'fromusb livecd=' + '/multibootusb/' + iso_basename(iso_link) + '/',
                                    string)
                    string = re.sub(r'prompt', '#prompt', string)
                    string = re.sub(r'ui gfxboot.com', '#ui gfxboot.com', string)
                    string = re.sub(r'timeout', '#timeout', string)
                elif distro == "wifislax":
                    string = re.sub(r'vmlinuz',
                                    'vmlinuz from=multibootusb/' + iso_basename(iso_link) + ' noauto', string)
                    string = re.sub(r'vmlinuz2',
                                    'vmlinuz2 from=multibootusb/' + iso_basename(iso_link) + ' noauto', string)
                elif distro == "porteus":
                    string = re.sub(r'APPEND',
                                    'APPEND from=/multibootusb/' + iso_basename(iso_link) + ' noauto', string)
                    string = re.sub(r'vmlinuz2',
                                    'vmlinuz2 from=multibootusb/' + iso_basename(iso_link) + ' noauto', string)
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
                    string = re.sub(r'initrd', 'fromiso=/multibootusb/' + iso_basename(iso_link) + '/' +
                                    iso_name(iso_link) + ' initrd', string)
                elif distro == 'alt-linux':
                    string = re.sub(r':cdrom', ':disk', string)
                elif distro == 'fsecure':
                    string = re.sub(r'APPEND ramdisk_size', 'APPEND noprompt ' + 'knoppix_dir=/multibootusb/' + iso_basename(iso_link)
                                    + '/KNOPPIX ramdisk_size', string)
                elif distro == 'alpine':
                    string = re.sub(r'modules', 'alpine_dev=usbdisk:vfat modules', string)
                elif config.distro == 'trinity-rescue':
                    # USB disk must have volume label to work properly
                    string = re.sub(r'initrd=', 'vollabel=' + config.usb_label + ' initrd=', string)
                    string = re.sub(r'root=\S*', 'root=/dev/ram0', string, flags=re.I)

                config_file = open(cfg_file, "w")
                config_file.write(string)
                config_file.close()

    update_mbusb_cfg_file(iso_link, usb_uuid, usb_mount, distro)
    grub.mbusb_update_grub_cfg()

    # Ensure that isolinux.cfg file is copied as syslinux.cfg to boot correctly.
    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            if f.lower().endswith("isolinux.cfg"):
                if not os.path.exists(os.path.join(dirpath, "syslinux.cfg")):
                    try:
                        shutil.copyfile(os.path.join(dirpath, f), os.path.join(dirpath, "syslinux.cfg"))
                    except Exception as e:
                        log('Copying isolinux to syslinux failed...')
                        log(e)
                else:
                    continue

    # Assertain if the entry is made..
    sys_cfg_file = os.path.join(config.usb_mount, "multibootusb", "syslinux.cfg")
    if gen.check_text_in_file(sys_cfg_file, iso_basename(config.image_path)):
        log('Updated entry in syslinux.cfg...')
    else:
        log('Unable to update entry in syslinux.cfg...')

    # Check if bootx64.efi is replaced by distro
    efi_grub_img = os.path.join(config.usb_mount, 'EFI', 'BOOT', 'bootx64.efi')
    if not os.path.exists(efi_grub_img):
        gen.log('EFI image does not exist. Copying now...')
        shutil.copy2(resource_path(os.path.join("data", "EFI", "BOOT", "bootx64.efi")),
                                   os.path.join(config.usb_mount, 'EFI', 'BOOT'))
    elif gen.grub_efi_exist(efi_grub_img) is False:
        gen.log('EFI image overwritten by distro install. Replacing it now...')
        shutil.copy2(resource_path(os.path.join("data", "EFI", "BOOT", "bootx64.efi")),
                     os.path.join(config.usb_mount, 'EFI', 'BOOT'))
    else:
        gen.log('multibootusb EFI image already exist. Not copying...')


def update_mbusb_cfg_file(iso_link, usb_uuid, usb_mount, distro):
    """
    Update main multibootusb suslinux.cfg file after distro is installed.
    :return:
    """
    if platform.system() == 'Linux':
        os.sync()
    log('Updating multibootusb config file...')
    sys_cfg_file = os.path.join(usb_mount, "multibootusb", "syslinux.cfg")
    install_dir = os.path.join(usb_mount, "multibootusb", iso_basename(iso_link))
    if os.path.exists(sys_cfg_file):

        if distro == "hbcd":
            if os.path.exists(os.path.join(usb_mount, "multibootusb", "menu.lst")):
                _config_file = os.path.join(usb_mount, "multibootusb", "menu.lst")
                config_file = open(_config_file, "w")
                string = re.sub(r'/HBCD', '/multibootusb/' + iso_basename(iso_link) + '/HBCD', _config_file)
                config_file.write(string)
                config_file.close()
            with open(sys_cfg_file, "a") as f:
                f.write("#start " + iso_basename(config.image_path) + "\n")
                f.write("LABEL " + iso_basename(config.image_path) + "\n")
                f.write("MENU LABEL " + iso_basename(config.image_path) + "\n")
                f.write("BOOT " + '/multibootusb/' + iso_basename(iso_link) + '/' + isolinux_bin_dir(iso_link).replace("\\", "/") + '/' + distro + '.bs' + "\n")
                f.write("#end " + iso_basename(config.image_path) + "\n")
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
                config_file.write('APPEND --config-file=/multibootusb/' + iso_basename(config.image_path) + '/menu.lst' + "\n")
                config_file.write("#end " + iso_basename(iso_link) + "\n")
                config_file.close()
        elif distro == 'kaspersky':
            if os.path.exists(sys_cfg_file):
                config_file = open(sys_cfg_file, "a")
                config_file.write("#start " + iso_basename(iso_link) + "\n")
                config_file.write("LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("MENU LABEL " + iso_basename(iso_link) + "\n")
                config_file.write("CONFIG " + '/multibootusb/' + iso_basename(config.image_path) + '/kaspersky.cfg' + "\n")
                config_file.write("#end " + iso_basename(iso_link) + "\n")
                config_file.close()
        elif distro == 'grub4dos':
            update_menu_lst()
        elif distro == 'grub4dos_iso':
            update_grub4dos_iso_menu()
        else:
            config_file = open(sys_cfg_file, "a")
            config_file.write("#start " + iso_basename(iso_link) + "\n")
            config_file.write("LABEL " + iso_basename(iso_link) + "\n")
            config_file.write("MENU LABEL " + iso_basename(iso_link) + "\n")
            if distro == "salix-live":
                if os.path.exists(os.path.join(config.usb_mount, 'multibootusb', iso_basename(iso_link), 'boot', 'grub2-linux.img')):
                    config_file.write(
                        "LINUX " + '/multibootusb/' + iso_basename(iso_link) + '/boot/grub2-linux.img' + "\n")
                else:
                    config_file.write("BOOT " + '/multibootusb/' + iso_basename(iso_link) + '/' + isolinux_bin_dir(iso_link).replace("\\", "/") + '/' + distro + '.bs' + "\n")
            elif distro == "pclinuxos":
                config_file.write("kernel " + '/multibootusb/' + iso_basename(iso_link) + '/isolinux/vmlinuz' + "\n")
                config_file.write("append livecd=livecd root=/dev/rd/3 acpi=on vga=788 keyb=us vmalloc=256M nokmsboot "
                                  "fromusb root=UUID=" + usb_uuid + " bootfromiso=/multibootusb/" +
                                  iso_basename(iso_link) + "/" + iso_name(iso_link) + " initrd=/multibootusb/"
                                  + iso_basename(iso_link) + '/isolinux/initrd.gz' + "\n")
            elif distro == "memtest":
                config_file.write("kernel " + '/multibootusb/' + iso_basename(iso_link) + '/BOOT/MEMTEST.IMG\n')

            elif distro == "sgrubd2" or config.distro == 'raw_iso':
                config_file.write("LINUX memdisk\n")
                config_file.write("INITRD " + "/multibootusb/" + iso_basename(iso_link) + '/' + iso_name(iso_link) + '\n')
                config_file.write("APPEND iso\n")

            elif distro == 'ReactOS':
                config_file.write("COM32 mboot.c32" + '\n')
                config_file.write("APPEND /loader/setupldr.sys" + '\n')
            elif distro == 'pc-unlocker':
                config_file.write("kernel ../ldntldr" + '\n')
                config_file.write("append initrd=../ntldr" + '\n')
            elif distro == 'pc-tool':
                config_file.write(menus.pc_tool_config(syslinux=True, grub=False))
            elif distro == 'grub2only':
                config_file.write(menus.grub2only())
            elif distro == 'memdisk_iso':
                print(menus.memdisk_iso_cfg(syslinux=True, grub=False))
                config_file.write(menus.memdisk_iso_cfg(syslinux=True, grub=False))
            elif distro == 'memdisk_img':
                config_file.write(menus.memdisk_img_cfg(syslinux=True, grub=False))
            else:
                if isolinux_bin_exist(config.image_path) is True:
                    if distro == "generic":
                        distro_syslinux_install_dir = isolinux_bin_dir(iso_link)
                        if isolinux_bin_dir(iso_link) != "/":
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
                        config_file.write("# Delete or comment above two lines using # and remove # from below line if "
                                          "you get not a COM module error.\n")
                        config_file.write("#BOOT " + distro_sys_install_bs.replace("//", "/") + "\n")
                    else:
                        config_file.write("BOOT " + distro_sys_install_bs.replace("//", "/") + "\n")

            config_file.write("#end " + iso_basename(iso_link) + "\n")
            config_file.close()
            # Update extlinux.cfg file by copying updated syslinux.cfg
            shutil.copy(os.path.join(usb_mount, 'multibootusb', 'syslinux.cfg'),
                        os.path.join(usb_mount, 'multibootusb', 'extlinux.cfg'))


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


def update_menu_lst():
    sys_cfg_file = os.path.join(config.usb_mount, "multibootusb", "syslinux.cfg")
#     install_dir = os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path))
    menu_lst = iso_menu_lst_path(config.image_path).replace("\\", "/")
    with open(sys_cfg_file, "a") as f:
        f.write("#start " + iso_basename(config.image_path) + "\n")
        f.write("LABEL " + iso_basename(config.image_path) + "\n")
        f.write("MENU LABEL " + iso_basename(config.image_path) + "\n")
        f.write("KERNEL grub.exe" + "\n")
        f.write('APPEND --config-file=/' + menu_lst + "\n")
        f.write("#end " + iso_basename(config.image_path) + "\n")


def update_grub4dos_iso_menu():
        sys_cfg_file = os.path.join(config.usb_mount, "multibootusb", "syslinux.cfg")
        install_dir = os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path))
        menu_lst_file = os.path.join(install_dir, 'menu.lst')
        with open(menu_lst_file, "w") as f:
            f.write("title Boot " + iso_name(config.image_path) + "\n")
            f.write("find --set-root --ignore-floppies --ignore-cd /multibootusb/" + iso_basename(config.image_path) + '/'
                    + iso_name(config.image_path) + "\n")
            f.write("map --heads=0 --sectors-per-track=0 /multibootusb/" + iso_basename(config.image_path)
                    + '/' + iso_name(config.image_path) + ' (hd32)' + "\n")
            f.write("map --hook" + "\n")
            f.write("chainloader (hd32)")

        with open(sys_cfg_file, "a") as f:
            f.write("#start " + iso_basename(config.image_path) + "\n")
            f.write("LABEL " + iso_basename(config.image_path) + "\n")
            f.write("MENU LABEL " + iso_basename(config.image_path) + "\n")
            f.write("KERNEL grub.exe" + "\n")
            f.write('APPEND --config-file=/multibootusb/' + iso_basename(config.image_path) + '/menu.lst'  + "\n")
            f.write("#end " + iso_basename(config.image_path) + "\n")
