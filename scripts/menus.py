#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     menus.py
# Purpose:  Module contain custom menu entries for fewer distros
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

from . import iso
from . import config


def pc_tool_config(syslinux=True, grub=False):
    """
    Menu entry for PC Tool ISO 
    :param syslinux: 
    :param grub: 
    :return: 
    """
    if syslinux is True:
        return """LABEL livecd
KERNEL /system/stage1
APPEND initrd=/system/stage2 root=/dev/ram0 rw rdinit=/linuxrc video=vesa:ywrap,mtrr vga=0x303 loglevel=0 splash boot=cdrom\n"""
    elif grub is True:
        return """menuentry """ + iso.iso_basename(config.image_path) + """ {
linux /system/stage1 root=/dev/ram0 rw rdinit=/linuxrc video=vesa:ywrap,mtrr vga=0x303 loglevel=0 splash boot=cdrom
initrd /system/stage2\n}"""
