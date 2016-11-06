#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Name:     gen.py
# Purpose:  This 'general' module contain many functions required to be called at many places
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import sys
import os
import platform
import shutil
import string
import zipfile

def scripts_dir_path():
    return os.path.dirname(os.path.realpath(__file__))

def resource_path(relativePath):
    """
    Function to detect the correct path of file when working with sourcecode/install or binary.
    :param relativePath: Path to file/data.
    :return: Modified path to file/data.
    """

    try:
        basePath = sys._MEIPASS  # Try if we are running as standalone executable
        # print('Running stand alone executable.')
    except:
        basePath = '/usr/share/multibootusb'  # Check if we run in installed environment
        #if os.path.exists('/usr/share/multibootusb'):
            #print('Running from installed machine.')
        if not os.path.exists(basePath):
            #basePath = os.path.abspath(".")
            basePath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    if os.path.exists(os.path.join(basePath, relativePath)):
        path = os.path.join(basePath, relativePath)
        return path
    elif not os.path.exists(os.path.join(basePath, relativePath)):
        if os.path.exists(os.path.join(os.path.abspath("."), relativePath)):
            basePath = os.path.abspath(".")
        elif os.path.exists(os.path.join(os.path.abspath(".."), relativePath)):
            basePath = os.path.abspath("..")
        path = os.path.join(basePath, relativePath)
        return path


def print_version():
    """
    Simple print the version number of the multibootusb application
    :return:
    """
    print('multibootusb version : ', mbusb_version())


def quote(text):
    """
    Function to quote the input word or sentence.
    :param text:    Any word or sentence.
    :return:        Quoted text or sentence. If already quoted the same text is returned.
    """
    if not is_quoted(text):
        return '"' + text + '"'
    else:
        return text


def is_quoted(text):
    """
    Function to check if word is quoted.
    :param text:    Any word or sentence with or without quote.
    :return:        True if text is quoted else False.
    """
    if text.startswith("""") and text.endswith("""):
        return True
    else:
        return False


def has_digit(word):
    """
    Useful function to detect if input word contain digit.
    :param word:    Any alphanumeric word.
    :return:        True if the word has a digit else False.
    """
    return any(char.isdigit() for char in word)


def sys_64bits():
    """
    Detect if the host system is 64 bit.
    :return:    True if system is 64 bit.
    """
    return sys.maxsize > 2**32


def multibootusb_host_dir():
    """
    Cross platform way to detect multibootusb directory on host system.
    :return: Path to multibootusb directory of host system.
    """
    import tempfile

    if platform.system() == "Linux":
        home_dir = os.path.expanduser('~')
        mbusb_dir = os.path.join(home_dir, ".multibootusb")
    elif platform.system() == "Windows":
        mbusb_dir = os.path.join(tempfile.gettempdir(), "multibootusb")

    return mbusb_dir


def iso_cfg_ext_dir():
    """
    Function to return the path to ISO configuration file extraction directory.
    :return:    Path to directory where ISO config files will be extracted.
    """
    return os.path.join(multibootusb_host_dir(), 'iso_cfg_ext_dir')


def clean_iso_cfg_ext_dir(iso_cfg_ext_dir):
    """
    Clean old ISO config files extracted by previous use of multibootusb.
    :param iso_cfg_ext_dir: Path to config extract directory.
    :return:
    """
    if os.path.exists(iso_cfg_ext_dir):
        filelist = [f for f in os.listdir(iso_cfg_ext_dir)]
        for f in filelist:
            if os.path.isdir(os.path.join(iso_cfg_ext_dir, f)):
                shutil.rmtree(os.path.join(iso_cfg_ext_dir, f))
            else:
                os.remove(os.path.join(iso_cfg_ext_dir, f))
    else:
        print('iso_cfg_ext_dir directory does not exist.')


def copy_mbusb_dir_usb(usb_disk):
    """
    Copy the multibootusb directory to USB mount path.
    :param usb_mount_path: Path to USB mount.
    :return:
    """
    from .iso import iso_size
    from .usb import details

    usb_details = details(usb_disk)
    usb_mount_path = usb_details['mount_point']
    if not os.path.exists(os.path.join(usb_mount_path, "multibootusb")):
        try:
            print('Copying multibootusb directory to', usb_mount_path)
            shutil.copytree(resource_path(os.path.join("data", "multibootusb")), os.path.join(usb_mount_path, "multibootusb"))
            return True
        except:
            return False
    else:
        print('multibootus directory already exist. Not copying.')


