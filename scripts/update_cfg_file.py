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
from functools import partial

from .usb import *
from .gen import *
from .iso import *
from . import config
from . import grub
from . import menus

from .param_rewrite import add_tokens, remove_tokens, replace_token, \
    add_or_replace_kv, replace_kv, remove_keys, \
    always, contains_token, contains_all_tokens, contains_any_token, \
    contains_key, contains_all_keys, contains_any_key, starter_is_either, _not


def dont_require_tweaking(fname, content, match_start, match_end):
    # Avoid fixing a path on a comment line
    beginning_of_line = content.rfind('\n', 0, match_start)
    if beginning_of_line<0:
        beginning_of_line = 0
    if content[beginning_of_line:match_start].lstrip()[:1]=='#':
        return True
    if fname.startswith(('cdrom/', 'dev/')):
        return True
    if (4 <= match_start and # Don't write an arg of 'init=' param.
        content[match_start-4:match_start+1] == 'init='):
        return True

def fix_abspath_r(pattern, string, install_dir, iso_name, kept_paths):
    """Return a list of tuples consisting of 'string' with replaced path and a bool representing if /boot/ was prepended in the expression."""
    m = pattern.search(string)
    if not m:
        return [(string, False)]
    start, end = m.span()
    prologue, specified_path = m.group(1), m.group(2)

    if dont_require_tweaking(specified_path, string, start, end):
        return [(string[:start] + prologue + '/' + specified_path,
                 '/%s is kept as is.' % specified_path)] \
                + fix_abspath_r(pattern, string[end:], install_dir, iso_name,
                                kept_paths)

    # See if a path that has 'boot/' prepended is a better choice.
    # E.g. Debian debian-live-9.4.0-amd64-cinnamon has a loopback.cfg
    # which contains "source /grub/grub.cfg".
    specified_path_exists = os.path.exists(
        os.path.join(install_dir, specified_path))
    if specified_path_exists:
        # Confidently accept what is specified.
        selected_path, fixed = specified_path, False
    elif os.path.exists(os.path.join(install_dir, 'boot', specified_path)):
        selected_path, fixed = ('boot/' + specified_path,
                                "Prepended '/boot/' to %s" % specified_path)
    # A path specified by 'preseed/file=' or 'file=' is utilized
    # after OS boots up. Doing this for grub is moot.
    #elif specified_path.startswith('cdrom/') and \
    #     os.path.exists(os.path.join(install_dir, # len('cdrom/') => 6
    #                                 specified_path[6:])):
    #    # See /boot/grub/loopback.cfg in 
    #    # ubuntu-14.04.5-desktop-amd64.iso for an example of this case.
    #    selected_path, fixed = specified_path[6:], "Removed '/cdrom/'"
    elif specified_path.endswith('.efi') and \
         os.path.exists(os.path.join(install_dir, specified_path[:-4])):
        # Avira-RS provides boot/grub/loopback.cfg which points
        # to non-existent /boot/grub/vmlinuz.efi.
        selected_path, fixed = (specified_path[:-4],
                                "Removed '.efi' from %s" % specified_path)
    else:
        # Reluctantly accept what is specified.
        if specified_path not in kept_paths:
            kept_paths.append(specified_path)
        selected_path, fixed = specified_path, False

    out = string[:start] + prologue + '/multibootusb/' + iso_name + '/' \
          + selected_path.replace('\\', '/')
    return [(out, fixed)] \
        + fix_abspath_r(pattern, string[end:], install_dir, iso_name,
                        kept_paths)

