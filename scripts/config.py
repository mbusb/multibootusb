#!/usr/bin/env python3
# Name:     config.py
# Purpose:  Module to share important variables between various modules. Mainly included so as not to call many
#           functions again and again
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

iso_link = ""
usb_disk = None
usb_mount = ""
usb_uuid = ""
usb_label = ""
usb_details = ''
image_path = None
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
remounted_partitions = []

debug = False

# protected_drives = ['C:','D:','E:', '/dev/sda', '/dev/sdb', '/dev/sdc']

# If turned off, qemu will be sought at a few preset locations
# first before deciding to use the bundled exe.
# Set 'qemu_exe_path' to explicitly specify.
qemu_use_builtin = True # Relevant on Windows only

# qemu_exe_path = r"C:\pkgs\qemu\qemu-system-x86_64.exe"
# Relevant on Windows only

# Enable QEMU accelaration by Intel HAXM hypervisor.
# Bundled QEMU does not support this.
# See https://www.qemu.org/2017/11/22/haxm-usage-windows/ for setup.
qemu_use_haxm = not qemu_use_builtin  # Relevant on Windows only
# qemu_use_kvm = False
# qemu_bios = 'OVMF.fd'

def update_usb_mount(new_usb_details):
    global usb_mount, usb_details
    usb_mount = new_usb_details['mount_point'].replace('\\x20', ' ')
    usb_details = new_usb_details

def add_remounted(usb_disk):
    if usb_disk not in remounted_partitions:
        remounted_partitions.append(usb_disk)
