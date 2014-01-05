#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MultibootUSB allows user to install multiple live linux of selected usb.
Created by Sundar and co-authored by Ian Bruce.
"""
from PyQt4 import QtGui
from multibootusb_ui import Ui_Dialog
import sys
import os
import re 
import platform
import tempfile
import subprocess
import shutil
import psutil 
import threading
import admin 
import var, qemu, detect_iso, update_cfg,  uninstall_distro


if platform.system() == "Windows":
    import win32com.client
    if not admin.isUserAdmin():
        admin.runAsAdmin()
        sys.exit(0)

if sys.platform.startswith("linux"):
    import dbus
    from os.path import expanduser
    home = expanduser("~")
    mbusb_dir = os.path.join(home, ".multibootusb")
    #zip = os.path.join(os.getcwd(),  "tools",  "7zip", "linux", "7z")
else:
    mbusb_dir = os.path.join(tempfile.gettempdir(), "multibootusb")
#    resource_path(relative):
    #zip = os.path.join(os.getcwd(),  "tools",  "7zip", "windows", "7z.exe")
    
if not os.path.exists(mbusb_dir):
    os.makedirs(mbusb_dir)
if not os.path.exists(os.path.join(mbusb_dir,  "preference")):
    os.makedirs(os.path.join(mbusb_dir, "preference"))

usb_device = ""
usb_file_system = ""
usb_mount = ""
uninstall_distro_name = ""
usb_label = ""
usb_uuid = ""
usb_size_total = ""
usb_size_avail = ""
usb_size_used = ""
sys_cfg_file = ""
required_syslinux_install = ""
detected_device_details = ""
process_exist = []  # yet to be implemented
password = ""
iso_cfg_ext_dir = os.path.join(mbusb_dir, "iso_cfg_ext_dir")
editors_linux = ["gedit",  "kate", "kwrite"]
editors_win = ["notepad++.exe",  "notepad.exe"]
editor_exit_status = "dummy"
quit_ready = ""
version = ""
zip = ""
#version = open(os.path.join(os.getcwd(), "tools","version.txt"), 'r').read().strip()



if not os.path.exists(iso_cfg_ext_dir):
    os.makedirs(iso_cfg_ext_dir)
if os.listdir(iso_cfg_ext_dir): 
    print os.listdir(iso_cfg_ext_dir)
    print "iso extract directory is not empty."
    print "Removing junk files..."
    for files in os.listdir(iso_cfg_ext_dir):
        os.remove(os.path.join(iso_cfg_ext_dir, files))

"""
def resource_path(relative):
    return os.path.join(
        os.environ.get(
            "_MEIPASS",
            os.path.abspath(".")
        ),
        relative
    )