def fix_abspath(string, install_dir, iso_name, config_fname):
    """Rewrite what appear to be a path within 'string'. If a file does not exist with specified path, one with '/boot' prepended is tried."""

    path_expression = re.compile(r'([ \t=,])/(.*?)((?=[,|\s*])|$)')
    kept_paths = []
    chunks = fix_abspath_r(
        path_expression, string, install_dir, iso_name,  kept_paths)
    if len(kept_paths)==1:
        log("In '%s', '/%s' is kept as is though it does not exist."
            % (config_fname, kept_paths[0]))
    elif 2<=len(kept_paths):
        log("In '%s', "
            "following paths are used as they are though they don't exist."
            % config_fname)
        for kept_path in kept_paths:
            log('  /' + kept_path)
    tweaked_chunks = [c for c in chunks if c[1]]
    if len(tweaked_chunks) == 0:
        # Fallback to the legacy implementation so that
        # this tweak brings as little breakage as possible.
        replace_text = r'\1/multibootusb/' + iso_name + '/'
        return re.sub(r'([ \t =,])/', replace_text, string)
    else:
        log("Applied %s on '%s' as shown below:" %
            (len(tweaked_chunks)==1 and 'a rewrite exception' or
             ('%d rewrite exceptions' % len(tweaked_chunks)), config_fname))
        count_dict = {}
        for path, op_desc in tweaked_chunks:
            count_dict.setdefault(op_desc, []).append((path,op_desc))
        for op_desc, sub_chunks in count_dict.items():
            log("  %s [%d]" % (op_desc, len(sub_chunks)))
        return ''.join([c[0] for c in chunks])

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
    _iso_name = iso_basename(iso_link)
    install_dir = os.path.join(usb_mount, "multibootusb", _iso_name)
    install_dir_for_grub = '/multibootusb/%s' % _iso_name
    log('Updating distro specific config files...')

    tweaker_params = ConfigTweakerParam(
        _iso_name, install_dir_for_grub,
        persistence, usb_uuid, usb_mount, usb_disk)
    tweaker_class_dict = {
        'ubuntu'         : UbuntuConfigTweaker,
        'debian'         : DebianConfigTweaker,
        'debian-install' : DebianConfigTweaker,
        'gentoo'         : GentooConfigTweaker,
        'centos'         : CentosConfigTweaker,
        'centos-install' : CentosConfigTweaker,
        'antix'          : AntixConfigTweaker,
        }
    tweaker_class = tweaker_class_dict.get(distro)

    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            if f.endswith(".cfg") or f.endswith('.CFG') or f.endswith('.lst') or f.endswith('.conf'):
                cfg_file = os.path.join(dirpath, f)
                try:
                    string = open(cfg_file, errors='ignore').read()
                except IOError:
                    log("Unable to read %s" % cfg_file)
                else:
                    if not distro == "generic":
                        string = fix_abspath(string, install_dir, _iso_name,
                                             os.path.join(dirpath, f))
                        string = re.sub(r'linuxefi', 'linux', string)
                        string = re.sub(r'initrdefi', 'initrd', string)
                if tweaker_class:
                    tweaker = tweaker_class(distro, tweaker_params)
                    string = tweaker.tweak(string)

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
                    string = string.replace('%INSTALL_DIR%', 'arch')
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
                elif distro == "solydx":
                    string = re.sub(r'live-media-path=', 'live-media-path=/multibootusb/' + iso_basename(iso_link),
                                    string)
                elif distro == "salix-live":
                    string = re.sub(r'iso_path', '/multibootusb/' + iso_basename(iso_link) + '/' + iso_name(iso_link),
                                    string)
                    string = re.sub(r'initrd=',
                                    'fromiso=/multibootusb/'
                                    + iso_basename(iso_link) + '/'
                                    + iso_name(iso_link) + ' initrd=', string)
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

    # copy isolinux.cfg file to syslinux.cfg for grub to boot.
    def copy_to_syslinux_cfg_callback(dir_, fname):
        if not fname.lower().endswith('isolinux.cfg'):
            return
        isolinux_cfg_path = os.path.join(dir_, fname)
        syslinux_cfg_fname = fname.replace('isolinux.cfg','syslinux.cfg')
        syslinux_cfg_path = os.path.join(dir_, syslinux_cfg_fname)
        if os.path.exists(syslinux_cfg_path):
            return # don't overwrite.
        try:
            shutil.copyfile(isolinux_cfg_path, syslinux_cfg_path)
        except Exception as e:
            log('Copying %s %s to %s failed...' % (
                fname, dir_, syslinux_cfg_fname))
            log(e)

    def fix_desktop_image_in_thema_callback(install_dir_for_grub,
                                            dir_, fname):
        if fname.lower() != 'theme.txt':
            return
        log("Probing '%s'!" % fname)
        theme_file = os.path.join(dir_, fname)
        with open(theme_file, 'r') as f:
            lines = []
            pattern = re.compile(r'^desktop-image\s*:\s*(.*)$')
            for line in f.readlines():
                line = line.rstrip()
                m = pattern.match(line)
                if m and m.group(1)[:1]=='/':
                    log("Updating '%s'" % line)
                    partial_path = m.group(1).strip('"').lstrip('/')
                    line = 'desktop-image: "%s/%s"' % \
                           (install_dir_for_grub, partial_path)
                lines.append(line)
        with open(theme_file, 'w') as f:
            f.write('\n'.join(lines))

    visitor_callbacks = [
        # Ensure that isolinux.cfg file is copied as syslinux.cfg
        # to boot correctly.
        copy_to_syslinux_cfg_callback,

        # Rewrite 'desktop-image: ...' line in a theme definition file
        # so that a background image is displaymed during boot item selection.
        # This tweak was first introduced for kali-linux-light-2018-1.
        partial(fix_desktop_image_in_thema_callback, install_dir_for_grub),
    ]
    # Now visit the tree.
    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            for callback in visitor_callbacks:
                callback(dirpath, f)


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
        sys_cfg_file = os.path.join(config.usb_mount, "multibootusb",
                                    "syslinux.cfg")
        install_dir = os.path.join(config.usb_mount, "multibootusb",
                                   iso_basename(config.image_path))
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

