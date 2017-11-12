#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Name:     grub.py
# Purpose:  This module contain many functions used for updating grub.cfg file to provide support for EFI/UEFI booting
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
import os
import re
from . import config
from . import iso
from . import _7zip
from . import gen
from .usb import bytes2human
from . import menus


def mbusb_update_grub_cfg():
    """
    Function to update grub.cfg file to support UEFI/EFI systems
    :return:
    """
    # Lets convert syslinux config file to grub2 accepted file format.
    _iso_dir = os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path))

    # First write custom loopback.cfg file so as to be detected by iso2grub2 function later.
    write_custom_gurb_cfg()

    # Try to generate loopback entry file from syslinux config files
    try:
        gen.log('Trying to create loopback.cfg')
        iso2_grub2_cfg = iso2grub2(_iso_dir)
    except Exception as e:
        print(e)
        gen.log(e)
        gen.log('Error converting syslinux cfg to grub2 cfg', error=True)
        iso2_grub2_cfg = False

    grub_cfg_path = None
    syslinux_menu = None
#     sys_cfg_path = None
    loopback_cfg_path = None
    mbus_grub_cfg_path = os.path.join(config.usb_mount, 'multibootusb', 'grub', 'grub.cfg')
#     iso_grub_cfg = iso.iso_file_path(config.image_path, 'grub.cfg')
    if iso.isolinux_bin_dir(config.image_path) is not False:
        iso_sys_cfg_path = os.path.join(iso.isolinux_bin_dir(config.image_path), 'syslinux.cfg')
        iso_iso_cfg_path = os.path.join(iso.isolinux_bin_dir(config.image_path), 'isolinux.cfg')

        if os.path.exists(os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path),
                                       iso_sys_cfg_path)):
            syslinux_menu = iso_sys_cfg_path.replace('\\', '/')
        elif os.path.exists(os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path),
                                         iso_iso_cfg_path)):
            syslinux_menu = iso_iso_cfg_path.replace('\\', '/')

    efi_grub_cfg = get_grub_cfg(config.image_path)
    boot_grub_cfg = get_grub_cfg(config.image_path, efi=False)
    loopback_cfg_path = iso.iso_file_path(config.image_path, 'loopback.cfg')

    if loopback_cfg_path is not False:
        grub_cfg_path = loopback_cfg_path.replace('\\', '/')
    elif efi_grub_cfg is not False:
        grub_cfg_path = efi_grub_cfg.replace('\\', '/')
    elif boot_grub_cfg is not False:
        grub_cfg_path = boot_grub_cfg.replace('\\', '/')
    elif iso2_grub2_cfg is not False:
        grub_cfg_path = iso2_grub2_cfg.replace('\\', '/')
    #elif bootx_64_cfg is not False:
    #    grub_cfg_path = bootx_64_cfg.replace('\\', '/')

    if os.path.exists(mbus_grub_cfg_path):
        gen.log('Updating grub.cfg file...')
        if grub_custom_menu(mbus_grub_cfg_path, config.distro) is False:
            with open(mbus_grub_cfg_path, 'a') as f:
                f.write("#start " + iso.iso_basename(config.image_path) + "\n")
                if grub_cfg_path is not None:
                    if  config.distro == 'grub2only':
                        f.write('     menuentry ' + iso.iso_basename(config.image_path) + ' {configfile '
                                + '/' + grub_cfg_path.replace('\\', '/') + '}' + "\n")
                    else:
                        f.write('     menuentry ' + iso.iso_basename(config.image_path) + ' {configfile '
                                + '/multibootusb/' + iso.iso_basename(config.image_path) + '/' + grub_cfg_path + '}' + "\n")
                elif config.distro == 'f4ubcd':
                    f.write('     menuentry ' + iso.iso_basename(config.image_path) +
                            ' {linux /multibootusb/grub.exe --config-file=/multibootusb' +
                            iso.iso_basename(config.image_path) + '/menu.lst}'"\n")
                elif config.distro == 'pc-unlocker':
                    f.write('     menuentry ' + iso.iso_basename(config.image_path) +
                            ' {\n    linux /ldntldr\n    ntldr /ntldr }' + "\n")
                elif config.distro == 'ReactOS':
                    f.write('     menuentry ' + iso.iso_basename(config.image_path) +
                            ' {multiboot /loader/setupldr.sys}' + "\n")
                elif config.distro == 'memdisk_img':
                    f.write(menus.memdisk_img_cfg(syslinux=False, grub=True))
                elif config.distro == 'memdisk_iso':
                    f.write(menus.memdisk_iso_cfg(syslinux=False, grub=True))
                elif config.distro == 'memtest':
                    f.write('     menuentry ' + iso.iso_basename(config.image_path) +
                            ' {linux16 ' + '/multibootusb/' + iso.iso_basename(config.image_path) + '/BISOLINUX/MEMTEST}' + "\n")
                elif syslinux_menu is not None:
                    f.write('     menuentry ' + iso.iso_basename(config.image_path) + ' {syslinux_configfile '
                            + '/multibootusb/' + iso.iso_basename(config.image_path) + '/' + syslinux_menu + '}' + "\n")
                f.write("#end " + iso.iso_basename(config.image_path) + "\n")

    # Ascertain if the entry is made..
    if gen.check_text_in_file(mbus_grub_cfg_path, iso.iso_basename(config.image_path)):
        gen.log('Updated entry in grub.cfg...')
    else:
        gen.log('Unable to update entry in grub.cfg...')


