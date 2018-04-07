#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     distro.py
# Purpose:  Module to detect if distro types supported by multibootusb (by extracting specific files)
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

from functools import partial
import os
import platform
import re

from . import _7zip
from .gen import *
from . import iso
from .isodump3 import ISO9660

def distro(iso_cfg_ext_dir, iso_link, expose_exception=False):
    """
    Detect if distro is supported by multibootusb.
    :param iso_cfg_ext_dir: Directory where *.cfg files are extracted.
    :return: Detected distro name as string.
    """
#     iso9660fs = ISO9660(iso_link)
#     iso_file_list = iso9660fs.readDir("/")

    distro = None  # tenatively set to None

    iso_file_list = _7zip.list_iso(
        iso_link, expose_exception=expose_exception)
    iso_file_list_lower = [f.lower() for f in iso_file_list]
    v_isolinux_bin_exists = iso.isolinux_bin_exist(iso_link)

    # Let's have less costly checks first.
    # We'll have to make these checks as strictive as possible
    # so that keyword based tests will not be skipped because
    # of a false positive.

    if iso_file_list:
        distro = perform_strict_detections(iso_cfg_ext_dir, iso_file_list)
        if distro:
            return distro
        distro = detect_iso_from_file_list(iso_file_list)
        if distro:
            return distro
    else:
        iso_file_list = []

    def run_contains(keywords, filename, file_content, iso_flielist,
                     isolinux_bin_exists):
        return any(k in file_content for k in keywords.split('|'))

    def contains(keywords):
        return partial(run_contains, keywords.lower())

    def run_file_exists(filename_sought, filename, file_content, iso_filelist,
                        isolinux_bin_exists):
        return filename_sought in iso_filelist
    def file_exists(filename_sought):
        return partial(run_file_exists, filename_sought)

    def run_isolinux_bin_exists(exist_or_not, filename, file_content,
                                iso_filelist, isolinux_bin_exists):
        return exist_or_not is isolinux_bin_exists

    def isolinux_bin_exists(exist_or_not):
        return partial(run_isolinux_bin_exists, exist_or_not)

    def run_not(predicate, filename, file_content,
                iso_filelist, isolinux_bin_exists):
        return not predicate(filename, file_content, iso_filelist,
                             isolinux_bin_exists)
    def not_(predicate):
        return partial(run_not, predicate)

    # contains(X) predicates that X is contained in an examined text file.
    # Multiple keywords can be concatenated by '|'. Predicates gets aaserted
    # if anyone of the keywords is found in the text file.
    # Sorry you can't include | in a keyword for now.
    test_vector = [
        ('ubcd',       contains('ubcd')),
        ('sgrubd2',    contains('Super Grub Disk')),
        ('hbcd',       contains('hbcd')),
        ('systemrescuecd', contains('systemrescuecd')),
        ('parted-magic', [contains('pmagic|partedmagic'),
                          isolinux_bin_exists(True)]),
        # mounting fat filesystem hard coded in to initrd.
        # Can be modified only under linux.
        ('mageialive', contains('mgalive')),
        ('arch',       contains('archisolabel|misolabel|parabolaisolabel')),
        ('chakra',     contains('chakraisolabel')),
        ('kaos',       contains('kdeosisolabel')),
        ('debian',     [contains('boot=live'), isolinux_bin_exists(True)]),
        ('grml',       [contains('grml'), contains('live-media-path')]),
        ('debian-install', [contains('debian-installer'),
                            not_(file_exists('casper'))]),
        ('solydx',     contains('solydx')),
        ('knoppix',    contains('knoppix')),
        ('centos',     contains('root=live:CDLABEL=CentOS')),
        ('fedora',     contains('root=live:CDLABEL=|root=live:LABEL=')),
        ('fedora',     contains('redcore')),
        ('redhat',     contains('redhat')),
        ('slitaz',     contains('slitaz|dban |ophcrack|tinycore|rescue.cpi'
                                '|xpud|untangle|4mlinux|partition wizard'
                                '|android-x86.png|riplinux|lebel dummy'
                                '|http://pogostick.net/~pnh/ntpasswd/'
                                '|AVG Rescue CD|AntivirusLiveCD'
                                '|lkrn|Nanolinux|OSForensics|PING')),
        ('slitaz',     contains('minimal Slackware|Slackware-HOWTO')),
        #('suse',      contains('suse')),
        ('opensuse-install', contains('class opensuse')),
        ('ubuntu',     contains('boot=casper')),
        ('wifislax',   contains('wifislax')),
        ('slax',       contains('slax')),
        ('sms',        [contains('sms.jpg|vector |autoexec'),
                        isolinux_bin_exists(True)]),
        ('antix',      contains('antix')),
        ('porteus',    contains('porteus')),
        ('pclinuxos',  contains('livecd=livecd|PCLinuxOS')),
        ('gentoo',     contains('looptype=squashfs|http://dee.su/liberte')),
        ('finnix',     contains('finnix')),
        ('wifiway',    contains('wifiway')),
        ('puppy',      contains('puppy|quirky|fatdog|slacko|xenialpup')),
        ('ipcop',      contains('ipcop')),
        ('ipfire',     contains('ipfire')),
        ('salix-live', [contains('zenwalk|slack|salix'),
                        contains('live')]),
        ('zenwalk',        contains('zenwalk|slack|salix')),
        ('ubuntu-server',  contains('ubuntu server')),
        ('centos-install', contains('Install CentOS')),
        ('centos',         contains('centos')),
        ('trinity-rescue', contains('Trinity Rescue Kit')),
        ('alpine',         contains('alpine')),
        ('kaspersky',      contains('http://support.kaspersky.com')),
        ('alt-linux',      contains('ALT Linux')),
        ('Windows',        contains('Sergei Strelec')),
        ('ReactOS',        contains('ReactOS')),
        ('fsecure',        contains('fsecure')),
        ('pc-unlocker',    contains('default rwp')),
        ('pc-tool',        contains('/system/stage1')),
        ('grub2only',      contains('vba32rescue')),
        ('rising-av',      contains('BOOT_IMAGE=rising')),
        ('Avira-RS',       contains('Avira Rescue System')),
        ('insert',         contains('BOOT_IMAGE=insert')),
        ]


    # I'm not sure if this check is necessary prvious but code had skipped
    # keyword based checks if the platform is unknown.
    if platform.system() == "Linux" or platform.system() == "Windows":
        for path, subdirs, files in os.walk(iso_cfg_ext_dir):
            for name in files:
                name_lower = name.lower()
                if not name_lower.endswith(('.cfg', '.txt', '.lst')):
                    continue
                if name_lower=='i18n.cfg':
                    # i18n.cfg in salitaz-rolling cause misdetection
                    # of centos by the following line.
                    # MENU LABEL English US (acentos)
                    continue
                try:
                    # errors='ignore' is required as some files also
                    # contain non utf character
                    string = open(os.path.join(path, name),
                                  errors='ignore').read()
                except IOError:
                    log("Read Error on %s." % name)
                    continue

                for distro_, predicate in test_vector:
                    predicates = [predicate] if callable(predicate) \
                                 else predicate
                    if all( p(name_lower, string.lower(), iso_file_list_lower,
                              v_isolinux_bin_exists) for p in predicates ):
                        return distro_

    if distro:
        return distro