class ConfigTweakerParam:
    def __init__(self, distro_name, distro_path, persistence_size, 
                 usb_uuid, usb_mount, usb_disk):
        self.distro_name = distro_name
        assert distro_path[0] == '/'
        self.distro_path = distro_path           # drive relative
        self.persistence_size = persistence_size
        self.usb_uuid = usb_uuid
        self.usb_mount = usb_mount
        self.usb_disk = usb_disk


class ConfigTweaker:

    BOOT_PARAMS_STARTER = 'kernel|append|linux'

    def __init__(self, distro_type, setup_params):
        self.disto_type = distro_type
        self.setup_params = setup_params

    def tweak_first_match(self, content, kernel_param_line_pattern,
                          apply_persistence_to_all_lines,
                          param_operations,
                          param_operations_for_persistence):
        """Perofrm specified parameter modification to the first maching
        line and return the concatination of the string leading up to the
        match and the tweaked paramer line. If no match is found,
        unmodified 'content' is returned.
        """
        m = kernel_param_line_pattern.search(content)
        if m is None:
            return content

        start, end = m.span()
        upto_match, rest_of_content = content[:start], content[end:]
        starter_part, starter_token, params_part = [
            m.group(i) for i in [1,2,3]]
        params = params_part.split(' ')
        if apply_persistence_to_all_lines or \
          self.has_persistency_param(params):
            ops_to_apply = param_operations + \
              param_operations_for_persistence
        else:
            ops_to_apply = param_operations
        for op_or_op_list, precondition in ops_to_apply:
            if not precondition(starter_token, params):
                continue
            try:
                iter(op_or_op_list)
                op_list = op_or_op_list
            except TypeError:
                op_list = [op_or_op_list]
            for op in op_list:
                params = op(params)

        # I see something special about this param. Place it at the end.
        three_dashes = '---'
        if three_dashes in params:
            params.remove(three_dashes)
            params.append(three_dashes)

        return upto_match + starter_part + ' '.join(params) + \
               self.tweak_first_match(
                   rest_of_content, kernel_param_line_pattern,
                   apply_persistence_to_all_lines,
                   param_operations, param_operations_for_persistence)

    def tweak(self, content):
        apply_persistence_to_all_lines = \
            0 < self.setup_params.persistence_size and \
            not self.config_is_persistence_aware(content)
        matching_re = r'^(\s*(%s)\s*)(.*)$' % self.BOOT_PARAMS_STARTER
        kernel_parameter_line_pattern = re.compile(
            matching_re,
            flags = re.I | re.MULTILINE)
        out = self.tweak_first_match(
            content,
            kernel_parameter_line_pattern,
            apply_persistence_to_all_lines,
            self.param_operations(),
            self.param_operations_for_persistence())
        
        return self.post_process(out)

    def on_liveboot_params(self, starter, params):
        return self.LIVE_BOOT_DETECT_PARAM in params

    def post_process(self, entire_string):
        return entire_string

    def add_op_if_file_exists(self, op_list, op_creator_func, key,
                              candidate_relative_path_list, predicate):
        for candidate in candidate_relative_path_list:
            relpath = os.path.join(self.setup_params.distro_path[1:],
                                    candidate)
            if os.path.exists(os.path.join(
                    self.setup_params.usb_mount, relpath)):
                normalized_relpath = '/' + relpath.replace('\\','/')
                op_list.append((op_creator_func(key, normalized_relpath),
                                predicate))
                break

    def fullpath(self, subpath):
        p = self.setup_params
        return os.path.join(p.usb_mount, p.distro_path[1:], subpath)

    def file_is_installed(self, subpath):
        return os.path.exists(self.fullpath(subpath))

    def file_content(self, subpath):
        fp = self.fullpath(subpath)
        if not os.path.exists(fp):
            return None
        with open(fp, errors='ignore') as f:
            return f.read()


class PersistenceConfigTweaker(ConfigTweaker):
    def __init__(self, pac_re, *args, **kw):
        self.persistence_awareness_checking_re = pac_re
        super(PersistenceConfigTweaker, self).__init__(*args, **kw)

    def config_is_persistence_aware(self, content):
        """ Used to restrict update of boot parameters to persistent-aware
        menu entries if the distribution provides any.
        """
        return self.persistence_awareness_checking_re.search(content) \
            is not None


