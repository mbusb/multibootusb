#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     uninstall_distro.py
# Purpose:  Module to remove selected distro from USB disk.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import sys
import shutil

if not os.getuid() == 0:
    print "You must run this file with admin privilege."
    print "Try sudo ./uninstall.py"
    sys.exit(0)
else:
    if os.path.exists("./.install_files.txt"):
        with open("./.install_files.txt", "r") as f:
            file_list = f.readlines()
        for f in file_list:
            print "Removing " + f.replace('\n', '')
            if os.path.isfile(f.replace('\n', '')):
                os.remove(f.replace('\n', ''))
            elif os.path.isdir(f.replace('\n', '')):
                shutil.rmtree(f.replace('\n', ''))
        if os.path.exists(os.path.join(sys.prefix, "multibootusb")):
            shutil.rmtree(os.path.join(sys.prefix, "multibootusb"))

        print "multibootusb is successfully unistalled..."
    else:
        print "Unable to find install file list."
        print "This script works only if you have installed multibootusb using install.py script."