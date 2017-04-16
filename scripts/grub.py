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


def mbusb_update_grub_cfg():
    """
    Function to update grub.cfg file to support UEFI/EFI systems
    :return:
    """
    # Lets convert syslinux config file to grub2 accepted file format.
    _iso_dir = os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path))
    try:
        gen.log('Trying to create loopback.cfg')
        iso2_grub2_cfg = iso2grub2(_iso_dir)
        # gen.log('loopback.cfg file created...')
    except Exception as e:
        gen.log('Error converting syslinu cfg to grub2 cfg', error=True)
        gen.log(e)
        iso2_grub2_cfg = False

    grub_cfg_path = None
    syslinux_menu = None
    sys_cfg_path = None
    loopback_cfg_path = None
    mbus_grub_cfg_path = os.path.join(config.usb_mount, 'multibootusb', 'grub', 'grub.cfg')
    iso_grub_cfg = iso.iso_file_path(config.image_path, 'grub.cfg')
    if iso.isolinux_bin_dir(config.image_path) is not False:
        iso_sys_cfg_path = os.path.join(iso.isolinux_bin_dir(config.image_path), 'syslinux.cfg')
        iso_iso_cfg_path = os.path.join(iso.isolinux_bin_dir(config.image_path), 'isolinux.cfg')

        if os.path.exists(os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path),
                                       iso_sys_cfg_path)):
            syslinux_menu = iso_sys_cfg_path.replace('\\', '/')
        elif os.path.exists(os.path.join(config.usb_mount, 'multibootusb', iso.iso_basename(config.image_path),
                                         iso_iso_cfg_path)):
            syslinux_menu = iso_iso_cfg_path.replace('\\', '/')

#<<<<<<< HEAD
#    efi_grub_cfg = get_grub_cfg(config.iso_link)
#    boot_grub_cfg = get_grub_cfg(config.iso_link, efi=False)
#    loopback_cfg_path = iso.iso_file_path(config.iso_link, 'loopback.cfg')
#=======
    efi_grub_cfg = get_grub_cfg(config.image_path)
    loopback_cfg_path = iso.iso_file_path(config.image_path, 'loopback.cfg')
    boot_grub_cfg = get_grub_cfg(config.image_path, efi=False)
