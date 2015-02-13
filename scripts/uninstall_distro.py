#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil


from PyQt4 import QtGui, QtCore

from gui.ui_multibootusb import Ui_Dialog
import usb


usb_mount_path = ""
uninstall_distro_name = ""


class AppGui(QtGui.QDialog, Ui_Dialog):

    def uninstall_distro(self, usb_disk):
        global usb_mount_path
        global uninstall_distro_name
        self.progress_thread_uninstall = WorkThreadUninstall()
        self.progress_thread_uninstall.update.connect(self.ui.progressBar.setValue)
        self.progress_thread_uninstall.finished.connect(lambda: self.update_sys_cfg_file(str(self.ui.usb_mount.text()[9:]),
                                                                                         str(self.ui.listWidget.currentItem().text())))

        usb_mount_path = usb.usb_details(usb_disk)['mount']
        print usb_mount_path
        if self.ui.listWidget.currentItem() is None:
            print "Please select a distro from the list."
            QtGui.QMessageBox.information(self, 'No selection.', 'Please select a distro from the list.')
        else:
            uninstall_distro_name = str(self.ui.listWidget.currentItem().text())

            reply = QtGui.QMessageBox.question(self, "Review selection...",
                                       "Are you sure to uninstall " + uninstall_distro_name,
                                      QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:

                if not os.path.exists(str(usb_mount_path) + "/multibootusb/" + uninstall_distro_name.strip()):
                    print "Distro install directory not found. Just updating syslinux.cfg file."
                    self.update_sys_cfg_file(usb_mount_path, uninstall_distro_name)
                else:
                    self.progress_thread_uninstall.start()

    def update_sys_cfg_file(self, usb_mount_path, uninstall_distro_name):
        sys_cfg_file = os.path.join(str(usb_mount_path),  "multibootusb",  "syslinux.cfg")
        if not os.path.exists(sys_cfg_file):
            QtGui.QMessageBox.information(self, 'No file..', 'syslinux.cfg file not found for updating changes.')
        else:
            print "Updating syslinux.cfg file..."
            string = open(sys_cfg_file).read()
            string = re.sub(r'#start ' + uninstall_distro_name.strip() + '.*?' + '#end ' + uninstall_distro_name.strip() + '\s*', '',  string, flags=re.DOTALL)
            config_file = open(sys_cfg_file, "w")
            config_file .write(string)
            config_file .close()
            self.update_list_box(usb_mount_path)
            self.onComboChange()
            QtGui.QMessageBox.information(self, 'Uninstall...',  uninstall_distro_name.strip() + ' ' + 'is successfully removed.')

    def remove_dir(self,usb_mount_path, uninstall_distro_name, distro):
        for path, subdirs, files in os.walk((os.path.join(str(usb_mount_path), "multibootusb", uninstall_distro_name.strip()))):
            for name in files:
                if name.endswith('ldlinux.sys'):
                    os.chmod(os.path.join(path, name), 0777)
                    os.unlink(os.path.join(path, name))
        if distro == "opensuse":
            os.remove(os.path.join(str(usb_mount_path), uninstall_distro_name.strip() + ".iso"))
        elif distro == "windows":
            windows_files = ["SOURCES", "BOOT", "[BOOT]", "EFI", "SUPPORT", "UPGRADE", "AUTORUN.INF", "BOOTMGR", "README.TXT", "SETUP.EXE"]
            for f in windows_files:
                if os.path.isfile(os.path.join(str(usb_mount_path), f)):
                    os.remove(os.path.join(str(usb_mount_path), f))
                elif os.path.isdir(os.path.join(str(usb_mount_path), f)):
                    shutil.rmtree(os.path.join(str(usb_mount_path), f))
        if distro == "ipfire":
            files = os.listdir(str(usb_mount_path))
            for f in files:
                if f.endswith('.tlz'):
                    os.remove(os.path.join(str(usb_mount_path), f))
        elif distro == "trinity-rescue":
            shutil.rmtree(os.path.join(str(usb_mount_path), "multibootusb", "trk3"))

        if os.path.exists(os.path.join(str(usb_mount_path), "multibootusb", uninstall_distro_name.strip())):
            shutil.rmtree(os.path.join(str(usb_mount_path), "multibootusb", uninstall_distro_name.strip()))
        distro = ""


class WorkThreadUninstall(QtCore.QThread):

    global distro

    update = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):

        if os.path.exists(os.path.join(usb_mount_path, uninstall_distro_name, "multibootusb.cfg")):
            with open(os.path.join(usb_mount_path, uninstall_distro_name, "multibootusb.cfg"), "r") as multibootusb_cfg:
                distro = multibootusb_cfg.read().replace('\n', '')
        else:
            distro = ""

        if distro == "opensuse":
            folder_size_to_remove = os.path.getsize(os.path.join(usb_mount_path, uninstall_distro_name.strip()) + ".iso")
            folder_size_to_remove += self.get_size(str(usb_mount_path) + "/multibootusb/" + uninstall_distro_name.strip())
        elif uninstall_distro_name.strip() == "windows":
            distro = "Windows"
            folder_size_to_remove = self.get_size(str(usb_mount_path) + "/SOURCES")
        elif distro == "ipfire":
            folder_size_to_remove = self.get_size(str(usb_mount_path) + "/multibootusb/" + uninstall_distro_name.strip())
            files = os.listdir(os.path.join(str(usb_mount_path)))
            for f in files:
                if f.endswith('.tlz'):
                    folder_size_to_remove += os.path.getsize(os.path.join(str(usb_mount_path), f))
        elif distro == "trinity-rescue":
            folder_size_to_remove = self.get_size(os.path.join(str(usb_mount_path) ,"multibootusb", "trk3"))
            folder_size_to_remove += self.get_size(str(usb_mount_path) + "/multibootusb/" + uninstall_distro_name.strip())
        else:

            folder_size_to_remove = usb.disk_usage(os.path.join(str(usb_mount_path), "multibootusb", uninstall_distro_name.strip())).used
        main_uninstall_class = AppGui()
        self.uninstall_thread = GenericThreadUninstall(main_uninstall_class.remove_dir, usb_mount_path, uninstall_distro_name, distro)
        self.uninstall_thread.start()

        initial_usb_size = usb.disk_usage(usb_mount_path).used

        while self.uninstall_thread.isRunning():
            current_size = usb.disk_usage(usb_mount_path).used
            diff_size = int(initial_usb_size - current_size)
            percentage = float(diff_size)/folder_size_to_remove*100
            #print percentage
            self.update.emit(percentage)
        self.update.emit(100)
        self.update.emit(0)

        if self.uninstall_thread.isFinished():
            self.finished.emit()
            print ("Distro directory has been removed successfully;..")

        return


class GenericThreadUninstall(QtCore.QThread):

    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args, **self.kwargs)
        return