class ConfigTweakerWithDebianStylePersistenceParam(PersistenceConfigTweaker):
    def __init__(self, *args, **kw):
        persistence_awareness_checking_re = re.compile(
            r'^\s*(%s).*?\s%s(\s.*|)$' % \
            (self.BOOT_PARAMS_STARTER, self.PERSISTENCY_TOKEN),
            flags=re.I|re.MULTILINE)
        super(ConfigTweakerWithDebianStylePersistenceParam,
              self).__init__(persistence_awareness_checking_re, *args, **kw)

    def has_persistency_param(self, params):
        return self.PERSISTENCY_TOKEN in params
    
    def param_operations_for_persistence(self):
        return [
            ([add_tokens(self.PERSISTENCY_TOKEN),
              add_or_replace_kv('%s-path=' % self.PERSISTENCY_TOKEN,
                                self.setup_params.distro_path)],
             self.on_liveboot_params)]


class UbuntuConfigTweaker(ConfigTweakerWithDebianStylePersistenceParam):
    LIVE_BOOT_DETECT_PARAM = 'boot=casper'
    PERSISTENCY_TOKEN = 'persistent'

    def param_operations(self):
        return [
            ([add_tokens('ignore_bootid'),
              add_or_replace_kv('live-media-path=',
                                '%s/casper' % self.setup_params.distro_path),
              add_or_replace_kv('cdrom-detect/try-usb=', 'true'),
            # Recently, correct param seems to be 'floppy=0,allowed_driver_mask
              add_or_replace_kv('floppy.allowed_drive_mask=', '0'),
              add_tokens('ignore_uuid'),
              add_or_replace_kv('root=UUID=', self.setup_params.usb_uuid),
              ],
             self.on_liveboot_params),
            (replace_kv('live-media=',
                        '/dev/disk/by-uuid/%s' % self.setup_params.usb_uuid),
             always),
            ]
    def post_process(self, entire_string):
        return entire_string.replace(r'ui gfxboot', '#ui gfxboot')


class DebianConfigTweaker(ConfigTweakerWithDebianStylePersistenceParam):

    LIVE_BOOT_DETECT_PARAM = 'boot=live'
    PERSISTENCY_TOKEN = 'persistence'

    def param_operations(self):
        return [
            (add_tokens('ignore_bootid'), self.on_liveboot_params),
            (add_or_replace_kv('live-media-path=',
                               '%s/live' % self.setup_params.distro_path),
             self.on_liveboot_params),
            ]

class NoPersistenceTweaker(ConfigTweaker):

    def config_is_persistence_aware(self, content):
        return False

    def param_operations_for_persistence(self):
        return []

    def has_persistency_param(self, params):
        return False
    
class GentooConfigTweaker(NoPersistenceTweaker):

    def param_operations(self):
        ops = [
            ([add_or_replace_kv('real_root=', self.setup_params.usb_disk),
              add_tokens('slowusb'),
              add_or_replace_kv('subdir=', self.setup_params.distro_path),
              remove_keys('cdroot_hash='),

              # Without this, pentoo-amd64-hardened-2018.0_RC5.8_pre20180305/
              # stucks at "copying read-write image contents to tmpfs"
              add_tokens('overlayfs'),

              # Said distro fails to mount root device if this param is given
              remove_tokens('aufs'),
              ],
             starter_is_either('append', 'linux')),
            ]
        self.add_op_if_file_exists(
            ops, add_or_replace_kv,
            'loop=', ['liberte/boot/root-x86.sfs', 'image.squashfs'],
            starter_is_either('append', 'linux'))
        return ops


