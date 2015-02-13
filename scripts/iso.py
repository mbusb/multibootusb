__author__ = 'sundar'
import os
import platform
from isodump import ISO9660
import subprocess
import shutil
import gen_fun


def iso_extract_full(iso_path, dest_dir):
    iso9660fs = ISO9660(iso_path)
    try:
        iso9660fs.writeDir("/", dest_dir)
    except:
        print "ISO extraction failed."


def iso_install_dir_name(iso_link):
    try:
        iso_name = os.path.basename(str(iso_link))
        dir_name = str(os.path.splitext(iso_name)[0])
        return dir_name
    except:
        return None


def iso_name(iso_link):
    try:
        name = os.path.basename(str(iso_link))
        return name
    except:
        return None

def iso_check_integrity(iso_path):
    if os.path.exists(iso_path):
        iso9660fs = ISO9660(iso_path)
        if iso9660fs.checkIntegrity():
            print "ISO passed."
            return True
        else:
            print "ISO failed."
            return False


def iso_check_bootable(iso_path):

    if os.path.exists(iso_path):
        f = open(iso_path)
        f.seek(510)
        h = f.read(2)
        if h == "U\xaa":
            print "Bootable"
            f.close()
            return True
        else:
            print "Not bootable"
            return False


def iso_extract_file(iso_path, dest_dir, filter):
    if os.path.exists(iso_path) and os.path.exists(dest_dir):
        iso9660fs = ISO9660(iso_path)
        iso9660fs.writeDir("/", dest_dir, filter)


def install_distro(distro, iso_path, usb_mount_path, install_dir, persistence_size):

    if not os.path.exists(os.path.join(usb_mount_path, "multibootusb")):
        print "Copying multibootusb directory to " + usb_mount_path
        shutil.copytree(gen_fun.resource_path(os.path.join("tools", "multibootusb")), os.path.join(usb_mount_path, "multibootusb"))
    if not os.path.exists(install_dir):
        os.mkdir(install_dir)
        multibootusb_config = open(os.path.join(install_dir, "multibootusb.cfg"), "w")
        multibootusb_config.write(distro)
        multibootusb_config.close()
    print "Install dir is " + install_dir

    if distro == "opensuse":
        try:
            iso_extract_file(iso_path, install_dir, "boot")
            if platform.system() == "Windows":
                subprocess.call(["xcopy",iso_path, usb_mount_path], shell=True)  # Have to use xcopy as python file copy is dead slow.
            elif platform.system() == "Linux":
                shutil.copy(iso_path, usb_mount_path)
        except:
            return None
    elif distro == "Windows":
        print "Extracting iso to " + usb_mount_path
        iso_extract_full(iso_path, usb_mount_path)
    elif distro == "ipfire":
        iso_extract_file(iso_path, install_dir, "boot")
        iso_extract_file(iso_path, usb_mount_path, ".tlz")
    elif distro == "zenwalk":
        iso_extract_file(iso_path, install_dir, "kernel")
        iso_extract_file(iso_path, install_dir, "kernel")
        if platform.system() == "Windows":
            subprocess.call(["xcopy",iso_path,install_dir], shell=True)
        elif platform.system() == "Linux":
            shutil.copy(iso_path, install_dir)
        elif distro == "salix-live":
            iso_extract_file(iso_path, install_dir, "boot")
            if platform.system() == "Windows":
                subprocess.call("xcopy " + iso_path + " " + install_dir, shell=True)
            elif platform.system() == "Linux":
                shutil.copy(iso_path, install_dir)
    else:
        iso_extract_full(iso_path, install_dir)

    if persistence_size:
        import persistence
        home = gen_fun.mbusb_dir()
        if not persistence_size == 0:
            #persistence_option = int(persistence.get_persistence_size()) * 1024
            persistence.persistence_extract(distro, str(persistence_size), home, install_dir)


def isolinux_bin_dir(iso_path):
    if os.path.exists(iso_path):
        iso9660fs = ISO9660(iso_path)
        iso_file_list = iso9660fs.readDir("/")
        if any("isolinux.bin" in s.lower() for s in iso_file_list):
            for f in iso_file_list:
                if 'isolinux.bin' in f.lower():
                    isolinux_bin_dir = os.path.dirname(f)
                    return isolinux_bin_dir
        else:
            return False

