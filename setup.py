#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Name:     setup.py
# Purpose:  Module to create packages or install multibootusb package from source
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

from distutils.core import setup
#from setuptools import setup, find_packages
import os
import sys
from scripts.gen import mbusb_version

Version = mbusb_version()
print(Version)
setup(
    name='multibootusb',
    version=Version,
    packages=['scripts', 'scripts.pyudev', 'scripts.pyudev.device', 'scripts.pyudev._ctypeslib', 'scripts.pyudev._os',
              'scripts.gui', 'scripts.progressbar'],
    #packages=find_packages(),
    scripts=['multibootusb', 'multibootusb-pkexec'],
    platforms=['Linux'],
    url='http://multibootusb.org/',
    license='General Public License (GPL)',
    author='Sundar',
    author_email='feedback.multibootusb@gmail.com',
    description='Create multi boot live Linux on a USB disk...',
    long_description='multibootusb is an advanced cross-platform application for installing/uninstalling Linux operating systems on to a single USB flash drives.',
    data_files=[("/usr/share/applications", ["data/multibootusb.desktop"]),
                ('/usr/share/pixmaps', ["data/tools/multibootusb.png"]),
                ('/usr/share/polkit-1/actions/', ['org.debian.pkexec.run-multibootusb.policy']),
                ('/usr/share/multibootusb/data/tools', ["data/tools/mbr.bin"]),
                ('/usr/share/multibootusb/data', ["data/version.txt"]),
                ('/usr/share/multibootusb/data/tools', ["data/tools/multibootusb.png"]),
                ('/usr/share/multibootusb/data/tools/dd', ["data/tools/dd/dd.exe"]),
                ('/usr/share/multibootusb/data/tools/dd', ["data/tools/dd/diskio.dll"]),
                ('/usr/share/multibootusb/data/tools/mkfs', ["data/tools/mkfs/mke2fs.exe"]),
                ('/usr/share/multibootusb/data/tools/EFI', ["data/EFI/*"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/chain.c32"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/bg.png"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/extlinux.cfg"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/grub.exe"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/memdisk"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/menu.c32"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/menu.lst"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/syslinux.cfg"]),
                ('/usr/share/multibootusb/data/multibootusb', ["data/multibootusb/vesamenu.c32"]),
                ('/usr/share/multibootusb/data/multibootusb/grub', ["data/multibootusb/grub/*"]),
                ('/usr/share/multibootusb/data/tools/syslinux', ["data/tools/syslinux/syslinux_modules.zip"]),
                ('/usr/share/multibootusb/data/tools/syslinux', ["data/tools/syslinux/syslinux_linux.zip"]),
                ('/usr/share/multibootusb/data/tools/syslinux', ["data/tools/syslinux/syslinux_linux_64.zip"]),
                ('/usr/share/multibootusb/data/tools/syslinux', ["data/tools/syslinux/syslinux_windows.zip"])]
)
