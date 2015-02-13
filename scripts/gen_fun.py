__author__ = 'sundar'
import os
import sys
import shutil
import zipfile
import platform
import usb


def resource_path(relativePath):
    try:
        basePath = sys._MEIPASS  # Try if we are running as standalone executable
    except:
        try:
            basePath = os.path.join(sys.prefix, "multibootusb")  # Check if we run in installed environment
        except:
            basePath = os.path.abspath("")  # Lets check now if we run from source

    if not os.path.exists(os.path.join(basePath, relativePath)):
        if os.path.exists(os.path.join(os.path.abspath(".."), relativePath)):
            basePath = os.path.abspath("..")
        if os.path.exists(os.path.join(os.path.abspath("."), relativePath)):
            basePath = os.path.abspath(".")

    path = os.path.join(basePath, relativePath)
    #print "path is " + path
    if not os.path.exists(path):
        return None

    return path


def copy_mbusb_dir(usb_mount_path):
    if not os.path.exists(os.path.join(usb_mount_path, "multibootusb")):
        try:
            shutil.copytree(resource_path(os.path.join("tools", "multibootusb")), os.path.join(usb_mount_path, "multibootusb"))
            return True
        except:
            return False
    else:
        print "multibootus directory exist. Not copying."


def mbusb_dir():

    import platform
    import tempfile

    if platform.system() == "Linux":
        from os.path import expanduser
        home = expanduser("~")
        mbusb_dir = os.path.join(home, ".multibootusb")
    elif platform.system() == "Windows":
        mbusb_dir = os.path.join(tempfile.gettempdir(), "multibootusb")

    return mbusb_dir


def install_dir(iso_link, usb_mount_path):
    try:
        iso_name = os.path.basename(str(iso_link))
        dir_name = str(os.path.splitext(iso_name)[0])
        install_dir_path = os.path.join(usb_mount_path, "multibootusb", dir_name)
        return install_dir_path
    except:
        return None


def distro_install_dir_exist(iso_link, usb_mount_path):
    install_directory = install_dir(iso_link, usb_mount_path)
    if os.path.exists(install_directory):
        return True


def persistence_size(persistence_option):
    import persistence
    if persistence_option:
        size = persistence.get_persistence_size()
        if size is not False:
            iso_size = size
    else:
        iso_size = 0

    return iso_size


def install_size(iso_link, persistence_size):
    if not persistence_size == 0:
        iso_size = (os.path.getsize(iso_link) / 1024) + (int(persistence_size) * 1024)
    else:
        iso_size = (os.path.getsize(iso_link) / 1024)

    return iso_size


def clean_iso_cfg_ext_dir(iso_cfg_ext_dir):
    if os.path.exists(iso_cfg_ext_dir):
        filelist = [f for f in os.listdir(iso_cfg_ext_dir)]
        #if not filelist:
        for f in filelist:
            if os.path.isdir(os.path.join(iso_cfg_ext_dir, f)):
                shutil.rmtree(os.path.join(iso_cfg_ext_dir, f))
            else:
                os.remove(os.path.join(iso_cfg_ext_dir, f))


def prepare_mbusb_dir():

    home = mbusb_dir()
    if not os.path.exists(home):
        os.makedirs(home)
    else:
        print "Cleaning old multibootusb directory."
        shutil.rmtree(home)
        os.makedirs(home)

    if not os.path.exists(os.path.join(home, "preference")):
        os.makedirs(os.path.join(home, "preference"))

    if not os.path.exists(os.path.join(home, "iso_cfg_ext_dir")):
        os.makedirs(os.path.join(home, "iso_cfg_ext_dir"))

    if os.path.exists(os.path.join(home, "syslinux", "bin", "syslinux4")):
        print "Syslinux exist in multibootusb directory."
    else:
        print "Extracting syslinux to multibootusb directory..."
        if platform.system() == "Linux":
            with zipfile.ZipFile(resource_path(os.path.join("tools", "syslinux", "syslinux_linux.zip")), "r") as z:
                z.extractall(home)
        else:
            with zipfile.ZipFile(resource_path(os.path.join("tools", "syslinux", "syslinux_windows.zip")), "r") as z:
                z.extractall(home)
        print "Extracting syslinux modules to multibootusb directory..."
        print resource_path(os.path.join("tools", "syslinux", "syslinux_modules.zip"))
        with zipfile.ZipFile(resource_path(os.path.join("tools", "syslinux", "syslinux_modules.zip")), "r") as z:
                z.extractall(os.path.join(home, "syslinux"))

    if not os.path.exists(os.path.join(home, "persistence_data")):
        print "Copying persistence data to multibootusb directory."
        shutil.copytree(resource_path(os.path.join("tools", "persistence_data")),
                        os.path.join(home, "persistence_data"))

    if platform.system() == "Linux":
        if os.geteuid() == 0:
            for path, subdirs, files in os.walk(resource_path(os.path.join(home, "tools", "syslinux", "bin"))):
                for name in files:
                    if not name.endswith('.exe'):
                        os.system('chmod ' + '+x ' + resource_path(os.path.join(home, "tools", "syslinux", "bin", name)))

    if os.listdir(os.path.join(home, "iso_cfg_ext_dir")):
        print os.listdir(os.path.join(home, "iso_cfg_ext_dir"))
        print "iso extract directory is not empty."
        print "Removing junk files..."
        for files in os.listdir(os.path.join(home, "iso_cfg_ext_dir")):
            if os.path.isdir(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files))):
                print (os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                os.chmod(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)), 0777)
                shutil.rmtree(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
            else:
                try:
                    print (os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                    os.chmod(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)), 0777)
                    os.unlink(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                    os.remove(os.path.join(os.path.join(home, "iso_cfg_ext_dir", files)))
                except OSError:
                    print "Can't remove the file. Skip it."

def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None