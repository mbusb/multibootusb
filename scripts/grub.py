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

    install_dir = os.path.join(config.usb_mount, 'multibootusb',
                               iso.iso_basename(config.image_path))
    grub_cfg_path = None
    syslinux_menu = None
    mbus_grub_cfg_path = os.path.join(config.usb_mount, 'multibootusb',
                                      'grub', 'grub.cfg')
    isobin_dir = iso.isolinux_bin_dir(config.image_path)
    if isobin_dir is not False:
        for name in ['syslinux.cfg', 'isolinux.cfg']:
            cfg_path = os.path.join(isobin_dir, name)
            cfg_fullpath = os.path.join(install_dir, cfg_path)
            if os.path.exists(cfg_fullpath):
                syslinux_menu = cfg_path.replace('\\', '/')
                break

    # Decide which grub config file to boot by.
    loopback_cfg_list = iso.get_file_list(
        config.image_path,
        lambda x: os.path.basename(x).lower()=='loopback.cfg')
    grub_cfg_list = iso.get_file_list(
        config.image_path,
        lambda x: os.path.basename(x).lower().startswith('grub') and
        os.path.basename(x).lower().endswith('.cfg'))
    # favour 'grub.cfg' over variants.
    flagged  = [(f, os.path.basename(f).lower()=='grub.cfg')
                for f in grub_cfg_list]
    grub_cfg_list = [ x[0] for x in flagged if x[1] ] + \
                    [ x[0] for x in flagged if not x[1] ]
    candidates = []
    for src_list, predicate in [
            # List in the order of decreasing preference.
            (loopback_cfg_list, lambda x: 'efi' in x.lower()),
            (loopback_cfg_list, lambda x: 'boot' in x.lower()),
            (grub_cfg_list, lambda x: 'efi' in x.lower()),
            (grub_cfg_list, lambda x: 'boot' in x.lower() and 'efi' not in x.lower()),
            (loopback_cfg_list,
             lambda x: 'efi' not in x.lower() and 'boot' not in x.lower()),
            (grub_cfg_list,
             lambda x: 'efi' not in x.lower() and 'boot' not in x.lower())]:
        sub_candidates = [x for x in src_list if predicate(x)]
        if len(sub_candidates):
            candidates.append(sub_candidates[0])
            # We could 'break' here but will let the iteration continue
            # in order to lower the chance of keeping latent bugs.

    if config.distro == 'mageialive' and 1<len(candidates):
        grub_cfg_path = candidates[1].replace('\\', '/')
    elif 0<len(candidates):
        grub_cfg_path = candidates[0].replace('\\', '/')
    else :
        # No suitable grub configuration file is provided by distro.
        # Lets convert syslinux config files to grub2 accepted file format.
        new_loopback_here = 'loopback.cfg'
        try:
            # First write custom loopback.cfg file so as to be detected
            # by iso2grub2 function later.
            write_custom_grub_cfg(install_dir, new_loopback_here)
            gen.log('Trying to create loopback.cfg')
            iso2grub2(install_dir, new_loopback_here)
        except Exception as e:
            new_loopback_here = None
            gen.log(e)
            gen.log('Error converting syslinux cfg to grub2 cfg', error=True)
        if new_loopback_here:
            grub_cfg_path = new_loopback_here.replace('\\', '/')
        #elif bootx_64_cfg is not False:
        #    grub_cfg_path = bootx_64_cfg.replace('\\', '/')
    gen.log("Using %s to boot this distro." % grub_cfg_path)

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


