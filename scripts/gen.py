#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Name:     gen.py
# Purpose:  This 'general' module contain many functions required to be called at many places
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import logging
import sys
import os
import platform
import shutil
import string
import zipfile
import tempfile
import re
import ctypes


def scripts_dir_path():
    return os.path.dirname(os.path.realpath(__file__))


def log(message, info=True, error=False, debug=False):
    """
    Dirty function to log messages to file and also print on screen.
    :param message:
    :param info:
    :param error:
    :param debug:
    :return:
    """
    # LOG_FILE_PATH = os.path.join(multibootusb_host_dir(), 'multibootusb.log')
    LOG_FILE_PATH = mbusb_log_file()
    if os.path.exists(LOG_FILE_PATH):
        log_file_size = os.path.getsize(LOG_FILE_PATH) / (1024.0 * 1024.0)
        if log_file_size > 1:
            print('Removing log file as it crosses beyond 1mb')
            os.remove(LOG_FILE_PATH)
    logging.basicConfig(filename=LOG_FILE_PATH,
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    print(message)

    # remove ANSI color codes from logs
    # message_clean = re.compile(r'\x1b[^m]*m').sub('', message)

    if info is True:
        logging.info(message)
    elif error is not False:
        logging.error(message)
    elif debug is not False:
        logging.debug(message)



def resource_path(relativePath):
    """
    Function to detect the correct path of file when working with sourcecode/install or binary.
    :param relativePath: Path to file/data.
    :return: Modified path to file/data.
    """

    try:
        basePath = sys._MEIPASS  # Try if we are running as standalone executable
        # log('Running stand alone executable.')
    except:
        basePath = '/usr/share/multibootusb'  # Check if we run in installed environment
        #if os.path.exists('/usr/share/multibootusb'):
            #log('Running from installed machine.')
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
    Simple log the version number of the multibootusb application
    :return:
    """
    log('multibootusb version: ' + mbusb_version())


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
    return bool(text.startswith("\"") and text.endswith("\""))


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


def mbusb_log_file():
    """
    Function to genrate path to log file.
    Under linux path is created as /tmp/multibootusb.log
    Under Windows the file is created under installation directory
    """
    if platform.system() == "Linux":
        # home_dir = os.path.expanduser('~')
        # log_file = os.path.join(home_dir, "multibootusb.log")
        log_file = os.path.join(tempfile.gettempdir(), "multibootusb.log")
    elif platform.system() == "Windows":
        # log_file = os.path.join(tempfile.gettempdir(), "multibootusb", "multibootusb.log")
        log_file = os.path.join("multibootusb.log")

    return log_file


def multibootusb_host_dir():
    """
    Cross platform way to detect multibootusb directory on host system.
    :return: Path to multibootusb directory of host system.
    """
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
        log('iso_cfg_ext_dir directory does not exist.')


def copy_mbusb_dir_usb(usb_disk):
    """
    Copy the multibootusb directory to USB mount path.
    :param usb_mount_path: Path to USB mount.
    :return:
    """
#     from .iso import iso_size
    from .usb import details

    usb_details = details(usb_disk)
    usb_mount_path = usb_details['mount_point']
    result = ''
    if not os.path.exists(os.path.join(usb_mount_path, "multibootusb")):
        try:
            log('Copying multibootusb directory to ' + usb_mount_path)
            shutil.copytree(resource_path(os.path.join("data", "multibootusb")), os.path.join(usb_mount_path, "multibootusb"))

            result = True
        except:
            log('multibootusb directory could not be copied to ' + usb_mount_path)
            result = False
    else:
        log('multibootusb directory already exists. Not copying.')

    if not os.path.exists(os.path.join(usb_mount_path, 'EFI', 'BOOT', 'multibootusb_grub2.txt')):
        if not os.path.exists(os.path.join(usb_mount_path, 'EFI', 'BOOT')):
            log('EFI/BOOT directory does not exist. Creating new.')
            os.makedirs(os.path.join(usb_mount_path, 'EFI', 'BOOT'), exist_ok=True)
        if os.path.exists(os.path.join(usb_mount_path, 'EFI')):
            shutil.rmtree(os.path.join(usb_mount_path, 'EFI'))
        try:
            log('Copying EFI directory to ' + usb_mount_path)
            shutil.copytree(resource_path(os.path.join("data", "EFI")), os.path.join(usb_mount_path, "EFI"))
            result = True
        except Exception as e:
            log(e)
            result = False
    else:
        log('EFI directory already exist. Not copying.')

    '''
    # For backward compatibility
    if not os.path.exists(os.path.join(usb_mount_path, 'EFI', 'BOOT', 'bootx64-gpt.efi')):
        shutil.copy(resource_path(os.path.join('data', 'EFI', 'BOOT', 'bootx64-gpt.efi')),
                    os.path.join(usb_mount_path, 'EFI', 'BOOT', 'bootx64-gpt.efi'))

    if not os.path.exists(os.path.join(usb_mount_path, 'EFI', 'BOOT', 'bootx64-msdos.efi')):
        shutil.copy(resource_path(os.path.join('data', 'EFI', 'BOOT', 'bootx64-msdos.efi')),
                    os.path.join(usb_mount_path, 'EFI', 'BOOT', 'bootx64-msdos.efi'))

    if not os.path.exists(os.path.join(usb_mount_path, 'multibootusb', 'grub', 'core-gpt.img')):
        shutil.copy(resource_path(os.path.join('data', 'multibootusb', 'grub', 'core-gpt.img')),
                    os.path.join(usb_mount_path, 'multibootusb', 'grub', 'core-gpt.img'))

    if not os.path.exists(os.path.join(usb_mount_path, 'multibootusb', 'grub', 'core-msdos.img')):
        shutil.copy(resource_path(os.path.join('data', 'multibootusb', 'grub', 'core-msdos.img')),
                    os.path.join(usb_mount_path, 'multibootusb', 'grub', 'core-msdos.img'))
    
    if not os.path.exists(os.path.join(usb_mount_path, 'multibootusb', 'grub', 'x86_64-efi')):
        log("New EFI modules does not exist. Copying now.")
        shutil.copytree(resource_path(os.path.join('data', 'multibootusb', 'grub', 'x86_64-efi')),
                    os.path.join(usb_mount_path, 'multibootusb', 'grub', 'x86_64-efi'))
        log("Replacing gpt efi binary with latest one.")
        os.remove(os.path.join(usb_mount_path, 'EFI', 'BOOT', 'bootx64-gpt.efi'))
        shutil.copy(resource_path(os.path.join('data', 'EFI', 'BOOT', 'bootx64-gpt.efi')),
                    os.path.join(usb_mount_path, 'EFI', 'BOOT', 'bootx64-gpt.efi'))
    '''
    # Warn users about older version
    if not os.path.exists(os.path.join(usb_mount_path, 'multibootusb', 'grub', 'x86_64-efi')):
        log("You have created live usb using old version of multibootusb.")
        log("Please remove EFI and multibootusb directory and reinstall distros again.")
    # Ensue that we have iso directory. Implemented from version 9.0.1
    if not os.path.exists(os.path.join(usb_mount_path, 'multibootusb', 'iso')):
        os.makedirs(os.path.join(usb_mount_path, 'multibootusb', 'iso'))

    # Update the menu files from resource path to USB directory.
    try:
        with zipfile.ZipFile(resource_path(os.path.join('data', 'multibootusb', 'grub', 'menus.zip')), "r") as z:
            z.extractall(os.path.join(usb_mount_path, 'multibootusb', 'grub', 'menus'))
    except:
        log('Unable to extract menu files to USB disk.')

    return result


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


def strings(filename, _min=4):
    with open(filename, errors="ignore") as f:
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= _min:
                yield result
            result = ""
        if len(result) >= _min:  # catch result at EOF
            yield result


def size_not_enough(iso_link, usb_disk):
    from .iso import iso_size
    from .usb import details
    isoSize = iso_size(iso_link)
    usb_details = details(usb_disk)
    usb_size = usb_details['size_free']

    return bool(isoSize > usb_size)


def mbusb_version():
    version = open(resource_path(os.path.join("data", "version.txt")), 'r').read().strip()
    return version


def check_text_in_file(file_path, text):
    """
    Helper function to check if a text exist in a file.
    :param file_path: Path to file
    :param text: Text to be searched
    :return: True if found else False
    """
    if not os.path.exists(file_path):
        return False
    else:
        with open(file_path) as data_file:
            return any(text in line for line in data_file)


def prepare_mbusb_host_dir():
    """
    Prepare multibootusb host directory and extract data files for use.
    :return:
    """
    home = multibootusb_host_dir()
    if not os.path.exists(home):
        os.makedirs(home)
    else:
        log("Cleaning old multibootusb directory...")
        clean_iso_cfg_ext_dir(os.path.join(home, "iso_cfg_ext_dir"))
        #shutil.rmtree(home)
        #os.makedirs(home)

    if not os.path.exists(os.path.join(home, "preference")):
        os.makedirs(os.path.join(home, "preference"))

    if not os.path.exists(os.path.join(home, "iso_cfg_ext_dir")):
        os.makedirs(os.path.join(home, "iso_cfg_ext_dir"))

    if os.path.exists(os.path.join(home, "syslinux", "bin", "syslinux4")):
        log("Syslinux exist in multibootusb directory...")
    else:
        log("Extracting syslinux to multibootusb directory...")
        if platform.system() == "Linux":
            if sys_64bits() is True:
                log('Host OS is 64 bit...')
                log("Extracting syslinux 64 bit...")
                # log(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_linux_64.zip")))
                with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_linux_64.zip")), "r") as z:
                    z.extractall(home)
            else:
                log("Extracting syslinux 32 bit...")
                with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_linux.zip")), "r") as z:
                    z.extractall(home)
        else:
            with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_windows.zip")), "r") as z:
                z.extractall(home)
        log("Extracting syslinux modules to multibootusb directory...")
        with zipfile.ZipFile(resource_path(os.path.join("data", "tools", "syslinux", "syslinux_modules.zip")), "r") as z:
                z.extractall(os.path.join(home, "syslinux"))

    if os.listdir(os.path.join(home, "iso_cfg_ext_dir")):
        log(os.listdir(os.path.join(home, "iso_cfg_ext_dir")))
        log("iso extract directory is not empty.")
        log("Removing junk files...")
        for files in os.listdir(os.path.join(home, "iso_cfg_ext_dir")):
            if os.path.isdir(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files))):
                log(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                os.chmod(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)), 0o777)
                shutil.rmtree(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
            else:
                try:
                    log(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                    os.chmod(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)), 0o777)
                    os.unlink(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                    os.remove(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                except OSError:
                    log("Can't remove the file. Skipping it.")


def grub_efi_exist(grub_efi_path):
    """
    Detect efi present in USB disk is copied by multibootusb.
    :param isolinux_path: Path to "grub efi image"
    :return: True if yes else False
    """
    from . import iso
    if grub_efi_path is not None:
        sl = list(iso.strings(grub_efi_path))
        for strin in sl:
            if re.search(r'multibootusb', strin, re.I):
                return True
        return False


def process_exist(process_name):
    """
    Detect if process exist/ running and kill it.
    :param process_name: process name to check
    :return: True if processis killed else False
    """
    if platform.system() == 'Windows':
        import signal
        import wmi
        c = wmi.WMI()
        for process in c.Win32_Process():
            if process_name in process.Name:
                log(process_name + ' exist...')
                log(str(process.ProcessId) + ' ' + str(process.Name))
                log("Having Windows explorer won't allow dd.exe to write ISO image properly."
                      "\nKilling the process..")
                try:
                    os.kill(process.ProcessId, signal.SIGTERM)
                    return True
                except:
                    log('Unable to kill process ' + str(process.ProcessId))

    return False


def write_to_file(filepath, text):
    """
    Simple function to write a text file
    :param filepath: Path to file
    :param text: Text to be written on to file
    :return:
    """
    with open(filepath, 'w') as f:
        f.write(text.strip())


class MemoryCheck():
    """
    Cross platform way to checks memory of a given system. Works on Linux and Windows.
    psutil is a good option to get memory info. But version 5.0 and only will work.
    Source: https://doeidoei.wordpress.com/2009/03/22/python-tip-3-checking-available-ram-with-python/
    Call this class like this: 
    mem_info = memoryCheck()
    print(mem_info.value)
    """

    def __init__(self):

        if platform.system() == 'Linux':
            self.value = self.linuxRam()
        elif platform.system() == 'Windows':
            self.value = self.windowsRam()
        else:
            log("MemoryCheck Class will only work on Linux and Windows.")

    def windowsRam(self):
        """
        Uses Windows API to check RAM
        """
        kernel32 = ctypes.windll.kernel32
        c_ulong = ctypes.c_ulong

        class MEMORYSTATUS(ctypes.Structure):
            _fields_ = [
                ("dwLength", c_ulong),
                ("dwMemoryLoad", c_ulong),
                ("dwTotalPhys", c_ulong),
                ("dwAvailPhys", c_ulong),
                ("dwTotalPageFile", c_ulong),
                ("dwAvailPageFile", c_ulong),
                ("dwTotalVirtual", c_ulong),
                ("dwAvailVirtual", c_ulong)
            ]

        memoryStatus = MEMORYSTATUS()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
        kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))

        return int(memoryStatus.dwTotalPhys / 1024 ** 2)

    def linuxRam(self):
        """
        Returns the RAM of a Linux system
        """
        totalMemory = os.popen("free -m").readlines()[1].split()[1]
        return int(totalMemory)

if __name__ == '__main__':
    log(quote("""Test-string"""))
    log(has_digit("test-string-with-01-digit"))
    log(sys_64bits())
    log(multibootusb_host_dir())
    log(iso_cfg_ext_dir())
    strings_test = strings('../../text-stings.bin')
    log(strings_test)