"""
def resource_path(relativePath):
    try:
        # PyInstaller stores data files in a tmp folder refered to as _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        # If not running as a PyInstaller created binary, try to find the data file as
        # an installed Python egg
        try:
            basePath = os.path.dirname(sys.modules['tools'].__file__)
        except Exception:
            basePath = ''
 
        # If the egg path does not exist, assume we're running as non-packaged
        if not os.path.exists(os.path.join(basePath, relativePath)):
            basePath = 'tootls'
 
    path = os.path.join(basePath, relativePath)
 
    # If the path still doesn't exist, this function won't help you
    if not os.path.exists(path):
        return None
 
    return path

class AppGui(qemu.AppGui,detect_iso.AppGui,update_cfg.AppGui,uninstall_distro.AppGui, QtGui.QDialog,Ui_Dialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)
        global version
        global zip
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.close.clicked.connect(self.on_close_Click)
        #QtGui.qApp.lastWindowClosed.connect(self.on_close_Click)
        self.ui.browse_iso.clicked.connect(self.browse_iso)
        self.ui.create.clicked.connect(self.onCreateClick)
        self.ui.uninstall.clicked.connect(self.uninstall_distro)
        self.ui.comboBox.activated[str].connect(self.onComboChange)
        # Syslinux Tab
        self.ui.install_syslinux.clicked.connect(self.onInstall_syslinuxClick)
        self.ui.edit_syslinux.clicked.connect(self.onedit_syslinux)
        # QEMU Tab
        self.ui.browse_iso_qemu.clicked.connect(self.on_Qemu_Browse_iso_Click)
        self.ui.boot_iso_qemu.clicked.connect(self.on_Qemu_Boot_iso_Click)
        self.ui.boot_usb_qemu.clicked.connect(self.on_Qemu_Boot_usb_Click)
        self.ui.tabWidget.removeTab(3)
        
        version = open(resource_path(os.path.join("tools","version.txt")), 'r').read().strip()
        var.gbl_mbusb_version = version
        
        if sys.platform.startswith("linux"):
            zip = resource_path(os.path.join("tools","7zip", "linux", "7z"))
            var.zip = zip
        else:
            zip = resource_path(os.path.join("tools","7zip","windows","7z.exe"))
            var.zip = zip
        
        if sys.platform.startswith("linux"):
            if os.geteuid() != 0:
                global password
                
                if os.system('which sudo')==0:
                    for x in xrange(3):
                        input,  ok = QtGui.QInputDialog.getText(self,'Password', 
                        'Enter user password::', QtGui.QLineEdit.Password)
                        if ok:
                                password = str(input)
                                var.gbl_pass = password
                                if os.popen('echo ' + password + ' | sudo -S id -u').read().strip() == '0':
                                    break
                                if x == 2 :
                                    print "You have entered wrong password 3 times. Exiting now. "
                                    sys.exit(0)
                        else:
                            print "Password not entered. Exiting now. "
                            sys.exit(0)
                elif os.system('which gksu')==0:
                    os.system("gksu -d "  + sys.executable + " " + sys.argv[0])
                    sys.exit(0)
                elif os.system('which gksudo')==0:
                    os.system("gksudo -d "  + sys.executable + " " + sys.argv[0])
                    sys.exit(0)
                elif os.system('which kdesu')==0:
                    os.system("kdesu -t "  + sys.executable + " " + sys.argv[0])
                    sys.exit(0)
                elif os.system('which kdesudo')==0:
                    os.system("kdesudo -t "  + sys.executable + " " + sys.argv[0])
                    sys.exit(0)
                
                else:
                    QtGui.QMessageBox.information(self, 'No root...', 'multibootusb require Please install either sudo, gksu, kdesu, gksudo or kdesudo then restart multibootusb.')
                    sys.exit(0)
        
        detected_device = self.find_usb()
        
        for device in detected_device :
            self.ui.comboBox.addItem (str(device))
        if self.ui.comboBox.currentText():
            self.onComboChange()
            
    
    def onComboChange(self):
        
        global usb_device
        global usb_file_system
        global usb_mount
        global sys_cfg_file 
        global usb_size_avail
        global usb_size_total
        global usb_size_used
        global usb_uuid
        global usb_label
        
        usb_details = self.get_usb_details()
        
        usb_device = str(usb_details[0])
        var.gbl_usb_device = usb_device
        usb_uuid = str(usb_details[1])
        var.gbl_usb_uuid = usb_uuid 
        usb_label = str(usb_details[2])
        usb_mount = str(usb_details[3])
        var.usb_mount = usb_mount 
        usb_file_system = str(usb_details[4])
        usb_size_total = int(usb_details[5])
        usb_size_avail = int(usb_details[6])
        usb_size_used = int(usb_details[7])
        sys_cfg_file = os.path.join(str(usb_details[3]), "multibootusb",  "syslinux.cfg")
        var.gbl_sys_cfg_file = sys_cfg_file 

        self.update_list_box(sys_cfg_file) 
        
    def browse_iso(self):
        self.ui.lineEdit.clear()
        iso_link = QtGui.QFileDialog.getOpenFileName(self, 'Select an iso...', "",  "ISO Files (*.iso)")

        if iso_link:
            self.ui.lineEdit.insert (iso_link)
        else:
            print ("File not selected.")
            
    def onCreateClick(self):
        self.create_mbusb()
        
    def onInstall_syslinuxClick(self):
        global required_syslinux_install
        required_syslinux_install = 'yes'
        src = str(resource_path(os.path.join("tools","multibootusb")))
        dst = str(os.path.join(str(usb_mount),  "multibootusb"))
        print os.path.join(str(usb_mount),  "multibootusb")
        if self.ui.install_sys_all.isChecked() or self.ui.install_sys_only.isChecked():
            self.install_syslinux(usb_device)
        else:
            QtGui.QMessageBox.information(self, 'No selection...', 'Please select from one of the install syslinux options')
        if self.ui.install_sys_all.isChecked():
            self.copytree(src, dst)
            
    def copytree(self, src, dst, symlinks=False, ignore=None):

        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)
        
    def find_usb(self):
        found = []
        if sys.platform.startswith("linux"):

            bus = dbus.SystemBus()
            ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
            ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks')

            for dev in ud_manager.EnumerateDevices():
                device_obj = bus.get_object("org.freedesktop.UDisks", dev)
                device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
                if device_props.Get('org.freedesktop.UDisks.Device', "DriveConnectionInterface") == "usb" and device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsPartition"):
                    if device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsMounted"):
                        device_file = device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile")
                        found.append(device_file)

                #else:
                 #   print "Device not mounted"

            return found
        
        else:
            oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
            oDrives = oFS.Drives
            for drive in oDrives:
                if drive.DriveType == 1 and drive.IsReady:
                     found.append(drive)
            return found
            
    def get_usb_details(self):

        if sys.platform.startswith("linux"):
            selected_usb_part = str(self.ui.comboBox.currentText())[4:]
            bus = dbus.SystemBus()
            device_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks/devices" + selected_usb_part)
            device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
            selected_usb_device = device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile")
            selected_usb_uuid =   device_props.Get('org.freedesktop.UDisks.Device', "IdUuid")
            selected_usb_label =   device_props.Get('org.freedesktop.UDisks.Device', "IdLabel")
            selected_usb_mount_path =   device_props.Get('org.freedesktop.UDisks.Device', "DeviceMountPaths")[0]
            #selected_usb_size = device_props.Get('org.freedesktop.UDisks.Device', "PartitionSize") 
            selected_usb_file_system = device_props.Get('org.freedesktop.UDisks.Device', "IdType") 
            selected_usb_total_size = psutil.disk_usage(selected_usb_mount_path)[0]
            selected_usb_avail_size = psutil.disk_usage(selected_usb_mount_path)[2]
            selected_usb_used_size = psutil.disk_usage(selected_usb_mount_path)[1]

        else:
            selected_usb_part = str(self.ui.comboBox.currentText())[:2]
            oFS = win32com.client.Dispatch("Scripting.FileSystemObject")
            d = oFS.GetDrive(oFS.GetDriveName(oFS.GetAbsolutePathName(selected_usb_part)))
            selected_usb_device = d.DriveLetter
            serno = "%X" % (long(d.SerialNumber) & 0xFFFFFFFF)
            selected_usb_uuid = serno[:4] + '-' + serno[4:]
            selected_usb_label = d.VolumeName
            selected_usb_mount_path = selected_usb_device + ":\\"
            selected_usb_file_system = d.FileSystem
            selected_usb_total_size = psutil.disk_usage(selected_usb_mount_path)[0]
            selected_usb_avail_size = psutil.disk_usage(selected_usb_mount_path)[2]
            selected_usb_used_size = psutil.disk_usage(selected_usb_mount_path)[1]

        self.ui.usb_size_ttl.setText("Filesystem :: " + selected_usb_file_system )
        self.ui.usb_size_avl.setText("Size :: " + str(self.bytes2human(psutil.disk_usage(selected_usb_mount_path)[0])))
        self.ui.usb_label.setText("Label :: " + selected_usb_label )
        self.ui.usb_dev.setText("USB Device :: " + selected_usb_device )
        self.ui.usb_mount.setText("Mount :: " + str(selected_usb_mount_path ))
            #[0] = selected_usb_device
            #[1] = selected_usb_uuid 
            #[2] = selected_usb_label  
            #[3] = selected_usb_mount_path 
            #[4] = selected_usb_file_system
            #[5 = selected_usb_total_size
            #[6] = selected_usb_avail_size
            #[7] = selected_usb_used_size
        return (selected_usb_device, selected_usb_uuid, selected_usb_label, selected_usb_mount_path, selected_usb_file_system, selected_usb_total_size, selected_usb_avail_size, selected_usb_used_size)
        
    def update_list_box(self, sys_cfg_file):
        if sys_cfg_file:
            self.ui.listWidget.clear()
            if os.path.exists(sys_cfg_file):
                for line in open(sys_cfg_file):
                    if "#start " in line:
                        installed_distro = (line)[7:]
                        self.ui.listWidget.addItem(installed_distro)

    def create_mbusb(self):
        global required_syslinux_install
        
        if not self.ui.comboBox.currentText():
            QtGui.QMessageBox.information(self, 'No USB...', 'No USB found. (Step 1)\n\nInsert USB disk and restart multibootusb')
            self.ui.lineEdit.clear()
        elif not self.ui.lineEdit.text() :
            QtGui.QMessageBox.information(self, 'No ISO...', 'No ISO selected. (Step 2)\n\nPlease choose an iso and click create')
        else:
            iso_path = str(self.ui.lineEdit.text())
            print self.ui.lineEdit.text()
            iso_name = os.path.basename(iso_path)
            self.ui.lineEdit.clear()
            mbusb_dir_content = resource_path(os.path.join("tools","multibootusb"))
            
            # Extract necessary files...
            print zip + " e "+ iso_path + " -y -o" + iso_cfg_ext_dir + "/ *.cfg -r"
            os.system(zip + " e "+ iso_path + " -y -o" + iso_cfg_ext_dir + "/ *.cfg -r")
            var.iso_file_content = subprocess.check_output([zip, 'l', iso_path])
            print var.iso_file_content
            
            
            if os.system(zip + " e "+ iso_path + " -y -o" + iso_cfg_ext_dir + "/ *.cfg -r" ):
                print "success"
            else:
                print "fail"
            #os.system(resource_path(os.path.join("tools","7zip","windows","bsdtar.exe"))  + " -C "+ iso_cfg_ext_dir +  " -xvf " + iso_path + " *.cfg")

            iso_size = int(os.path.getsize(iso_path))
            distro = self.detect_iso(iso_cfg_ext_dir)
            var.distro = distro
            
            if not distro:
                if re.search(r'sources', var.iso_file_content, re.I):
                    distro = "windows"
    
            elif re.search(r'0.img', var.iso_file_content, re.I):
                distro = "opensuse"
                #self.detect_iso_zip_info()
            var.distro = distro

            print var.distro

            if not distro :
                print distro 
                QtGui.QMessageBox.information(self, 'No support...', 'Sorry. ' + iso_name + ' is not supported at the moment\n\nPlease email this issue to feedback.multibootusb@gmail.com')
            elif iso_size > usb_size_avail:
                print iso_size
                print usb_size_avail
                QtGui.QMessageBox.information(self, 'No Space...', 'Sorry. There is no space available on ' + usb_device)
            else:
                mbusb_usb_dir = os.path.join(str(usb_mount), "multibootusb")
                install_dir = os.path.join(mbusb_usb_dir,  os.path.splitext(iso_name)[0])
                
                if os.path.exists(install_dir ):
                    QtGui.QMessageBox.information(self, 'Already exist...', iso_name + ' is already installed on ' + usb_device )
                else:
                    reply = QtGui.QMessageBox.question(self, 'Review selection...',
                                    'Selected USB disk:: %s\n' % usb_device +
                                    'USB mount point:: %s\n' % usb_mount +
                                    'Selected distro:: %s\n\n' % iso_name + 
                                    'Would you like to install the selected distro?',
                                      QtGui.QMessageBox.Yes, QtGui.QMessageBox.No )
                    if reply == QtGui.QMessageBox.Yes:
                        if not os.path.exists(mbusb_usb_dir):
                            required_syslinux_install = 'yes'
                            shutil.copytree (mbusb_dir_content,  os.path.join(str(usb_mount),  "multibootusb"))
                        else:
                                required_syslinux_install = 'no'
                        os.makedirs(install_dir)

                        out_dir = "-o" + install_dir
                        inintial_size = os.path.getsize(iso_path)
                        self.ui.label.setText ("Installing " + iso_name)
                        
                        def copy_process():
                           #subprocess.Popen([zip, 'x', iso_path, '-y',  out_dir ])
                            if var.distro == "opensuse":

                                if sys.platform.startswith("linux"):
                                    if not password == "":
                                        if not os.path.exists ('/tmp/suse/mbusb_suse'):
                                            os.system('echo ' + password + ' | sudo -S mkdir /tmp/mbusb_suse')
                                        else:    
                                            os.system('echo ' + password + ' | sudo -S mount -o loop ' + iso_path + ' /tmp/mbusb_suse')
                                            #shutil.copytree ('/tmp/mbusb_suse/boot', os.path.join(install_dir, 'boot'))
                                            os.system('cp -rfv /tmp/mbusb_suse/boot ' + install_dir + '/boot')
                                        os.system('echo ' + password + ' | sudo -S umount /tmp/mbusb_suse')
                                        os.system('echo ' + password + ' | sudo -S rm -r /tmp/mbusb_suse')
                                elif platform.system() == "Windows":
                                    os.system(resource_path(os.path.join("tools","7zip","windows","bsdtar.exe")) + " -xvf " + iso_path + " boot " + install_dir)

                                shutil.copy(iso_path, usb_mount)
                            elif var.distro == "windows":
                                os.system(zip + " x "+ iso_path + " -y -o" + var.usb_mount + "/")
                            elif var.distro == "ipfire":
                                os.system(zip + " x "+ iso_path + " -y" + out_dir + " boot -r" )
                                os.system(zip + " e "+ iso_path + " -y -o" + var.usb_mount + "/ *.tlz -r" )
                            else:
                               os.system(zip + " x "+ iso_path + " -y" + out_dir )

                        thrd = threading.Thread(target=copy_process, name="copy_process")
                        thrd.start()
                        inintial_usb_size = int(psutil.disk_usage(usb_mount)[1])
                        while thrd.is_alive():
                            current_size = int(psutil.disk_usage(usb_mount)[1])
                            diff_size = int(inintial_usb_size - current_size)
                            percentage = float(1.0*diff_size)/inintial_size*100
                            self.ui.progressBar.setValue(abs(percentage))
                            QtGui.qApp.processEvents()
                        print ("All Completed")
                        self.ui.progressBar.setValue(100)
                        self.ui.progressBar.setValue(0)
                        sys_cfg_file = os.path.join(str(usb_mount), "multibootusb", "syslinux.cfg")
                        self.update_distro_cfg_files(distro, iso_name, install_dir)
                        if required_syslinux_install == 'yes':
                            print "Installing syslinux..."
                            self.install_syslinux(usb_device)
                        self.update_list_box(sys_cfg_file)
                        self.ui.label.clear()
                        if sys.platform.startswith("linux"):
                            os.system('sync')
                        QtGui.QMessageBox.information(self, 'Installation Completed...', iso_name + ' is successfully installed.')
    
    def get_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size
    

                
    def install_syslinux(self, usb_device):
        if required_syslinux_install == "yes":
            if usb_file_system == "vfat" or  usb_file_system == "ntfs" or  usb_file_system == "FAT32":
                if sys.platform.startswith("linux"):
                    if password == "":
                        if os.system('syslinux -i -d /multibootusb ' + usb_device) ==0:
                            if os.system('dd bs=440 count=1 conv=notrunc if=' + resource_path(os.path.join("tools",  "mbr.bin")) + ' of=' + usb_device[:-1]) == 0:
                                print "Syslinux and mbr install was success..."
                    elif  not password == "":
                        syslinux_linux = resource_path(os.path.join("tools","syslinux", "bin", 'syslinux4'))
                        if os.path.exists("/usr/lib/syslinux/bios/"):
                            os.system('cp -rf /usr/lib/syslinux/bios/*.c32 ' + usb_mount + "/multibootusb")
                        #if os.system('echo ' + password + ' | sudo -S syslinux -i -d /multibootusb ' + usb_device)==0:
                        if os.system('echo ' + password + ' | sudo -S ' + syslinux_linux + ' -i -d /multibootusb ' + usb_device)==0:
                            if os.system('echo ' + password + ' | sudo -S dd bs=440 count=1 conv=notrunc if=' + resource_path(os.path.join("tools",  "mbr.bin")) + ' of=' + usb_device[:-1]) == 0:
                                print "Syslinux and mbr install was success..."
#                                print "Copying com modules..."
                                  
                            else:
                                print "mbr install fail..."
                        else:
                                print "syslinux install fail..."
                else:
                    print resource_path(os.path.join("tools",  "syslinux", "bin", 'syslinux4.exe')) + " -maf -d /multibootusb " + usb_device
                    if os.system(resource_path(os.path.join("tools",  "syslinux.exe")) + " -maf -d /multibootusb " + usb_device + ":") == 0:
                        print "syslinux install success."
                    else:
                        print "syslinux install fail."
       

    
    def bytes2human(self, n):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i+1)*10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n
        
    def onedit_syslinux (self):
        global editor_exit_status
        if not os.path.exists (sys_cfg_file):
            print "syslinux.cfg file not found..."
            QtGui.QMessageBox.information(self, 'File not found...',  'Sorry. Unable to locate syslinux.cfg.')
        else:
            
            if sys.platform.startswith("linux"):
                for editor in editors_linux:
                    if os.system('which ' + editor)==0:
                        editor_exit_status  = subprocess.Popen(editor + " " + sys_cfg_file, shell=True).pid
                        if not editor_exit_status:
                            print "syslinux.cfg file successfully opened for append."
                        break
            else:
                for editor in editors_win:
                    if not self.which(editor) == None:
                        print editor
                        editor_exit_status  = subprocess.Popen(editor + " " + sys_cfg_file, shell=True).pid
                        if not editor_exit_status:
                            print "syslinux.cfg file successfully opened for append."
                        break
                        
    def which(self, program):
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
        
    
        
    def on_close_Click(self):
        global quit_ready
        
        if not editor_exit_status == "dummy":
            p = psutil.Process(editor_exit_status)
            try:
                print p.get_open_files()[0]
                QtGui.QMessageBox.information(self, 'Process exist...',  'syslinux.cfg is open for edit.\nPlease save and close file before terminating multibootusb.')
            except:
                print "Process not exit."
                quit_ready = "yes"
                QtGui.qApp.closeAllWindows()
        else:
            quit_ready = "yes"
            print "Closing multibootusb..."
            QtGui.qApp.closeAllWindows()

    
    def closeEvent(self, event):
        
        quit_msg = "Do you really want to exit multibootusb?"
        reply = QtGui.QMessageBox.question(self, 'Exit...', 
                     quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


app = QtGui.QApplication(sys.argv)
window = AppGui()
ui = Ui_Dialog()
window.show()
window.setWindowTitle("MultibootUSB - " + version)
sys.exit(app.exec_())