class CentosConfigTweaker(PersistenceConfigTweaker):

    def __init__(self, *args, **kw):
        persistence_awareness_checking_re = re.compile(
            r'^\s*(%s).*?\s(rd.live.overlay|overlay)=.+?' %
            self.BOOT_PARAMS_STARTER,  flags=re.I|re.MULTILINE)
        super(CentosConfigTweaker, self).__init__(
            persistence_awareness_checking_re, *args, **kw)

    def has_persistency_param(self, params):
        return any(p.startswith(('overlay=', 'rd.live.overlay='))
                   for p in params)

    def param_operations(self):
        uuid_spec = 'UUID=%s' % self.setup_params.usb_uuid
        escaped_distro_path = self.setup_params.distro_path \
          .replace(' ', '\\0x20')
        live_path = escaped_distro_path + '/LiveOS'
        ops = [(replace_kv('inst.stage2=', 'hd:%s:%s' %
                           (uuid_spec, escaped_distro_path)), always),
               (add_or_replace_kv('inst.repo=',
                                   'http://mirror.centos.org'
                                   '/centos/7/os/x86_64/'),
                contains_key('inst.stage2=')),
               (replace_kv('root=', 'live:' + uuid_spec), always),
               (add_or_replace_kv('rd.live.dir=', live_path),
                contains_any_token('rd.live.image', 'Solus')),
               (add_or_replace_kv('live_dir=', live_path),
                contains_token('liveimage')), ]

        if self.file_is_installed('.treeinfo'):
            # Add or replace value of 'inst.repo=' with reference
            # to the copied iso.
            ops.append(
                 (add_or_replace_kv(
                     'inst.repo=',
                     'hd:UUID=%s:%s' % (
                        self.setup_params.usb_uuid,
                        self.setup_params.distro_path + '/' +
                        self.setup_params.distro_name + '.iso')),
                  starter_is_either('append', 'linux')))
        return ops

    def param_operations_for_persistence(self):
        uuid_spec = 'UUID=%s' % self.setup_params.usb_uuid
        return [
            (remove_tokens('ro'), always),
            (add_or_replace_kv('overlay=', uuid_spec),
             contains_token('liveimage')),
            ([add_tokens('rw'),
              add_or_replace_kv('rd.live.overlay=', uuid_spec)],
             contains_token('rd.live.image'))
            ]

class AntixConfigTweaker(NoPersistenceTweaker):
    def param_operations(self):
        content = self.file_content('version')
        if content and 0 <= content.find('antiX-17'):
            ops = [
                add_or_replace_kv('buuid=', self.setup_params.usb_uuid),
                add_or_replace_kv('bdir=',
                                  self.setup_params.distro_path + '/antiX')]
        else:
            ops = add_or_replace_kv('image_dir=',
                                    self.setup_params.distro_path)

        return [(ops, starter_is_either('append', 'APPEND', 'linux'))]

    def post_process(self, entire_string):
        return entire_string.replace(
            r'UI gfxboot gfx-cpio readme.msg',
            r'UI gfxboot gfx-cpio.renamed_to_avoid_lockup readme.msg')


def test_tweak_objects():
    def os_path_exists(f):
        if f.endswith('liberte/boot/root-x86.sfs'):
            return False
        if f.endswith('image.squashfs'):
            return True
        return False
    saved = os.path.exists
    os.path.exists = os_path_exists
    try:
        _test_tweak_objects()
    finally:
        os.path.exists = saved


