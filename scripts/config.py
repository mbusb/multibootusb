#!/usr/bin/env python3
# Name:     config.py
# Purpose:  Module to share important variables between various modules. Mainly included so as not to call many
#           functions again and again
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

iso_link = ""
usb_disk = ""
usb_mount = ""
usb_uuid = ""
usb_label = ""
usb_details = ''
image_path = ""
persistence = 0
persistence_available = False
persistence_max_size = 0
distro = ""
status_text = ""
percentage = 0
syslinux_version = ''
uninstall_distro_dir_name = ""
uninstall_distro_dir_path = ""
iso_file_list = ''
iso_bin_dir = ''
process_exist = None
yes = False
cli_dd = False
cli_syslinux = False
usb_gpt = ''

imager_iso_link = ""
imager_usb_disk_selected = ""
imager_lock = ""
imager_percentage = ""
imager_status_text = ""

install_size = ""

editors_linux = ["xdg-open", "gedit", "kate", "kwrite"]
editors_win = ["notepad++.exe", "notepad.exe"]

imager_usb_disk = []

debug = False
