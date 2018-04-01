#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     persistence.py
# Purpose:  Module to deal with persistence of a selected distro.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

from functools import partial
import os
import platform
import stat
import subprocess
import tarfile

from . import iso
from . import gen
from . import config

def max_disk_persistence(usb_disk):
    """
    Detect max persistence value for filesystem on usb_disk
    :param usb_disk: Disk filesystem to check
    :return: Max persistence supported (bytes)
    """
    assert usb_disk is not None

    fat_max_size = (4096 * 1024 * 1024)
    usb_details = config.usb_details
    config.usb_uuid = usb_details['uuid']
    config.usb_label = usb_details['label']

    if usb_details['file_system'] in ['vfat', 'FAT32'] and usb_details['size_free'] > fat_max_size:
        _max_size = fat_max_size
    else:
        _max_size = usb_details['size_free']

    return _max_size

def persistence_distro(distro, iso_link):
    """
    Function to detect if distro can have persistence option.
    :param distro: Detected distro name.
    :return: Distro name as string or None otherwise.
    """
    assert distro is not None
    assert iso_link is not None

#     iso_size = iso.iso_size(iso_link)

    if distro in ["ubuntu", "debian", "debian-install", "fedora", "centos"]:
        gen.log("Persistence option is available.")
        return distro
    else:
        return None

def create_persistence_using_mkfs(persistence_fname, persistence_size):
    persistence_path = os.path.join(config.usb_mount, 'multibootusb',
                                    iso.iso_basename(config.image_path),
                                    persistence_fname)
    volume_name = os.path.basename(persistence_fname)
    if platform.system() == 'Windows':
        tools_dir = os.path.join('data', 'tools')
        mke2fs_relative_path = os.path.join(tools_dir, 'mkfs', 'mke2fs.exe')
        mkfs = gen.resource_path(mke2fs_relative_path)
        dd_relative_path = os.path.join(tools_dir, 'dd', 'dd.exe')
        dd = gen.resource_path(dd_relative_path)
        persistence_mkfs_cmd = 'echo y|' + mkfs + ' -b 1024 ' + \
                               '-L ' + volume_name + ' ' + \
                               persistence_path
    else:
        mkfs = 'mkfs.ext3'
        dd = 'dd'
        persistence_mkfs_cmd = mkfs + ' -F ' + persistence_path

    mbytes =  persistence_size / 1024 / 1024
    persistence_dd_cmd = dd + ' if=/dev/zero ' + \
                         'of=' + persistence_path + \
                         ' bs=1M count=' + str(int(mbytes))

    gen.log('Executing ==>' + persistence_dd_cmd)
    config.status_text = 'Creating persistence file...'

    if subprocess.call(persistence_dd_cmd, shell=True) == 0:
        gen.log("\nSuccessfully created persistence file...\n")

    if config.distro != 'fedora':
        gen.log('Applying filesystem to persistence file...')
        config.status_text = 'Applying filesystem to persistence file. Please wait...'
        gen.log('Executing ==> ' + persistence_mkfs_cmd)
        config.status_text = 'Applying filesystem to persistence file...'
        if subprocess.call(persistence_mkfs_cmd, shell=True) == 0:
            gen.log("\nSuccessfully applied filesystem...\n")