def write_custom_gurb_cfg():
    """
    Create custom grub loopback.cfg file for known distros. Custom menu entries are stored on munus.py module
    :return: 
    """
    loopback_cfg_path = os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path), 'loopback.cfg')
    menu = False
    if config.distro == 'pc-tool':
        menu = menus.pc_tool_config(syslinux=False, grub=True)
    elif config.distro == 'rising-av':
        menu = menus.rising(syslinux=False, grub=True)

    if menu is not False:
        gen.log('Writing custom loopback.cfg file...')
        write_to_file(loopback_cfg_path, menu)


def get_grub_cfg(iso_link, efi=True):
    """
    Detects path to "grub.cfg" file from ISO file. Default is to get from EFI directory.
    :return: path of "grub.cfg" file as string.
    """
    if os.path.exists(iso_link):
        grub_path = False
        iso_file_list = _7zip.list_iso(iso_link)
        if any("grub" in s.lower() for s in iso_file_list):
            for f in iso_file_list:
                f_basename = os.path.basename(f).lower()
                if f_basename.startswith('grub') and f_basename.endswith('.cfg'):
                #if 'grub.cfg' in f.lower():
                    if efi is True:
                        if 'efi' in f.lower():
                            grub_path = f.replace('\\', '/')
                            gen.log('Found ' + grub_path)
                            break
                        elif 'boot' in f.lower():
                            grub_path = f.replace('\\', '/')
                            gen.log('Found ' + grub_path)
                            break
                        else:
                            grub_path = f.replace('\\', '/')
                            gen.log('Found ' + grub_path)
                            break
        return grub_path


def grub_custom_menu(mbus_grub_cfg_path, distro):
    iso_size_mb = bytes2human(iso.iso_size(config.image_path))
    gen.log('size of the ISO is ' + str(iso_size_mb))
    if distro in ['sgrubd2', 'raw_iso']:
        grub_raw_iso(mbus_grub_cfg_path)

#         with open(mbus_grub_cfg_path, 'a') as f:
#             f.write("#start " + iso.iso_basename(config.image_path) + "\n")
#             f.write(grub_raw_iso())
#             f.write("#end " + iso.iso_basename(config.image_path) + "\n")
#
#
#     elif iso_size_mb < 750.0:
#         grub_raw_iso(mbus_grub_cfg_path)

    else:
        return False


def grub_raw_iso(mbus_grub_cfg_path):
    """
    Generic menu entry for booting ISO files directly using memdisk. Should have enough memory to load to RAM
    :return:
    """
    menu_entry = '    search --set -f /multibootusb/' + iso.iso_basename(config.image_path) + '/' + iso.iso_name(config.image_path) + '\n' \
                 '    menuentry ' + iso.iso_basename(config.image_path) + ' {\n' \
                 '    linux16 /multibootusb/memdisk iso raw vmalloc=750M\n' \
                 '    initrd16 /multibootusb/' + iso.iso_basename(config.image_path) + '/' + iso.iso_name(config.image_path) + '\n' \
                 '}\n'
    with open(mbus_grub_cfg_path, 'a') as f:
        f.write("#start " + iso.iso_basename(config.image_path) + "\n")
        f.write(menu_entry)
        f.write("#end " + iso.iso_basename(config.image_path) + "\n")
    return menu_entry


