#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os,sys,subprocess,platform
import var
from PyQt4 import QtGui
from multibootusb_ui import Ui_Dialog

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
            basePath = 'tools'

    path = os.path.join(basePath, relativePath)

    # If the path still doesn't exist, this function won't help you
    if not os.path.exists(path):
        return None

    return path

class AppGui(QtGui.QDialog,Ui_Dialog):

    def on_Qemu_Browse_iso_Click(self):
        global qemu_exist 
        global qemu
        global qemu_iso_link
        self.ui.lineEdit_2.clear()
        
        qemu_exist = self.check_qemu_exist()
                
        if qemu_exist == "yes":
            qemu_iso_link = QtGui.QFileDialog.getOpenFileName(self, 'Select an iso...', "",  "ISO Files (*.iso)")
        else:
            QtGui.QMessageBox.information(self, 'No QEMU...', 'Please install qemu to avail this feature.')

        if qemu_iso_link:
            self.ui.lineEdit_2.insert (qemu_iso_link)
        else:
            print ("File not selected.")
            
    def on_Qemu_Boot_iso_Click(self):
        
        global qemu_exit_status
        global qemu_iso_link
        global qemu
        
        if not self.ui.lineEdit_2.text():
            QtGui.QMessageBox.information(self, 'No ISO...', 'No ISO selected.\n\nPlease choose an iso and click Boot ISO.')
        elif not qemu_exist == "yes":
            QtGui.QMessageBox.information(self, 'No QEMU...', 'Please install qemu to avail this feature.')
        else:
            ram = self.qemu_iso_ram()
            if not ram == None:
                self.ui.lineEdit_2.clear()
                if platform.system() == "Windows":
                    #print var.qemu, " -cdrom ", str(qemu_iso_link), " -boot d -m ", ram
                    var.qemu_iso = subprocess.Popen(var.qemu + " -cdrom " + str(qemu_iso_link) + " -boot d -m " + ram, shell=True).pid
                else:
                    print var.qemu + ' -m ' + ram + ' -cdrom ' + str(qemu_iso_link) + ' -boot d'
                    if os.geteuid() == 0:
                        var.qemu_iso = subprocess.Popen(var.qemu + ' -m ' + ram + ' -cdrom ' + str(qemu_iso_link) + ' -boot d', shell=True).pid
                    else:
                        var.qemu_iso = subprocess.Popen('echo ' + var.password + ' | sudo -S ' + var.qemu + ' -m ' + ram + ' -cdrom ' + str(qemu_iso_link) + ' -boot d', shell=True).pid
            else:
                QtGui.QMessageBox.information(self, 'No ram...', 'No ram selected.\n\nPlease choose any ram value and click Boot ISO.')
                
    def on_Qemu_Boot_usb_Click(self):
        global qemu_exit_status
        qemu_exist = self.check_qemu_exist()

        if qemu_exist == "yes":
            ram = self.qemu_usb_ram()
            
        if not ram == None:
            if platform.system() == "Windows":
                disk_number = self.get_physical_disk_number(var.usb_mount[:-1])
                print var.qemu + " -L . -boot c -m " + ram + " -hda //./PhysicalDrive" + disk_number
                parent_dir = os.getcwd()
                os.chdir(var.qemu_dir)
                var.qemu_usb = subprocess.Popen("qemu-system-x86_64.exe -L . -boot c -m "  + ram + " -hda //./PhysicalDrive" + disk_number, shell=True).pid
                os.chdir(parent_dir)
            else:
                if os.geteuid() == 0:
                    var.qemu_usb = subprocess.Popen('qemu-system-x86_64 -hda ' + var.gbl_usb_device [:-1] + ' -m ' + ram + ' -vga std', shell=True).pid
                else:
                    var.qemu_usb = subprocess.Popen('echo ' + var.password + ' | sudo -S qemu-system-x86_64 -hda ' + var.gbl_usb_device [:-1] + ' -m ' + ram + ' -vga std', shell=True).pid
        else:
            QtGui.QMessageBox.information(self, 'No ram...', 'No ram selected.\n\nPlease choose any ram value and click Boot USB.')
            
    def qemu_iso_ram(self):
        if self.ui.ram_iso_256.isChecked():
            return str(256)
        elif self.ui.ram_iso_512.isChecked():
            return str(512)
        elif self.ui.ram_iso_768.isChecked():
            return str(768)
        elif self.ui.ram_iso_1024.isChecked():
            return str(1024)
        elif self.ui.ram_iso_2048.isChecked():
            return str(2048)
        else:
            return None

    def qemu_usb_ram(self):
        if self.ui.ram_usb_256.isChecked():
            return str(256)
        if self.ui.ram_usb_512.isChecked():
            return str(512)
        if self.ui.ram_usb_768.isChecked():
            return str(768)
        if self.ui.ram_usb_1024.isChecked():
            return str(1024)
        if self.ui.ram_usb_2048.isChecked():
            return str(2048)
        else:
            return None
            
    def check_qemu_exist(self):
        if sys.platform.startswith("linux"):
            if os.system('which qemu-system-x86_64')==0:
                print "qemu-system-x86_64 exists"
                var.qemu = "qemu-system-x86_64"
                return "yes"
            else:
                return "no"
            """
            # kvm is not used as of now.
            elif os.system('which kvm')==0:
                print "kvm exists"
                var.qemu = "kvm"
                return "yes"
            """

        else:
            return "yes"



    def get_physical_disk_number(self, usb_disk):
        import wmi
        c = wmi.WMI ()
        for physical_disk in c.Win32_DiskDrive ():
          for partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
              if logical_disk.Caption == usb_disk:
                """
                print physical_disk.Caption
                print partition.Caption
                print logical_disk.Caption
                """
                print "Physical Device Number is " + partition.Caption[6:-14]
                return str(partition.Caption[6:-14])