def _test_tweak_objects():

    usb_mount = 'L:'
    usb_disk  = 'L:'
    setup_params_no_persistence = ConfigTweakerParam(
        '{iso-name}', '/multibootusb/{iso-name}', 0,
        '{usb-uuid}', usb_mount, usb_disk)
    debian_tweaker = DebianConfigTweaker('debian', setup_params_no_persistence)
    ubuntu_tweaker = UbuntuConfigTweaker('ubuntu', setup_params_no_persistence)
    centos_tweaker = CentosConfigTweaker('centos', setup_params_no_persistence)

    # Test awareness on 'persistent'
    content = """
    append   boot=live foo baz=1  double-spaced ignore_bootid persistent more stuff""".lstrip()
    print ("Testing awareness on 'persistent' of ubuntu tweaker.")
    assert ubuntu_tweaker.config_is_persistence_aware(content)
    print ("Testing awareness on 'persistent' of debian tweaker.")
    assert not debian_tweaker.config_is_persistence_aware(content)

    content = """
    append   boot=live foo baz=1  double-spaced ignore_bootid persistence more stuff""".lstrip()
    print ("Testing awareness on 'persistence' of ubuntu tweaker.")
    assert not ubuntu_tweaker.config_is_persistence_aware(content)
    print ("Testing awareness on 'persistence' of debian tweaker.")
    assert debian_tweaker.config_is_persistence_aware(content)

    print ("Testing awareness on 'overlay=' of centos tweaker.")
    content = """
    append   boot=live foo baz=1 overlay=UUID:2234-1224 double-spaced ignore_bootid persistence more stuff""".lstrip()
    assert centos_tweaker.config_is_persistence_aware(content)

    print ("Testing awareness on 'rd.live.overlay=' of centos tweaker.")
    content = """
    append   boot=live foo baz=1 rd.live.overlay=UUID:2234-1224 double-spaced ignore_bootid persistence more stuff""".lstrip()
    assert centos_tweaker.config_is_persistence_aware(content)

    print ("Testing indefference on persistence keys of centos tweaker.")
    content = """
    append   boot=live foo baz=1  double-spaced ignore_bootid persistence more stuff""".lstrip()
    assert not centos_tweaker.config_is_persistence_aware(content)

    print ("Testing awareness on 'overlay=' of centos tweaker.")
    content = """
    append   boot=live foo baz=1 double-spaced ignore_bootid persistence more stuff""".lstrip()
    assert not centos_tweaker.config_is_persistence_aware(content)

    print ("Testing if 'persistence' token is left at the original place.")
    content = "\tlinux\tfoo persistence boot=live in the middle"
    assert debian_tweaker.tweak(content) == "\tlinux\tfoo persistence boot=live in the middle ignore_bootid live-media-path=/multibootusb/{iso-name}/live persistence-path=/multibootusb/{iso-name}"""

    print ("Testing if 'boot=live' at the very end is recognized.")
    content = "menu\n\tlinux\tfoo persistence in the middle boot=live"
    assert debian_tweaker.tweak(content) == "menu\n\tlinux\tfoo persistence in the middle boot=live ignore_bootid live-media-path=/multibootusb/{iso-name}/live persistence-path=/multibootusb/{iso-name}"""

    print ("Testing if 'boot=live' at a line end is recognized.")
    content = """append zoo
\tappend\tfoo persistence in the middle boot=live
append foo"""
    assert debian_tweaker.tweak(content) == """append zoo
\tappend\tfoo persistence in the middle boot=live ignore_bootid live-media-path=/multibootusb/{iso-name}/live persistence-path=/multibootusb/{iso-name}
append foo"""

    print ("Testing if replacement of 'live-media=' happens on non-boot lines.")
    content = "\t\tlinux live-media=/tobe/replaced"
    assert ubuntu_tweaker.tweak(content)==\
        "\t\tlinux live-media=/dev/disk/by-uuid/{usb-uuid}"

    print ("Testing if \\tappend is recognized as a starter.")
    content = """\tappend  foo boot=live ignore_bootid persistence in the middle live-media-path=/foo/bar"""
    assert debian_tweaker.tweak(content) == """\tappend  foo boot=live ignore_bootid persistence in the middle live-media-path=/multibootusb/{iso-name}/live persistence-path=/multibootusb/{iso-name}"""

    print ("Testing if debian tweaker does not get tickled by 'persistent'.")
    content = """\tappend  boot=live foo ignore_bootid persistent in the middle live-media-path=/foo/bar"""
    assert debian_tweaker.tweak(content) == """\tappend  boot=live foo ignore_bootid persistent in the middle live-media-path=/multibootusb/{iso-name}/live"""

    print ("Testing replacement of 'live-media-path' value.")
    content = "  append boot=live foo live-media-path=/foo/bar more"
    assert debian_tweaker.tweak(content) == """  append boot=live foo live-media-path=/multibootusb/{iso-name}/live more ignore_bootid"""

    print ("Testing rewriting of 'file=' param by debian_tweaker.")
    content = "  kernel file=/cdrom/preseed/ubuntu.seed boot=live"

    setup_params_persistent = ConfigTweakerParam(
        'debian', '/multibootusb/{iso-name}', 128*1024*1024, '{usb-uuid}',
        usb_mount, usb_disk)
    debian_persistence_tweaker = DebianConfigTweaker(
        'debian', setup_params_persistent)
    ubuntu_persistence_tweaker = UbuntuConfigTweaker(
        'ubuntu', setup_params_persistent)
    centos_persistence_tweaker = CentosConfigTweaker(
        'centos', setup_params_persistent)

    print ("Testing if debian tweaker appends persistence parameters.")
    content = """label foo
  kernel foo bar
  append boot=live foo live-media-path=/foo/bar more
"""
    assert debian_persistence_tweaker.tweak(content) == """label foo
  kernel foo bar
  append boot=live foo live-media-path=/multibootusb/{iso-name}/live more ignore_bootid persistence persistence-path=/multibootusb/{iso-name}
"""

    print ("Testing if ubuntu tweaker selectively appends persistence params.")
    content = """label foo
      kernel foo bar
      append boot=casper foo live-media-path=/foo/bar more
    """
    assert ubuntu_persistence_tweaker.tweak(content) == """label foo
      kernel foo bar
      append boot=casper foo live-media-path=/multibootusb/{iso-name}/casper more ignore_bootid cdrom-detect/try-usb=true floppy.allowed_drive_mask=0 ignore_uuid root=UUID={usb-uuid} persistent persistent-path=/multibootusb/{iso-name}
    """

    # Test rewrite of persistence-aware configuration.
    # Only 'live-persistence' line should receive 'persistence-path'
    # parameter.
    print ("Testing if debian tweaker appends persistence params "
           "to relevant lines only.")
    content = """label live-forensic
        menu label Live (^forensic mode)
        linux /live/vmlinuz
        initrd /live/initrd.img
        append boot=live noconfig=sudo username=root hostname=kali noswap noautomount

label live-persistence
    menu label ^Live USB Persistence              (check kali.org/prst)
    linux /live/vmlinuz
    initrd /live/initrd.img
    append boot=live noconfig=sudo username=root hostname=kali persistence
"""
    assert debian_persistence_tweaker.tweak(content)=="""label live-forensic
        menu label Live (^forensic mode)
        linux /live/vmlinuz
        initrd /live/initrd.img
        append boot=live noconfig=sudo username=root hostname=kali noswap noautomount ignore_bootid live-media-path=/multibootusb/{iso-name}/live

label live-persistence
    menu label ^Live USB Persistence              (check kali.org/prst)
    linux /live/vmlinuz
    initrd /live/initrd.img
    append boot=live noconfig=sudo username=root hostname=kali persistence ignore_bootid live-media-path=/multibootusb/{iso-name}/live persistence-path=/multibootusb/{iso-name}
"""

    setup_params = ConfigTweakerParam(
        '{iso-name}', '/multibootusb/{iso-name}',
        0, '{usb-uuid}', usb_mount, usb_disk)
    gentoo_tweaker = GentooConfigTweaker('gentoo', setup_params)

    print ("Testing Gentoo-tweaker on syslinux config.")
    content = """label pentoo
menu label Pentoo Defaults (verify)
kernel /isolinux/pentoo
append initrd=/isolinux/pentoo.igz root=/dev/ram0 init=/linuxrc nox nodhcp overlayfs max_loop=256 dokeymap looptype=squashfs loop=/image.squashfs cdroot video=uvesafb:mtrr:3,ywrap,1024x768-16 usbcore.autosuspend=1 console=tty0 net.ifnames=0 scsi_mod.use_blk_mq=1 ipv6.autoconf=0 verify
"""

    assert gentoo_tweaker.tweak(content)=="""label pentoo
menu label Pentoo Defaults (verify)
kernel /isolinux/pentoo
append initrd=/isolinux/pentoo.igz root=/dev/ram0 init=/linuxrc nox nodhcp overlayfs max_loop=256 dokeymap looptype=squashfs loop=/multibootusb/{iso-name}/image.squashfs cdroot video=uvesafb:mtrr:3,ywrap,1024x768-16 usbcore.autosuspend=1 console=tty0 net.ifnames=0 scsi_mod.use_blk_mq=1 ipv6.autoconf=0 verify real_root=%s slowusb subdir=/multibootusb/{iso-name}
""" % usb_disk
    print ("Testing Gentoo-tweaker on grub config.")
    content = """insmod all_video

menuentry 'Boot LiveCD (kernel: pentoo)' --class gnu-linux --class os {
    linux /isolinux/pentoo root=/dev/ram0 init=/linuxrc  nox aufs max_loop=256 dokeymap looptype=squashfs loop=/image.squashfs  cdroot cdroot_hash=xxx
    initrd /isolinux/pentoo.igz
}
"""
    assert gentoo_tweaker.tweak(content)=="""insmod all_video

menuentry 'Boot LiveCD (kernel: pentoo)' --class gnu-linux --class os {
    linux /isolinux/pentoo root=/dev/ram0 init=/linuxrc  nox max_loop=256 dokeymap looptype=squashfs loop=/multibootusb/{iso-name}/image.squashfs  cdroot real_root=%s slowusb subdir=/multibootusb/{iso-name} overlayfs
    initrd /isolinux/pentoo.igz
}
""" % usb_disk

    print ("Testing centos tweaker on DVD-installer")
    saved = os.path.exists
    os.path.exists = lambda f: f.endswith('/.treeinfo') or saved(f)
    try:
        content = r"""label linux
  menu label ^Install CentOS 7
  kernel vmlinuz
  append initrd=initrd.img inst.stage2=hd:LABEL=CentOS\x207\x20x86_64 quiet
"""
        assert centos_tweaker.tweak(content)=="""label linux
  menu label ^Install CentOS 7
  kernel vmlinuz
  append initrd=initrd.img inst.stage2=hd:UUID={usb-uuid}:/multibootusb/{iso-name} quiet inst.repo=hd:UUID={usb-uuid}:/multibootusb/{iso-name}/{iso-name}.iso
"""
    finally:
        os.path.exists = saved

    print ("Testing centos tweaker on Net-installer")
    assert centos_tweaker.tweak(content)=="""label linux
  menu label ^Install CentOS 7
  kernel vmlinuz
  append initrd=initrd.img inst.stage2=hd:UUID={usb-uuid}:/multibootusb/{iso-name} quiet inst.repo=http://mirror.centos.org/centos/7/os/x86_64/
"""
    content = r"""label linux0
  menu label ^Start CentOS
  kernel vmlinuz0
  append initrd=initrd0.img root=live:CDLABEL=CentOS-7-x86_64-LiveGNOME-1708 rootfstype=auto ro rd.live.image quiet  rhgb rd.luks=0 rd.md=0 rd.dm=0
  menu default
"""
    print ("Testing centos tweaker on Live")
    assert centos_tweaker.tweak(content)=="""label linux0
  menu label ^Start CentOS
  kernel vmlinuz0
  append initrd=initrd0.img root=live:UUID={usb-uuid} rootfstype=auto ro rd.live.image quiet  rhgb rd.luks=0 rd.md=0 rd.dm=0 rd.live.dir=/multibootusb/{iso-name}/LiveOS
  menu default
"""

    print ("Testing persistent centos tweaker on non-persistence config.")
    content = r"""label linux0
  menu label ^Start CentOS
  kernel vmlinuz0
  append initrd=initrd0.img root=live:CDLABEL=CentOS-7-x86_64-LiveGNOME-1708 rootfstype=auto ro rd.live.image quiet  rhgb rd.luks=0 rd.md=0 rd.dm=0
  menu default
"""
    assert centos_persistence_tweaker.tweak(content)=="""label linux0
  menu label ^Start CentOS
  kernel vmlinuz0
  append initrd=initrd0.img root=live:UUID={usb-uuid} rootfstype=auto rd.live.image quiet  rhgb rd.luks=0 rd.md=0 rd.dm=0 rd.live.dir=/multibootusb/{iso-name}/LiveOS rw rd.live.overlay=UUID={usb-uuid}
  menu default
"""
    print ("Testing persistent centos tweaker not touching "
           "non-persistent line")
    content = r"""label linux0
  menu label ^Start CentOS
  append kenel=vmlinuz0
  append rd.live.overlay=UUID:2234-2223 ro rd.live.image
  append initrd=initrd0.img root=live:CDLABEL=CentOS-7-x86_64-LiveGNOME-1708 rootfstype=auto ro rd.live.image quiet  rhgb rd.luks=0 rd.md=0 rd.dm=0
  menu default
"""
    assert centos_persistence_tweaker.tweak(content)=="""label linux0
  menu label ^Start CentOS
  append kenel=vmlinuz0
  append rd.live.overlay=UUID={usb-uuid} rd.live.image rd.live.dir=/multibootusb/{iso-name}/LiveOS rw
  append initrd=initrd0.img root=live:UUID={usb-uuid} rootfstype=auto ro rd.live.image quiet  rhgb rd.luks=0 rd.md=0 rd.dm=0 rd.live.dir=/multibootusb/{iso-name}/LiveOS
  menu default
"""