def string_in_file(_file, search_text):
    """
    Search if string exist in a file.
    :param _file: Path to file
    :param search_text: String to be searched
    :return: True if string is found
    """
    if search_text in open(_file).read().lower():
        return True


def write_to_file(file_path, _strings):

    try:
        if not os.path.exists(file_path):
            open(file_path, 'a').close()

        with open(file_path, 'a') as f:
            f.write(_strings + '\n')
    except:
        gen.log('Error writing to loopback.cfg file..')


def extract_kernel_line(search_text, match_line, isolinux_dir):
    """
    Function to check if kernel/linux line present in isolinux.cfg file is valid.
    If valid, then convert them in to grub accepted format
    :param search_text: Type of text is to be searched. Typically kernel or linux
    :param match_line: Line containing kernel ot linux from isolinux supported .cfg files
    :param isolinux_dir: Path to isolinux directory of an ISO
    :return: Valid grub2 accepted kernel/linux line after conversion. If nothing found return ''.
    """
    kernel_line = ''

    # Remove '=' from linux/kernel parameter
    if (search_text + '=') in match_line:
        kernel_path = match_line.replace((search_text + '='), '').strip()
        search_text = search_text.replace('=', '')
    else:
        kernel_path = match_line.replace(search_text, '', 1).strip()

    # Check if kernel/linux exist using absolute path (kernel_path)
    if os.path.exists(os.path.join(config.usb_mount, kernel_path)):
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' ' + kernel_path.strip()

    # Check if path to kernel/linux exist in isolinux directory and return absolute path
    elif os.path.exists(os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path), isolinux_dir, kernel_path)):
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' /multibootusb/' + \
                      iso.iso_basename(config.image_path) + '/' + isolinux_dir + '/' + kernel_path.strip()

    # Check if multiple kernel/linux exist and convert it to grub accepted line
    # Found such entries in manjaro and slitaz
    elif ',/' in kernel_path:
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' ' + kernel_path.strip()
        kernel_line = kernel_line.replace(',/', ' /')

    # Same as above but I found this only in dban
    elif 'z,' in kernel_path:
        kernel_line = search_text.lower().replace('kernel', 'linux') + ' ' + kernel_path.strip()
        kernel_line = kernel_line.replace('z,', ' /multibootusb/' + iso.iso_basename(config.image_path) + '/'
                                          + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')
    else:
        kernel_line = ''

    return kernel_line.replace('\\', '/').replace('//', '/')


def iso2grub2(iso_dir):
    """
    Function to convert syslinux configuration to grub2 accepted configuration format. Features implemented are similar
    to that of grub2  'loopback.cfg'. This 'loopback.cfg' file can be later on caled directly from grub2. The main
    advantage of this function is to generate the 'loopback.cfg' file automatically without manual involvement.
    :param iso_dir: Path to distro install directory for looping through '.cfg' files.
    :param file_out: Path to 'loopback.cfg' file. By default it is set to root of distro install directory.
    :return:
    """
    grub_file_path = os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path), 'loopback.cfg')
    gen.log('loopback.cfg file is set to ' + grub_file_path)
    iso_bin_dir = iso.isolinux_bin_dir(config.image_path)
    # Loop though the distro installed directory for finding config files
    for dirpath, dirnames, filenames in os.walk(iso_dir):
        for f in filenames:
            # We will strict to only files ending with '.cfg' extension. This is the file extension isolinux or syslinux
            #  recommends for writing configurations
            if f.endswith((".cfg", ".CFG")):
                cfg_file_path = os.path.join(dirpath, f)
                # We will omit the grub directory
                if 'grub' not in cfg_file_path:
                    # we will use only files containing strings which can be converted to grub2 cfg style
                    if string_in_file(cfg_file_path, 'menu label') or string_in_file(cfg_file_path, 'label'):
                        with open(cfg_file_path, "r", errors='ignore') as cfg_file_str:
                            data = cfg_file_str.read()
                            # Make sure that lines with menu label, kernel and append are available for processing
                            ext_text = re.finditer('(menu label|label)(.*?)(?=(menu label|label))', data, re.I|re.DOTALL)
                            if ext_text:
                                for m in ext_text:
                                    menuentry = ''