def read_input_yes():
    """
    List option and read user input
    :return: True if user selected yes or else false
    """
    yes_list = ['Y', 'y', 'Yes', 'yes', 'YES']
    no_list = ['N', 'n', 'No', 'no', 'NO']
    response = input("Please enter the option listed above : ")
    if response in yes_list:
        return True
    elif response in no_list:
        return False


def strings(file_path):
    """
    Similar to strings command in Linux.
    :param file_path: Path to file as string.
    :return: All printable character of a file.
    """
    import re
    nonprintable = re.compile(b'[^%s]+' % re.escape(string.printable.encode('ascii')))

    with open(file_path, "rb") as f:
        for result in nonprintable.split(f.read()):
            if result:
                yield result.decode('ASCII')


def size_not_enough(iso_link, usb_disk):
    from .iso import iso_size
    from .usb import details
    isoSize = iso_size(iso_link)
    usb_details = details(usb_disk)
    usb_size = usb_details['size_free']
    if isoSize > usb_size:
        return True
    else:
        return False


def mbusb_version():
    version = open(resource_path(os.path.join("data", "version.txt")), 'r').read().strip()
    return version


def prepare_mbusb_host_dir():
    """
    Prepare multibootusb host directory and extract data files for use.
    :return:
    """
    home = multibootusb_host_dir()
    if not os.path.exists(home):
        os.makedirs(home)
    else:
        print("Cleaning old multibootusb directory...")
        shutil.rmtree(home)
        os.makedirs(home)

    if not os.path.exists(os.path.join(home, "preference")):
        os.makedirs(os.path.join(home, "preference"))

    if not os.path.exists(os.path.join(home, "iso_cfg_ext_dir")):
        os.makedirs(os.path.join(home, "iso_cfg_ext_dir"))

    if os.path.exists(os.path.join(home, "syslinux", "bin", "syslinux4")):
        print("Syslinux exist in multibootusb directory...")
    else:
        print("Extracting syslinux to multibootusb directory...")
        if platform.system() == "Linux":
            if sys_64bits() is True:
                print('Host OS is 64 bit...')
                print("Extracting syslinux 64 bit...")
                # print(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_linux_64.zip")))
                with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_linux_64.zip")), "r") as z:
                    z.extractall(home)
            else:
                print("Extracting syslinux 32 bit...")
                with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_linux.zip")), "r") as z:
                    z.extractall(home)
        else:
            with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_windows.zip")), "r") as z:
                z.extractall(home)
        print("Extracting syslinux modules to multibootusb directory...")
        with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_modules.zip")), "r") as z:
                z.extractall(os.path.join(home, "syslinux"))

    '''
    if not os.path.exists(os.path.join(home, "persistence_data")):
        print("Copying persistence data to multibootusb directory...")
        shutil.copytree(resource_path(os.path.join("data", "tools", "persistence_data")),
                        os.path.join(home, "persistence_data"))
    '''
    if platform.system() == "Windows":
        if not os.path.exists(os.path.join(home, "dd")):
            print("Copying dd to multibootusb directory.")
            shutil.copytree(resource_path(os.path.join("data", "tools", "dd")),
                            os.path.join(home, "dd"))

    if os.listdir(os.path.join(home, "iso_cfg_ext_dir")):
        print(os.listdir(os.path.join(home, "iso_cfg_ext_dir")))
        print("iso extract directory is not empty.")
        print("Removing junk files...")
        for files in os.listdir(os.path.join(home, "iso_cfg_ext_dir")):
            if os.path.isdir(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files))):
                print (os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                os.chmod(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)), 0o777)
                shutil.rmtree(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
            else:
                try:
                    print (os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                    os.chmod(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)), 0o777)
                    os.unlink(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                    os.remove(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                except OSError:
                    print("Can't remove the file. Skip it.")

if __name__ == '__main__':
    print(quote("""Test-string"""))
    print(has_digit("test-string-with-01-digit"))
    print(sys_64bits())
    print(multibootusb_host_dir())
    print(iso_cfg_ext_dir())
    strings_test = strings('../../text-stings.bin')
    print(strings_test)