def locate_kernel_file(subpath, isolinux_dir):
    subpath_original = subpath
    # Looks like relative paths don't work in grub.
    #if subpath[0] != '/':
    #    gen.log("Accepting a relative kernel/initrd path '%s' as is."
    #            % subpath)
    #    return subpath
    if subpath[:1] != '/':
        subpath = '/' + subpath
    if os.path.exists(os.path.join(config.usb_mount, subpath[1:])):
        gen.log("Accepting kernel/initrd path '%s' as it exists." % subpath)
        return subpath
    _iso_basename = iso.iso_basename(config.image_path)
    subpath = subpath[1:]  # strip off the leading '/'
    drive_relative_prefix = 'multibootusb/' + _iso_basename + '/'
    if subpath.startswith(drive_relative_prefix):
        # Paths is already drive-relative make it install-dir-relative.
        subpath = subpath[len(drive_relative_prefix):]
    gen.log("Trying to locate kernel/initrd file '%s'" % subpath)
    for d in [
            os.path.join('multibootusb', _iso_basename, isolinux_dir or ''),
            # Down below are dire attemps to find.
            os.path.join('multibootusb', _iso_basename),
            os.path.join('multibootusb', _iso_basename, 'arch'),
            ]:
        fullpath = os.path.join(config.usb_mount, d, subpath)
        if os.path.exists(fullpath):
            gen.log("Digged out '%s' at '%s'" % (subpath, fullpath))
            unix_style_path = os.path.join(d, subpath).\
                              replace('\\', '/').\
                              lstrip('/')
            return ('/' + unix_style_path)
    return subpath_original
        
        
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


def extract_initrd_params_and_fix_kernel(value, isolinux_dir):
    initrd_line, others  = '', []
    tokens = value.split(' ')
    tokens.reverse()
    while 0<len(tokens):
        token = tokens.pop()
        if token=='linux':
            # deal with 'append linux /boot/bzImage' in salitaz-rolling
            if 0<len(tokens):
                kernel_file = locate_kernel_file(tokens.pop(), isolinux_dir)
                others.extend(['linux', kernel_file])
            else:
                others.append('linux')
        elif token.startswith('initrd='):
            paths = [locate_kernel_file(s, isolinux_dir) for s
                     in token[len('initrd='):].split(',')]
            initrd_line = 'initrd ' + ' '.join(paths)
        else:
            others.append(token)
    return  initrd_line, ' '.join(others),


def iso2grub2(install_dir, loopback_cfg_path):
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

    iso_bin_dir = iso.isolinux_bin_dir(config.image_path)
    seen_menu_entries = []
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
            matching_blocks_re = list(re.finditer(
                '^(label)(.*?)(?=(^label))',
                data, re.I|re.DOTALL|re.MULTILINE))

            if matching_blocks_re:
                matching_blocks = [m.group() for m in matching_blocks_re]
                # Append the block after the last matching position
                matching_blocks.append(data[matching_blocks_re[-1].span()[1]:])
            else:
                m = re.search('^(label)(.*?)',
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
                    menu_entry = 'Anonymous'
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
                    menu_entry = menu_label = value

                # Extract lines containing 'kernel','linux','initrd'
                # or 'append' to convert them into grub2 compatible ones.
                linux_line = initrd_line = None
                appends = []
                sought_archs = ['x86_64', 'i686', 'i386']
                arch = []
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
                        arch = [(value.find(a), a) for a in sought_archs
                                if 0 <= value.find(a)]
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
                        new_initrd_line, new_value \
                            = extract_initrd_params_and_fix_kernel(
                                value, iso_bin_dir)
                        appends.append(new_value)
                        if new_initrd_line:
                            if initrd_line:
                                gen.log("Warning: found more than one initrd "
                                        "specifications in block '%s'."
                                        % menu_label)
                            initrd_line = new_initrd_line
                if arch: # utilize left most arch.
                    menu_entry += (" (%s)" % sorted(arch)[-1][1])
                menu_line = 'menuentry ' + gen.quote(menu_entry)
                if menu_entry in seen_menu_entries:
                    out_lines.append( "# '%s' is superceded by the previous "
                                      "definition." % menu_label)
                else:
                    if linux_line or initrd_line:
                        seen_menu_entries.append(menu_entry)
                        out_lines.append(menu_line + ' {')
                        for starter, value in [
                                (linux_line, ' '.join(appends)),
                                (initrd_line, '')]:
                            vec = [x for x in [starter, value] if x]
                            if vec:
                                out_lines.append('    ' + ' '.join(vec))
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
        return loopback_cfg_path
    else:
        gen.log('Failed to convert syslinux config file to loopback.cfg')
        return False