def do_test_abspath_rewrite():

    content = """menuentry "Install Ubuntu" {
	linux	/casper/vmlinuz.efi  file=/cdrom/preseed/ubuntu.seed boot=casper only-ubiquity init=/linuxrc iso-scan/filename=${iso_path} quiet splash grub=/grub/grub.cfg ---
	initrd	/casper/initrd.lz
}"""
    assert fix_abspath(
        content, 'g:/multibootusb/ubuntu-14.04.5-desktop-amd64',
        'ubuntu-14.04.5-desktop-amd64', 'test_abspath_rewrite')==\
        """menuentry "Install Ubuntu" {
	linux	/multibootusb/ubuntu-14.04.5-desktop-amd64/casper/vmlinuz  file=/cdrom/preseed/ubuntu.seed boot=casper only-ubiquity init=/linuxrc iso-scan/filename=${iso_path} quiet splash grub=/multibootusb/ubuntu-14.04.5-desktop-amd64/boot/grub/grub.cfg ---
	initrd	/multibootusb/ubuntu-14.04.5-desktop-amd64/casper/initrd.lz
}"""


def test_abspath_rewrite():

    def os_path_exists(path):
        path = path.replace('\\', '/')
        if path.endswith('.efi'):
            return False
        if path.startswith('g:/multibootusb/ubuntu-14.04.5-desktop-amd64'
                           '/boot'):
            return True
        if path.endswith('/boot/grub/grub.cfg'):
            return True
        if path == '/grub/grub.cfg':
            return False
        if path.endswith('casper/vmlinuz'):
            return True
        if path.endswith('/casper/initrd.lz'):
            return True

        return False
    saved = os.path.exists
    try:
        os.path.exists = os_path_exists
        do_test_abspath_rewrite()
    finally:
        os.path.exists = saved
