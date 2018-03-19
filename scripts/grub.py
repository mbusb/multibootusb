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
    install_dir = os.path.join(config.usb_mount, 'multibootusb',
                               iso.iso_basename(config.image_path))

    # First write custom loopback.cfg file so as to be detected by iso2grub2 function later.

    # There may be more than one loopback.cfg but we just need to fix
    # one and that is goingn to be referenced in mbusb's grub.cfg.
    loopback_cfg_path = iso.iso_file_path(config.image_path, 'loopback.cfg')
    if not loopback_cfg_path:
        loopback_cfg_path = 'loopback.cfg'

    wrote_custom_cfg = write_custom_grub_cfg(install_dir, loopback_cfg_path)

    # Try to generate loopback entry file from syslinux config files
    try:
        gen.log('Trying to create loopback.cfg')
        iso2_grub2_cfg = iso2grub2(install_dir, loopback_cfg_path,
                                   wrote_custom_cfg)
    except Exception as e:
        print(e)
        gen.log(e)
        gen.log('Error converting syslinux cfg to grub2 cfg', error=True)
        iso2_grub2_cfg = False

    grub_cfg_path = None
    syslinux_menu = None
#     sys_cfg_path = None
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


def write_custom_grub_cfg(install_dir, loopback_cfg_path):
    """
    Create custom grub loopback.cfg file for known distros. Custom menu entries are stored on munus.py module
    :return: 
    """
    loopback_cfg_path = os.path.join(
        install_dir, loopback_cfg_path.lstrip(r'\/'))
    menu = False
    if config.distro == 'pc-tool':
        menu = menus.pc_tool_config(syslinux=False, grub=True)
    elif config.distro == 'rising-av':
        menu = menus.rising(syslinux=False, grub=True)

    if menu is not False:
        gen.log('Writing custom loopback.cfg file...')
        write_to_file(loopback_cfg_path, menu)
        return True
    else:
        return False


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


def write_to_file(file_path, _strings):

    try:
        with open(file_path, 'a') as f:
            f.write(_strings + '\n')
    except:
        gen.log('Error writing to %s...' % file_path)


def kernel_search_path(isolinux_dir):
    return 
    
def locate_kernel_file(subpath, isolinux_dir):
    for d in [
            '',
            os.path.join('multibootusb',
                         iso.iso_basename(config.image_path), isolinux_dir),
            # Down below are dire attemps to find.
            os.path.join('multibootusb',
                         iso.iso_basename(config.image_path)),
            os.path.join('multibootusb',
                         iso.iso_basename(config.image_path), 'arch'),
            ]:
        if os.path.exists(os.path.join(config.usb_mount, d, subpath)):
            unix_style_path = os.path.join(d, subpath).\
                              replace('\\', '/').\
                              lstrip('/')
            return ('/' + unix_style_path)
    return subpath
        
        
def tweak_bootfile_path(img_file_spec, isolinux_dir):
    """
    Function to find image files to boot and return them concatinated
    with a space. Return the spec untouched if no locations are found.
    :param kernel_file_spec: Image path specification lead by kernel/linux keyword within isolinux supported .cfg files.
    :param isolinux_dir: Path to isolinux directory of an ISO
    :return: Converted file paths joined by a space. If no files can be located, img_file_spec is returned unmodified.
    """
    kernel_line = ''

    raw_paths = img_file_spec.split(',')
    converted_paths = [locate_kernel_file(p, isolinux_dir) for p in raw_paths]
    if raw_paths != converted_paths: # Tweaked the paths successfully?
        return ' '.join(converted_paths)

    if 'z,' in img_file_spec:
        # Fallback to legacy code.
        # "... I found this only in dban"
        iso_dir = iso.isolinux_bin_dir(config.image_path)
        replacement = ' /multibootusb/' + iso.iso_basename(config.image_path) \
                      + '/' \
                      + iso_dir.replace('\\', '/') + '/'
        return img_file_spec.replace('z,', replacement)
    # Give up and return the original with replaced delimeters.
    return ' '.join(img_file_spec.split(','))


def extract_initrd_param(value, isolinux_dir):
    kernel_search_path = [
        '',
        os.path.join('multibootusb',
                     iso.iso_basename(config.image_path), isolinux_dir),
        os.path.join('multibootusb', # A dire attemp to find.
                     iso.iso_basename(config.image_path)),
        ]
    initrd_line, others = '', []
    for paramdef in value.split(' '):
        if not paramdef.lower().startswith('initrd='):
            others.append(paramdef)
            continue
        paths = [locate_kernel_file(s, isolinux_dir) for s 
                 in paramdef[len('initrd='):].split(',')]
        initrd_line = 'initrd ' + ' '.join(paths)
    return  initrd_line, ' '.join(others)