#                                     kernel = ''
                                    kernel_line = ''
                                    boot_options = ''
                                    initrd_line = ''
#                                     initrd = ''

                                    # Extract line containing 'menu label' and convert to menu entry of grub2
                                    if 'menu label' in m.group().lower():
                                        menu_line = re.search('menu label(.*)\s', m.group(), re.I).group()
                                        menuentry = 'menuentry ' + gen.quote(re.sub(r'menu label', '', menu_line, re.I, ).strip())
                                        # Ensure that we do not have caps menu label in the menuentry
                                        menuentry = menuentry.replace('MENU LABEL', '')

                                    elif 'label ' in m.group().lower():
                                        # Probably config does not use 'menu label' line. Just line containing 'label'
                                        #  and convert to menu entry of grub2
                                        menu_line = re.search('^label(.*)\s', m.group(), re.I).group()
                                        menuentry = 'menuentry ' + gen.quote(re.sub(r'label', '', menu_line, re.I, ).strip())
                                        # Ensure that we do not have caps label in the menuentry
                                        menuentry = menuentry.replace('LABEL', '')

                                    # Extract kernel line and change to linux line of grub2
                                    if 'kernel' in m.group().lower() or 'linux' in m.group().lower():
                                        kernel_text = re.findall('((kernel|linux)[= ].*?[ \s])', m.group(), re.I)
                                        match_count = len(re.findall('((kernel|linux)[= ].*?[ \s])', m.group(), re.I))
                                        if match_count is 1:
                                            kernel_line = extract_kernel_line(kernel_text[0][1], kernel_text[0][0], iso_bin_dir)
                                        elif match_count > 2:
                                            for _lines in kernel_text:
                                                kernel_line = extract_kernel_line(_lines[0][1], _lines[0][0],
                                                                                  iso_bin_dir)
                                                if kernel_line == '':
                                                    continue
                                                else:
                                                    break

                                    if 'initrd' in m.group().lower():
                                        initrd_text = re.findall('((initrd)[= ].*?[ \s])', m.group(), re.I)
                                        match_count = len(re.findall('((initrd)[= ].*?[ \s])', m.group(), re.I))
                                        if match_count is 1:
                                            initrd_line = extract_kernel_line(initrd_text[0][1], initrd_text[0][0], iso_bin_dir)
                                        elif match_count > 2:
                                            for _lines in initrd_text:
                                                initrd_line = extract_kernel_line(_lines[0][1], _lines[0][0],
                                                                                  iso_bin_dir)
                                                if initrd_line == '':
                                                    continue
                                                else:
                                                    break

                                    if 'append' in m.group().lower():
                                        append_line = re.search('append (.*)\s', m.group(), re.I).group()
                                        boot_options = re.sub(r'((initrd[= ])(.*?)[ ])', '', append_line, re.I, flags=re.DOTALL)
                                        boot_options = re.sub(r'append', '', boot_options, re.I).strip()
                                        boot_options = boot_options.replace('APPEND', '')

                                    if kernel_line.strip():
                                        linux = kernel_line.strip() + ' ' + boot_options.strip().strip()
                                    else:
                                        linux = ''

                                    if menuentry.strip() and linux.strip() and initrd_line.strip():
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '    ' + initrd_line)
                                        write_to_file(grub_file_path, '}\n')
                                    elif menuentry.strip() and linux.strip():
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '}\n')

    if os.path.exists(grub_file_path):
        gen.log(
            'loopback.cfg file is successfully created.\nYou must send this file for debugging if something goes wrong.')
        return 'loopback.cfg'
    else:
        gen.log('Failed to convert syslinux config file to loopback.cfg')
        return False