def detect_iso(iso_link, iso_cfg_ext_dir):
    """
    Function to detect supported distros.
    """
    import os, re, platform
    if platform.system() == "Linux" or platform.system() == "Windows":
        for path, subdirs, files in os.walk(iso_cfg_ext_dir):
            for name in files:
                if name.endswith('.cfg') or name.endswith('.CFG'):
                    try:
                        string = open(os.path.join(path, name)).read()
                    except IOError:
                        return "Read Error."
                    else:
                        if re.search(r'ubcd', string, re.I):
                            return "ubcd"
                        elif re.search(r'hbcd', string, re.I):
                            return "hbcd"
                        elif re.search(r'systemrescuecd', string, re.I):
                            return "systemrescuecd"
                        elif re.search(r'pmagic|partedmagic', string, re.I):
                            return "parted-magic"
                        elif re.search(r'mgalive', string,
                                       re.I):  # mounting fat filesystem hard coded in to initrd. Can be modifed only under linux.
                            return "mageialive"
                        elif re.search(r'archisolabel|misolabel', string, re.I):
                            return "arch"
                        elif re.search(r'chakraisolabel', string, re.I):
                            return "chakra"
                        elif re.search(r'boot=live', string, re.I):
                            return "debian"
                        elif re.search(r'solydx', string, re.I):
                            return "solydx"
                        elif re.search(r'knoppix', string, re.I):
                            return "knoppix"
                        elif re.search(r'root=live', string, re.I):
                            return "fedora"
                        elif re.search(r'redhat', string, re.I):
                            return "redhat"
                        #elif re.search(r'suse', string, re.I):
                        #   return "suse"
                        elif re.search(r'opensuse', string,
                                       re.I):
                            return "opensuse"
                        elif re.search(
                                r'slitaz|dban|ophcrack|tinycore|rescue.cpi|xpud|untangle|4mlinux|partition wizard|riplinux|lebel dummy',
                                string, re.I):
                            return "slitaz"
                        elif re.search(r'boot=casper', string, re.I):
                            return "ubuntu"
                        elif re.search(r'wifislax', string, re.I):
                            return "wifislax"
                        elif re.search(r'slax', string, re.I):
                            return "slax"
                        elif re.search(r'sms|vector|autoexec', string, re.I):
                            return "sms"
                        elif re.search(r'antix', string, re.I):
                            return "antix"
                        elif re.search(r'porteus', string, re.I):
                            return "porteus"
                        elif re.search(r'livecd=livecd|PCLinuxOS', string, re.I):
                            return "pclinuxos"
                        elif re.search(r'looptype=squashfs', string, re.I):
                            return "gentoo"
                        elif re.search(r'finnix', string, re.I):
                            return "finnix"
                        elif re.search(r'wifiway', string, re.I):
                            return "wifiway"
                        elif re.search(r'puppy', string, re.I):
                            return "puppy"
                        elif re.search(r'ipcop', string, re.I):
                            return "ipcop"
                        elif re.search(r'ipfire', string, re.I):
                            return "ipfire"
                        elif re.search(r'zenwalk|slack|salix', string, re.I) and re.search(r'live', string, re.I):
                            return "salix-live"
                        elif re.search(r'zenwalk|slack|salix', string, re.I):
                            return "zenwalk"
                        elif re.search(r'ubuntu server', string, re.I):
                            return "ubuntu-server"
                        elif re.search(r'Welcome to CentOS', string, re.I):
                            return "centos-net-minimal"
                        elif re.search(r'Trinity Rescue Kit', string, re.I):
                            return "trinity-rescue"

        distro = detect_iso_from_file_list(iso_link)
        if distro:
            return distro

def detect_iso_from_file_list(iso_path):
    if os.path.exists(iso_path):
        print "ISO exist."
        iso9660fs = ISO9660(iso_path)
        iso_file_list = iso9660fs.readDir("/")
        if any("sources" in s.lower() for s in iso_file_list):
            return "Windows"
        elif any("config.isoclient" in s.lower() for s in iso_file_list):
            return "opensuse"
        elif any("dban" in s.lower() for s in iso_file_list):
            return "slitaz"
        else:
            print iso_file_list