def create_persistence_using_resize2fs(persistence_fname, persistence_size):
    outdir = os.path.join(config.usb_mount, 'multibootusb',
                          iso.iso_basename(config.image_path))
    persistence_path = os.path.join(outdir, persistence_fname)
    tools_dir = os.path.join('data', 'tools')
    if platform.system()=='Windows':
        _7zip_exe = gen.resource_path(
            os.path.join(tools_dir, '7zip', '7z.exe'))
    else:
        _7zip_exe = '7z'

    config.status_text = 'Copying persistence file...'
    persistence_gz = gen.resource_path(
        os.path.join(tools_dir, 'persistence.gz'))
    _7zip_cmd_base = [_7zip_exe, 'x', '-o' + outdir]
    for more_opts in ( ['-y'], ['-aoa'] ):
        _7zip_cmd = _7zip_cmd_base + more_opts + [persistence_gz]
        if subprocess.call(_7zip_cmd)==0:
            if not os.path.exists(persistence_path):
                gen.log("%s has failed to create the persistence file." %
                        _7zip_cmd)
                continue
            gen.log("Generated 'persistence' file in '%s'" % outdir)
            if persistence_fname != 'persistence':
                os.rename(os.path.join(outdir, 'persistence'),
                          persistence_path)
                gen.log("Renamed to '%s'." % persistence_path)
            break
        gen.log("%s has failed with non-zero exit status." % _7zip_cmd)
    else:
        gen.log("Couldn't generate persistence file '%s' by any means." %
                persistence_path)
        return

    current_size = os.stat(persistence_path)[stat.ST_SIZE]
    if current_size < persistence_size:
        msg = 'Extending the persistence file by %.1f MB...' % \
              ((persistence_size - current_size) / float(1024*1024))
        config.status_text = msg
        gen.log(msg)
        with open(persistence_path, 'ab') as f:
            _1M_block = b'\0' * (1024*1024)
            bytes_left = persistence_size - current_size
            while 0<bytes_left:
                block_size = min(1024*1024, bytes_left)
                f.write(_1M_block[:block_size])
                bytes_left -= block_size

    config.status_text = 'Resizing the persistence file...'
    fsck_cmd = ['e2fsck', '-y', '-f', persistence_path]
    if subprocess.call(fsck_cmd)==0:
        gen.log("Checking the persistence file.")

    resize_cmd = ['resize2fs', persistence_path]
    if subprocess.call(resize_cmd)==0:
        gen.log("Successfully resized the persistence file.")

creator_dict = {
    'ubuntu' : (create_persistence_using_mkfs,
                lambda C: ('casper-rw',)),
    'debian' : (create_persistence_using_resize2fs,
                lambda C: ('persistence',)),
    'debian-install' : (
        create_persistence_using_resize2fs,
        lambda C: ('persistence',)),
    'fedora' : (
        create_persistence_using_mkfs,
        lambda C: (os.path.join(
            'LiveOS', 'overlay-%s-%s' % (C.usb_label, C.usb_uuid)),)),
    'centos' : (
        create_persistence_using_mkfs,
        lambda C: (os.path.join(
            'LiveOS', 'overlay-%s-%s' % (C.usb_label, C.usb_uuid)),)),
    }

def detect_missing_tools(distro):
    if distro not in creator_dict or \
       creator_dict[distro][0] is not create_persistence_using_resize2fs:
        return None
    try:
        with open(os.devnull) as devnull:
            for tool in ['e2fsck', 'resize2fs']:
                subprocess.Popen([tool], stdout=devnull, stderr=devnull)
    except FileNotFoundError:  # Windows
        return "'%s.exe' is not installed or not available for use." % tool
    except OSError:            # Linux
        return "'%s' is not installed or not available for use." % tool
    return None

def create_persistence():
    x = creator_dict.get(config.distro)
    if x is None:
        gen.log("Persistence is not supported for '%s'." % config.distro)
        return False
    creator_func, args_generator = x
    args = args_generator(config) + (config.persistence,)
    creator_func(*args)
    return True

def extract_file(file_path, install_dir):
    """
    Function to extract persistence files to distro install directory.
    :param file_path: Path to persistence file.
    :param install_dir: Path to distro install directory.
    :return:
    """
    tar = tarfile.open(file_path, "r:bz2")
    tar.extractall(install_dir)
    tar.close()


def test():
    config.image_path = 'c:/Users/shinj/Downloads/' \
                        'Fedora-Workstation-Live-x86_64-27-1.6.iso'
    config.persistence = 1024 * 1024 * 20
    config.distro = 'fedora'
    config.usb_mount = 'h:\\'
    create_persistence()