#>>>>>>> origin/devel

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
                elif config.distro == 'mentest':
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
    iso_size_mb = iso.iso_size(config.image_path) / (1024.0 * 1024.0)
    gen.log('size of the ISO is ' + str(iso_size_mb))
    if distro == 'sgrubd2' or distro == 'raw_iso':
        grub_raw_iso(mbus_grub_cfg_path)
    elif distro == '':

        '''
        with open(mbus_grub_cfg_path, 'a') as f:
            f.write("#start " + iso.iso_basename(config.image_path) + "\n")
            f.write(grub_raw_iso())
            f.write("#end " + iso.iso_basename(config.image_path) + "\n")
        
    
    elif iso_size_mb < 750.0:
        grub_raw_iso(mbus_grub_cfg_path)
        '''

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

    :param _file:
    :param search_text:
    :return:
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
    # Loop though the distro installed directory for finding config files
    for dirpath, dirnames, filenames in os.walk(iso_dir):
        for f in filenames:
            # We will strict to only files ending with '.cfg' extension. This is the file extension isolinux or syslinux
            #  recommends for writing configurations
            if f.endswith(".cfg") or f.endswith('.CFG'):
                cfg_file_path = os.path.join(dirpath, f)
                # We will omit the grub directory
                if 'grub' not in cfg_file_path:
                    # we will use only files containing strings which can be converted to grub2 cfg style
                    if string_in_file(cfg_file_path, 'menu label') or string_in_file(cfg_file_path, 'label'):
                        with open(cfg_file_path, "r", errors='ignore') as cfg_file_str:
                            data = cfg_file_str.read()
                            # Make sure that lines with menu label, kernel and append are available for processing
                            ext_text = re.finditer('(menu label|label)(.*?)(?=(menu label|label))', data, re.I|re.DOTALL)
                            # if (sum(1 for j in ext_text)) == 0:
                            #    ext_text = re.finditer('(menu label|label)(.*?)\Z', data, re.I|re.DOTALL)
                            if ext_text:
                                for m in ext_text:
                                    menuentry = ''
                                    kernel = ''
                                    boot_options = ''
                                    initrd = ''
                                    # print(m.group())

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
                                    if 'kernel' in m.group().lower() or 'linux ' in m.group().lower():
                                        kernel_line = re.findall('((kernel|linux)[= ].*?[ \s])', m.group(), re.I)[0][0]

                                        kernel = kernel_line.strip().replace('kernel', 'linux')
                                        kernel = kernel.strip().replace('KERNEL', 'linux')
                                        if 'linux=/multibootusb' in kernel.lower():
                                            kernel = kernel.strip().replace('linux=', 'linux ')

                                        elif 'linux=' in kernel.lower():
                                            kernel = kernel.strip().replace('linux=', 'linux /multibootusb/' +
                                                                                    iso.iso_basename(config.image_path) + '/'
                                                                                    + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')
                                        elif 'linux /' not in kernel:
                                            kernel = kernel.strip().replace('linux ', 'linux /multibootusb/' +
                                                                                    iso.iso_basename(config.image_path) + '/'
                                                                                    + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')

                                        # Ensure that we do not have linux parameter in caps
                                        kernel = kernel.replace('LINUX ', 'linux ')
                                        kernel = kernel.replace('Linux ', 'linux ')
                                        # Fix for solus os. Patch welcome.
                                        if config.distro == 'fedora' and '/linux' in kernel:
                                            kernel = kernel.replace('/linux', '/kernel')

                                    # Ensure that initrd is present in the config file
                                    if 'initrd' in m.group().lower():
                                        # Extract only initrd line which starts in first in the line
                                        if re.search('^initrd', m.group(), re.I|re.MULTILINE):
                                            initrd = re.findall('(initrd[= ].*?[ \s])', m.group(), re.I)[0]
                                            if not initrd:
                                                # print('initrd not in seperate line')
                                                initrd = re.findall('(initrd[= ].*[ \s])', initrd, re.I|re.DOTALL)[0]
                                                # Ensure that multiple initrd of syslinux are converted to grub2
                                                # standard
                                                initrd = initrd.replace(',/', ' /')
                                                initrd = initrd.replace('z,', 'z /multibootusb/' +
                                                                        iso.iso_basename(config.image_path) + '/'
                                                                        + iso.isolinux_bin_dir(config.image_path).replace('\\', '/')  + '/')
                                                #print('initrd')
                                        else:
                                            # Extract initrd parameter from within the line
                                            initrd = re.findall('(initrd[= ].*?[ ])', m.group(), re.I|re.DOTALL)[0]
                                            initrd = initrd.replace(',/', ' /')
                                            initrd = initrd.replace('z,', 'z /multibootusb/' +
                                                                    iso.iso_basename(config.image_path) + '/'
                                                                    + iso.isolinux_bin_dir(config.image_path).replace('\\', '/')  + '/')
                                            #print(initrd)

                                        # Ensure that we change the relative path to absolute path
                                        if 'initrd=/multibootusb' in initrd.lower():
                                            initrd = initrd.strip().replace('initrd=', 'initrd ')
                                            initrd = initrd.strip().replace('INITRD=', 'initrd ')

                                        elif 'initrd=' in initrd.lower():
                                            initrd = initrd.strip().replace('initrd=', 'initrd /multibootusb/' +
                                                                          iso.iso_basename(config.image_path) + '/'
                                                                          + iso.isolinux_bin_dir(config.image_path).replace('\\', '/') + '/')

                                        # Ensure that there is no caps which is not accepted by grub2
                                        initrd = initrd.replace('INITRD', 'initrd')

                                    # Extract append line for getting boot options
                                    if 'append' in m.group().lower():
                                        append = re.search('append (.*)\s', m.group(), re.I).group()
                                        boot_options = re.sub(r'((initrd[= ])(.*?)[ ])', '', append, re.I, flags=re.DOTALL)

                                        # Ensure that there is no append line exisit
                                        boot_options = re.sub(r'append', '', boot_options, re.I).strip()
                                        boot_options = boot_options.replace('APPEND', '')

                                    # We will ensure that all options are met as per grub2 specifications and
                                    # write to file
                                    linux = kernel.strip() + ' ' + boot_options.strip().strip()
                                    if menuentry and linux and initrd:
                                        # print('\n', menuentry)
                                        # print(linux)
                                        # print(initrd)
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '    ' + initrd)
                                        write_to_file(grub_file_path, '}\n')
                                    elif menuentry and linux.strip():
                                        write_to_file(grub_file_path, menuentry + '{')
                                        write_to_file(grub_file_path, '    ' + linux)
                                        write_to_file(grub_file_path, '}\n')

    if os.path.exists(grub_file_path):
        gen.log('loopback.cfg file successfully created.\nYou must send this file for debugging if something goes wrong.')
        return 'loopback.cfg'
    else:
        gen.log('Could not convert syslinux config to loopback.cfg')
        return False