# FIXME: See the below comments.
#         else:
#             # FIXME: The idea of detecting as generic is to work like a unetbootin if other methods fails.
#             #  This simply extracts distro to root of the USB and install syslinux on isolinux.bin directory.
#             #  All works fine but unable to boot the distro successfully. Also, see the generic section from
#             #  syslinux, update_cfg and install_distro modules.
#             if self.isolinux_bin_exist():
#                 return "generic"
    elif str(iso_link).lower().endswith('.iso'):
        return 'memdisk_iso'
    elif str(iso_link).lower().endswith('.img'):
        return 'memdisk_img'
    else:
        return None


def detect_iso_from_file_list(iso_file_list):
    """
    Fallback detection script from the content of an ISO.
    :return: supported distro as string
    """
    keys_to_distro = [
        (['f4ubcd'], 'f4ubcd'),
        (['alpine-release'], 'alpine'),
        (['sources', 'boot.wim'], 'Windows'),
        (['config.isoclient'], 'opensuse'),
        (['dban'], 'slitaz'),
        (['memtest.img'], 'memtest'),
        (['mt86.png', 'isolinux'], 'raw_iso'),
        (['menu.lst'], 'grub4dos'),
        (['bootwiz.cfg', 'bootmenu_logo.png'], 'grub4dos_iso') ]

    filenames = [f.lower() for f in iso_file_list]
    for keys, distro in keys_to_distro:
        if all(k in filenames for k in keys):
            return distro
    #log("Examined %d %s in the iso but could not determine the distro."
    #  % (len(filenames), len(filenames)==1 and 'filename' or 'filenames'))
    return None


def perform_strict_detections(iso_cfg_ext_dir, iso_file_list):

    def run_contains(filepath, keyword, cfg_dir=iso_cfg_ext_dir):
        fullpath = os.path.join(cfg_dir, filepath.replace('/', os.sep))
        if not os.path.exists(fullpath):
            return False
        try:
            with open(fullpath, 'rb') as f:
                data = f.read().lower()
                return keyword in data
        except (IOError, OSError):
            log("Failed to open %s" % fullpath)
            return False

    def contains(relataive_filepath, keyword):
        return partial(run_contains, relataive_filepath,
                       bytes(keyword.lower(),'us-ascii'))

    # contains(P, K) predicates that file P contains the specified
    # string K. The predicate get never asserted if P has not been
    # extracted into the staging area (iso_cfg_ext_dir).
    test_vector = [
        ('wifislax',   contains('boot/syslinux/menu/vesamenu.cfg',
                                'menu label Wifislax64 Live')),
        ('salix-live', contains('boot/menus/mainmenu.cfg',
                                'MENU LABEL SALIX LIVE')),
        ('grml',       contains('boot/isolinux/vesamenu.cfg',
                                'menu title  Grml - Live Linux'))
        ]
    for distro, predicate in test_vector:
        predicates = [predicate] if callable(predicate) else predicate
        if all(p() for p in predicates):
            return distro
    return None


if __name__ == '__main__':
    iso_cfg_ext_dir = os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir")
    iso_link = 'Downloads/clonezilla-live-2.4.2-32-amd64.iso'
    iso_extract_file(iso_link, iso_cfg_ext_dir, 'cfg')
    log(distro(iso_cfg_ext_dir))