def iso2grub2(install_dir, loopback_cfg_path, wrote_custom_cfg):
    """
    Function to convert syslinux configuration to grub2 accepted configuration format. Features implemented are similar
    to that of grub2  'loopback.cfg'. This 'loopback.cfg' file can be later on caled directly from grub2. The main
    advantage of this function is to generate the 'loopback.cfg' file automatically without manual involvement.
    :param install_dir: Path to distro install directory for looping through '.cfg' files.
    :param loopback_cfg_path: Path to 'loopback.cfg' to be updated
    :param file_out: Path to 'loopback.cfg' file. By default it is set to root of distro install directory.
    :return:
    """
    loopback_cfg_path = os.path.join(
        install_dir, loopback_cfg_path.lstrip(r'\/'))

    gen.log('loopback.cfg file is set to ' + loopback_cfg_path)
    # Comment-out the previous content if write_custom_grub_cfg() did nothing.
    if os.path.exists(loopback_cfg_path) and not wrote_custom_cfg:
        with open(loopback_cfg_path, 'r') as f:
            lines = f.readlines()
        with open(loopback_cfg_path, 'w') as f:
            f.write('##### Previous content is kept from here.\n')
            f.write( ''.join('#'+s for s in lines))
            f.write('##### to here.\n\n')

    iso_bin_dir = iso.isolinux_bin_dir(config.image_path)
    seen_menu_lines = []
    # Loop though the distro installed directory for finding config files
    for dirpath, dirnames, filenames in os.walk(install_dir):
        for f in filenames:
            # We will strict to only files ending with '.cfg' extension. This is the file extension isolinux or syslinux
            #  recommends for writing configurations
            if not f.endswith((".cfg", ".CFG")):
                continue
            cfg_file_path = os.path.join(dirpath, f)
            # We will omit the grub directory
            if 'grub' in cfg_file_path:
                continue
            # we will use only files containing strings which can be converted to grub2 cfg style
            with open(cfg_file_path, "r", errors='ignore') as f:
                data = f.read()

            # Make sure that lines with 'label' available for processing.
            # Do nothing otherwise.
            matching_blocks_re = [m for m in re.finditer(
                '^(label)(.*?)(?=(^label))',
                data, re.I|re.DOTALL|re.MULTILINE)]

            if matching_blocks_re:
                matching_blocks = [m.group() for m in matching_blocks_re]
                # Append the block after the last matching position
                matching_blocks.append(data[matching_blocks_re[-1].span()[1]:])
            else:
                m = re.match('^(label)(.*?)',
                             data, re.I|re.DOTALL|re.MULTILINE)
                matching_blocks = m and [data[m.start():]] or []

            if not matching_blocks:
                continue

            #if not cfg_file_path.endswith('archiso_pxe64.cfg'):
            #    continue
            gen.log("Probing '%s'" % cfg_file_path)
            out_lines = []
            for matching_block in matching_blocks:
                #print ('------------ block begins here ------------')
                #print (matching_block)
                #print ('------------ block ends here ------------')
                # Extract 'menu label or 'label' line.
                matches =  re.findall(
                    r'^\s*(menu label|label)\s+(.*)$',
                    matching_block, re.I|re.MULTILINE)
                labels = [v for v in matches if v[0].lower()=='label']
                menu_labels = [v for v in matches if v[0].lower()=='menu label']
                if 0 == len(labels) + len(menu_labels):
                    gen.log('Warning: found a block without menu-entry.')
                    menu_line = 'menuentry "Anonymous"'
                    menu_label = 'Unlabeled'
                else:
                    for vec, name in [ (labels, 'label'),
                                       (menu_labels, 'menu label') ]:
                        if 2 <= len(vec):
                            gen.log("warning: found a block with more than "
                                    "one '%s' entries." % name)
                    # Prefer 'menu label' over 'label'.
                    if 0<len(menu_labels):
                        value = menu_labels[0][1].replace('^', '')
                    else:
                        value = labels[0][1]
                    menu_line = 'menuentry ' + gen.quote(value)
                    menu_label = value

                # Extract lines containing 'kernel','linux','initrd'
                # or 'append' to convert them into grub2 compatible ones.
                linux_line = initrd_line = None
                appends = []
                for keyword, value in re.findall(
                        r'^\s*(kernel|linux|initrd|append)[= ](.*)$',
                        matching_block, re.I|re.MULTILINE):
                    kw = keyword.lower()
                    if kw in ['kernel', 'linux']:
                        if linux_line:
                            gen.log("Warning: found more than one "
                                    "'kernel/linux' lines in block '%s'."
                                    % menu_label)
                            continue
                        linux_line = 'linux ' + \
                                     tweak_bootfile_path(value, iso_bin_dir)
                    elif kw == 'initrd':
                        if initrd_line:
                            gen.log("Warning: found more than one "
                                    "'initrd' specifications in block '%s'."
                                    % menu_label)
                            continue
                        initrd_line = 'initrd ' + \
                                      tweak_bootfile_path(value, iso_bin_dir)
                    elif kw== 'append':
                        new_initrd_line, new_value = extract_initrd_param(
                            value, iso_bin_dir)
                        if new_initrd_line:
                            if initrd_line:
                                gen.log("Warning: found more than one initrd "
                                        "specifications in block '%s'."
                                        % menu_label)
                            initrd_line = new_initrd_line
                        appends.append(new_value)

                if menu_line in seen_menu_lines:
                    out_lines.append( "# '%s' is superceded by the previous "
                                      "definition." % menu_label)
                else:
                    if linux_line or initrd_line:
                        seen_menu_lines.append(menu_line)
                        out_lines.append(menu_line + ' {')
                        for l, a in [
                                (linux_line, ' ' + ' '.join(appends)),
                                (initrd_line, '')]:
                            if l:
                                out_lines.append('    ' + l + a)
                        out_lines.append( '}' )
                    else:
                        out_lines.append("# Avoided emitting an empty "
                                         "menu item '%s'." % menu_label)

            with open(loopback_cfg_path, 'a') as f:
                f.write('# Extracted from %s\n' %
                        cfg_file_path.replace('\\', '/'))
                f.write('\n'.join(out_lines) + '\n')
                f.write('\n')

    if os.path.exists(loopback_cfg_path):
        gen.log(
            'loopback.cfg file is successfully created.\nYou must send this file for debugging if something goes wrong.')
        return 'loopback.cfg'
    else:
        gen.log('Failed to convert syslinux config file to loopback.cfg')
        return False
