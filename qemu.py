#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os,  sys,  subprocess
import var
from PyQt4 import QtGui
from multibootusb_ui import Ui_Dialog

qemu = ""
qemu_exist = ""
qemu_exit_status = "dummy"
qemu_iso_link = ""


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
            self.ui.lineEdit_2.clear()
            ram = self.qemu_iso_ram()
            if not ram == None:
                print qemu + ' -enable-kvm -m ' + ram + ' -cdrom ' + str(qemu_iso_link) + ' -boot d'
                qemu_exit_status = subprocess.Popen('qemu-system-x86_64 -enable-kvm -m ' + ram + ' -cdrom ' + str(qemu_iso_link) + ' -boot d', shell=True).pid
            else:
                QtGui.QMessageBox.information(self, 'No ram...', 'No ram selected.\n\nPlease choose any ram value and click Boot ISO.')
                
    def on_Qemu_Boot_usb_Click(self):
        global qemu_exit_status
        qemu_exist = self.check_qemu_exist()

        if qemu_exist == "yes":
            ram = self.qemu_usb_ram()
            
        if not ram == None:
            qemu_exit_status = subprocess.Popen('echo ' + var.gbl_pass + ' | sudo -S qemu-system-x86_64 -enable-kvm -hda ' + var.gbl_usb_device [:-1] + ' -m ' + ram + ' -vga std', shell=True).pid
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
            if os.system('which qemu-x86_64')==0:
                print "qemu-x86_64 exists"
            elif os.system('which kvm')==0:
                print "kvm exists"
        return "yes"

        
