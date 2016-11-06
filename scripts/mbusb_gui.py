#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     mbusb_gui.py
# Purpose:  Module to handle multibootusb through gui
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above

import os
import platform
import sys
import signal
from PyQt5 import QtCore, QtGui, QtWidgets
import subprocess
import time
from scripts.gui.ui_multibootusb import Ui_Dialog
from . import usb
from .gen import *
from .install import *
from .uninstall_distro import *
from .syslinux import *
from .distro import *
from .iso import *
from .imager import Imager, dd_linux, dd_win
from . import persistence
from . import config
from . import admin
from . import qemu
from .update_cfg_file import update_distro_cfg_files


class AppGui(qemu.Qemu, Imager, QtWidgets.QDialog, Ui_Dialog):
    """
    Main multibootusb GUI manipulation class.
    """

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        #  Main Tab
        self.ui.detect_usb.clicked.connect(self.onRefereshClick)
        self.ui.close.clicked.connect(self.on_close_Click)
        self.ui.browse_iso.clicked.connect(self.browse_iso)
        self.ui.comboBox.activated[str].connect(self.onComboChange)
        # self.ui.create.clicked.connect(self.update_progress)
        self.ui.create.clicked.connect(self.onCreateClick)
        self.ui.slider_persistence.valueChanged.connect(self.update_slider_text)
        self.ui.uninstall.clicked.connect(self.OnUninstallClick)

        # ISO Imager Tab
        self.ui.pushButton.clicked.connect(self.on_Imager_Browse_iso_Click)
        self.ui.comboBox_2.activated[str].connect(self.onImagerComboChange)
        self.ui.pushbtn_imager_refreshusb.clicked.connect(self.onRefereshClick)
        self.ui.imager_close.clicked.connect(self.on_close_Click)
        self.ui.imager_write.clicked.connect(self.dd_write)

        #  Syslinux Tab
        self.ui.install_syslinux.clicked.connect(self.onInstall_syslinuxClick)
        self.ui.edit_syslinux.clicked.connect(self.onedit_syslinux)

        # QEMU Tab
        self.ui.browse_iso_qemu.clicked.connect(self.on_Qemu_Browse_iso_Click)
        self.ui.boot_iso_qemu.clicked.connect(self.on_Qemu_Boot_iso_Click)
        self.ui.boot_usb_qemu.clicked.connect(lambda: self.on_Qemu_Boot_usb_Click(str(self.ui.comboBox.currentText())))
        # self.ui.tabWidget.removeTab(3)

        #  Update progressbar and status  (Main ISO install)
        self.progress_thread_install = GuiInstallProgress()
        self.progress_thread_install.finished.connect(self.install_syslinux)
        self.progress_thread_install.update.connect(self.ui.progressBar.setValue)
        self.progress_thread_install.status.connect(self.ui.status.setText)

        #  Update progressbar and status  (Uninstall from previous install)
        self.progress_thread_uninstall = GuiUninstallProgress()
        self.progress_thread_uninstall.finished.connect(self.uninstall_sys_file_update)
        self.progress_thread_uninstall.update.connect(self.ui.progressBar.setValue)
        self.progress_thread_uninstall.status.connect(self.ui.status.setText)

        #  Update progressbar and status  (dd ISO)
        self.progress_thread_dd = DD_Progress()
        self.progress_thread_dd.update.connect(self.ui.imager_progressbar.setValue)
        self.progress_thread_dd.finished.connect(self.dd_finished)
        self.progress_thread_dd.status.connect(self.ui.imager_label_status.setText)

        self.add_device()
        prepare_mbusb_host_dir()

    def add_device(self):
        """
        Adds list of available USB devices to GUI combobox.
        :return:
        """
        detected_device = usb.list()
        if bool(detected_device):
            for device in detected_device:
                self.ui.comboBox.addItem(str(device))
                if self.ui.comboBox.currentText():
                    self.onComboChange()

        imager_detected_device = self.imager_list_usb(partition=0)
        if bool(imager_detected_device):
            for disk in imager_detected_device:
                self.ui.comboBox_2.addItem(str(disk))
                self.onImagerComboChange()

    def onComboChange(self):
        """
        Detects and updates GUI with populated USB device details.
        :return:
        """
        self.ui.listWidget.clear()
        config.usb_disk = str(self.ui.comboBox.currentText())
        config.imager_usb_disk = str(self.ui.comboBox_2.currentText())
        if bool(config.usb_disk):
            self.update_gui_oncombobox(config.usb_disk)
        else:
            print("No USB disk found...")

    def onRefereshClick(self):
        """
        Calls function to detect USB devices.
        :return:
        """
        self.ui.comboBox.clear()
        self.ui.comboBox_2.clear()
        self.add_device()

    def update_gui_oncombobox(self, usb_disk):
        self.usb_details = usb.details(usb_disk)
        config.usb_mount = self.usb_details['mount_point']
        self.ui.usb_dev.setText("Drive :: " + usb_disk)
        # self.label.setFont(QtGui.QFont("Times",weight=QtGui.QFont.Bold))
        self.ui.usb_vendor.setText("Vendor :: " + self.usb_details['vendor'])
        self.ui.usb_model.setText("Model :: " + self.usb_details['model'])
        self.ui.usb_size.setText("Total Size :: " + str(usb.bytes2human(self.usb_details['size_total'])))
        self.ui.usb_mount.setText("Mount :: " + self.usb_details['mount_point'])
        self.update_list_box(usb_disk)


    def update_list_box(self, usb_disk):
        """
        Updates listbox with installed distros on selected USB disk.
        :param usb_mount: Selected USB disk from combobox.
        :return:
        """
        distro_list = install_distro_list()
        #sys_cfg_file = os.path.join(str(usb_mount), "multibootusb", "syslinux.cfg")
        if distro_list is not None:
            self.ui.listWidget.clear()
            for name in distro_list:
                self.ui.listWidget.addItem(name)
        else:
            if config.usb_mount == 'No_Mount':
                print("UBS disk is not mounted and can't update list widget...")
            #QtWidgets.QMessageBox.information(self, 'No Install...',
            #                                  'syslinux.cfg does not exist for updating list widget.')

    def browse_iso(self):
        if str(self.ui.lineEdit.text()):
            self.ui.lineEdit.clear()
        config.iso_link = QtWidgets.QFileDialog.getOpenFileName(self, 'Select an iso...', '', 'ISO Files (*.iso)')[0]
        if config.iso_link:
            if platform.system() == "Windows":
                if "/" in config.iso_link:
                    config.iso_link = config.iso_link.strip().replace("/", "\\")
            self.ui.lineEdit.insert(str(config.iso_link))
            if os.path.exists(config.iso_link):
                clean_iso_cfg_ext_dir(
                    os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir"))  # Need to be cleaned.
                extract_cfg_file(config.iso_link)
                if integrity(config.iso_link) is True:
                    config.distro = distro(iso_cfg_ext_dir(), config.iso_link)
                else:
                    QtWidgets.QMessageBox.warning(self, 'ISO Error.', "ISO integrity failed.\n\n"
                                                                      "Please check the downloaded ISO.")
                if config.distro:
                    per_availability = persistence.persistence_distro(config.distro, config.usb_disk, config.iso_link)[0]
                    per_max_size = persistence.persistence_distro(config.distro, config.usb_disk, config.iso_link)[1]
                    if per_availability is not None:
                        self.ui.slider_persistence.setEnabled(True)
                        self.ui.slider_persistence.setTickInterval(10)
                        self.ui.slider_persistence.setSingleStep(10)
                        ui_per_max_size = per_max_size / 1024 / 1024
                        config.persistence = per_max_size
                        self.ui.slider_persistence.setMaximum(ui_per_max_size)
                        print('Persistence Max Size: ', bytes2human(per_max_size))
                    else:
                        print('Persistence is not available for', iso_name(config.iso_link))
        else:
            print("File not selected...")

    def update_slider_text(self):
        slide_value = self.ui.slider_persistence.value() * 1024 * 1024
        self.ui.label_persistence_value.setText(bytes2human(slide_value))
        config.persistence = slide_value

    def install_syslinux(self):
        """
        Function to install syslinux on distro directory and on selected USB disks.
        :return:
        """
        self.ui.status.setText(str("Installing Syslinux..."))
        syslinux_distro_dir(config.usb_disk, config.iso_link, config.distro)
        syslinux_default(config.usb_disk)
        update_distro_cfg_files(config.iso_link, config.usb_disk, config.distro, config.persistence)
        self.update_list_box(config.usb_disk)
        if sys.platform.startswith("linux"):
            self.ui.status.setText("Sync is in progress...")
            os.system('sync')
        self.ui.status.clear()
        QtWidgets.QMessageBox.information(self, 'Finished...', iso_name(config.iso_link) + ' has been successfully installed.')

    def onInstall_syslinuxClick(self):
        """
        Function to install syslinux/extlinux on selected USB disk.
        :return:
        """
        if platform.system() == "Linux" or platform.system() == "Windows":

            if self.ui.install_sys_all.isChecked() or self.ui.install_sys_only.isChecked():
                print("Installing default syslinux on ", config.usb_disk)
                ret = syslinux_default(config.usb_disk)
                if ret is True:
                    if self.ui.install_sys_all.isChecked():
                        print("Copying multibootusb directory to " + config.usb_mount)
                        for dirpath, dirnames, filenames in os.walk(resource_path(os.path.join("tools", "multibootusb"))):
                            for f in filenames:
                                print("Copying " + f)
                                shutil.copy(resource_path(os.path.join(dirpath, f)), os.path.join(self.usb.get_usb(config.usb_disk).mount, "multibootusb"))
                    QtWidgets.QMessageBox.information(self, 'Install Success...',
                                                  'Syslinux installed successfully on ' + config.usb_disk)
                elif ret is False:
                    QtWidgets.QMessageBox.information(self, 'Install error...',
                                                  'Sorry. Syslinux failed to install on ' + config.usb_disk)
            else:
                QtWidgets.QMessageBox.information(self, 'No selection...',
                                              'Please select one of the option from above.')

    def onedit_syslinux(self):
        """
        Function to edit main syslinux.cfg file.
        :return:
        """
        # Function to edit syslinux.cfg file on editors like gedit, notepad etc.
        # Suggest me more editor which can be included in to this function.
        sys_cfg_file = os.path.join(config.usb_mount, "multibootusb", "syslinux.cfg")
        print("Locating " + sys_cfg_file)
        editor = ''
        if not os.path.exists(sys_cfg_file):
            print("syslinux.cfg file not found...")
            QtWidgets.QMessageBox.information(self, 'File not found...', 'Sorry. Unable to locate syslinux.cfg file.\n'
                                                                     'You can only edit syslinux.cfg file generated by multibootusb.')
        else:
            if platform.system() == "Linux":
                for e in config.editors_linux:
                    if subprocess.call('which ' + e, shell=True) == 0:
                        print("Editor found is " + e)
                        editor = e
                        break
            elif platform.system() == "Windows":
                for e in config.editors_win:
                    if not shutil.which(e) is None:
                        print("Editor found is " + e)
                        editor = e
                        break
            if not editor:
                QtWidgets.QMessageBox.information(self, 'Editor not found...',
                                              'Sorry. Installed editor is not supported by multibootusb\n'
                                              'Edit ' + sys_cfg_file + ' manually.\n')
            else:
                try:
                    subprocess.Popen(editor + " '" + sys_cfg_file + "'", shell=True).pid
                except OSError:
                    QtWidgets.QMessageBox.warning(self, 'Error...',
                                              'Failed to open syslinux.cfg file.\n'
                                              'Edit syslinux.cfg file manually.\n')

    def OnUninstallClick(self):
        """
        Triggers a function to uninstall a selected distro.
        :return:
        """
        if self.ui.listWidget.currentItem() is None:
            print("Please select a distro from the list.")
            QtWidgets.QMessageBox.information(self, 'No selection.', 'Please select a distro from the list.')
        else:
            config.uninstall_distro_dir_name = str(self.ui.listWidget.currentItem().text()).strip()
            reply = QtWidgets.QMessageBox.question(self, "Review selection...",
                                               "Are you sure to uninstall " + config.uninstall_distro_dir_name,
                                                   QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:

                if not os.path.exists(os.path.join(config.usb_mount, 'multibootusb', config.uninstall_distro_dir_name)):
                    print("Distro install directory not found. Just updating syslinux.cfg file.")
                    update_sys_cfg_file()
                    #self.uninstall.update_sys_cfg_file()
                else:
                    self.progress_thread_uninstall.start()

    def uninstall_sys_file_update(self):
        """
        Function to remove and update uninstall distro text.
        :return:
        """
        update_sys_cfg_file()
        self.update_list_box(config.usb_mount)
        if sys.platform.startswith("linux"):
            self.ui.status.setText("Sync is in progress...")
            os.system('sync')
        self.ui.status.clear()
        QtWidgets.QMessageBox.information(self, 'Uninstall Complete...',
                                      config.uninstall_distro_dir_name + ' has been successfully removed.')

    def onCreateClick(self):
        """
        Main function to create bootable USB disk.
        :param usb_disk: ComboBox text as detected USB disk.
        :param iso_link: LineEdit text as selected ISO link.
        :return:
        """
        if not config.usb_disk:
            QtWidgets.QMessageBox.information(self, "No Device...",
                                          "No USB device found.\n\nInsert USB and use Refresh USB button to detect USB.")
        elif not config.iso_link:
            QtWidgets.QMessageBox.information(self, "No ISO...", "No ISO found.\n\nPlease use step 2 to choose an ISO.")
        elif usb.details(config.usb_disk)['mount_point'] == 'No_Mount':
            QtWidgets.QMessageBox.information(self, "No Mount...", "USB disk is not mounted.\n"
                                                                   "Please mount USB disk and press refresh USB button.")
        else:
            if not integrity(config.iso_link) is True:
                QtWidgets.QMessageBox.information(self, "Integrity...",
                                              "ISO integrity failed.\n\nPlease check the downloaded ISO.")
            else:
                if os.path.exists(config.iso_link):
                    self.ui.lineEdit.clear()
                    if config.distro:
                        print("Distro type detected is ", config.distro)
                        copy_mbusb_dir_usb(config.usb_disk)
                        if not os.path.exists(os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link))):
                            install_size = iso_size(config.iso_link) + config.persistence
                            # print("Persistence choosen is " + str(persistence_size) + " MB")
                            if install_size >= disk_usage(config.usb_mount).free:
                                QtWidgets.QMessageBox.information(self, "No Space.", "No space available on " +
                                                                  config.usb_disk)
                            else:
                                reply = QtWidgets.QMessageBox.question(self, 'Review selection...',
                                                                   'Selected USB disk:: %s\n' % config.usb_disk +
                                                                   'USB mount point:: %s\n' % config.usb_mount +
                                                                   'Selected distro:: %s\n\n' % iso_name(config.iso_link) +
                                                                   'Would you like to proceed for installation?',
                                                                   QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

                                if reply == QtWidgets.QMessageBox.Yes:
                                    self.ui.slider_persistence.setEnabled(False)
                                    self.progress_thread_install.start()

                        else:
                            QtWidgets.QMessageBox.information(self, 'Already Exist...',
                                                          os.path.basename(config.iso_link) + ' is already installed.')
                    else:
                        QtWidgets.QMessageBox.information(self, 'No support...',
                                                      'Sorry.\n' + os.path.basename(config.iso_link) +
                                                      ' is not supported at the moment\n'
                                                      'Please email this issue to feedback.multibootusb@gmail.com')

        # Added to refresh usb disk remaining size after distro installation
        # self.update_gui_usb_info()

    def dd_finished(self):
        """
        Re-enable the blocked widgets for newer use.
        :return:
        """
        self.ui.imager_progressbar.setValue(0)
        self.ui.imager_label_status.clear()
        self.ui.comboBox_2.setEnabled(True)
        self.ui.pushButton.setEnabled(True)
        self.ui.imager_bootable.setText("Bootable ISO :: ")
        self.ui.imager_iso_size.setText("ISO Size :: ")
        QtWidgets.QMessageBox.information(self, 'Finished...', 'ISO has been written to USB disk.\nPlease reboot your '
                                                           'system to boot from USB.')

    def dd_start(self):
        """
        Function to block the widgets under ISO Imager tab...
        :return:
        """
        self.ui.imager_progressbar.setValue(0)
        self.ui.imager_label_status.clear()
        self.ui.lineEdit_3.clear()
        self.ui.pushButton.setEnabled(False)
        self.ui.comboBox_2.setEnabled(False)
        self.ui.pushbtn_imager_refreshusb.setEnabled(False)
        status_text = ("<b>Writing " + os.path.basename(config.imager_iso_link) + "</b>" + " to " + "<b>" +
                       config.imager_usb_disk_selected + "</b>")
        self.ui.imager_label_status.setText(status_text)

    def dd_quit(self):
        self.ui.imager_progressbar.setValue(0)
        self.ui.imager_label_status.clear()
        self.ui.comboBox_2.setEnabled(True)
        self.ui.pushButton.setEnabled(True)
        QtWidgets.QMessageBox.information(self, 'Failed!', 'Writing ISO failed.')

    def dd_write(self):
        if not config.imager_usb_disk:
            QtWidgets.QMessageBox.information(self, 'No USB...', 'Please Insert USB disk and rerun multibootusb.')
        elif not config.imager_iso_link:
            QtWidgets.QMessageBox.information(self, 'No ISO...', 'Please select an ISO.')
        else:
            usb_disk_size = int(self.imager_usb_detail(config.imager_usb_disk, partition=0).total_size)
            self.iso_size = os.path.getsize(config.imager_iso_link)
            if self.iso_size >= usb_disk_size:
                QtWidgets.QMessageBox.information(self, "No Space.", os.path.basename(config.imager_iso_link) +
                                              " size is larger than the size of " + config.imager_usb_disk)
            else:
                reply = QtWidgets.QMessageBox.question \
                    (self, 'Review selection...',
                     'Selected USB disk:: %s\n' % config.imager_usb_disk +
                     'Selected distro:: %s\n\n' % os.path.basename(config.imager_iso_link) +
                     'Would you like to proceed for installation?',
                     QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

                if reply == QtWidgets.QMessageBox.Yes:
                    self.dd_start()
                    self.progress_thread_dd.start()

    def on_close_Click(self):
        """
        Closes main GUI.
        :return:
        """
        self.close()

    def closeEvent(self, event):
        """
        To capture the main close event.
        :param event: Close event.
        :return:
        """
        reply = QtWidgets.QMessageBox.question(self, 'Exit MultiBootUSB...',
                                           "Do you really want to quit multibootusb?", QtWidgets.QMessageBox.Yes,
                                            QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            print("Closing multibootusb...")
            event.accept()
            sys.exit(0)
        else:
            print("Close event cancelled.")
            event.ignore()


class GuiInstallProgress(QtCore.QThread):
    """
    Update GUI thread during install.
    """
    update = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        install_dir = os.path.join(config.usb_mount, "multibootusb", iso_basename(config.iso_link))
        self.thread = GenericThread(install_progress)
        status_text = ""
        self.thread.start()
        while self.thread.isRunning():
            if config.status_text.strip():
                config.status_text = config.status_text.replace(install_dir + "/", "Extracting ")
            self.update.emit(config.percentage)
            self.status.emit(config.status_text)
            if not self.thread.isFinished() and config.percentage == 100:
                config.status_text = ""
                self.status.emit("Please wait...")

        self.update.emit(100)
        self.update.emit(0)

        self.status.emit("Installing boot loader...")

        if self.thread.isFinished():
            config.status_text = ""
            self.finished.emit()

        print("Distro extraction completed...")

        return


class GuiUninstallProgress(QtCore.QThread):
    """
    Update GUI thread during uninstall.
    """
    update = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.thread = GenericThread(uninstall_progress)

    def __del__(self):
        self.wait()

    def run(self):
        self.thread.start()
        while self.thread.isRunning():
            self.update.emit(config.percentage)
            self.status.emit(config.status_text)
            if not self.thread.isFinished() and config.percentage == 100:
                config.status_text = "Please wait..."
        self.update.emit(100)
        self.update.emit(0)
        config.percentage = 0
        self.status.emit("Updating syslinux.cfg file...")

        if self.thread.isFinished():
            config.status_text = ""
            self.finished.emit()

        print("Distro uninstall is complete...")

        return


class DD_Progress(QtCore.QThread):
    """
    Update GUI progress bar without blocking rest of GUI element when dd process is in progress.
    """
    update = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)

        if platform.system() == 'Linux':
            self.thread = GenericThread(dd_linux)
        elif platform.system() == 'Windows':
            self.thread = GenericThread(dd_win)

    def __del__(self):
        self.wait()

    def run(self):
        self.thread.start()
        while self.thread.isRunning():
            if config.imager_percentage:
                self.update.emit(config.imager_percentage)
            if not self.thread.isFinished() and config.percentage == 100:
                config.imager_status_text = ""
                self.status.emit("Please wait...")

        self.update.emit(100)
        self.update.emit(0)

        if self.thread.isFinished():
            config.status_text = ""
            self.finished.emit()

        return


class GenericThread(QtCore.QThread):

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

def main_gui():
    app = QtWidgets.QApplication(sys.argv)
    window = AppGui()
    ui = Ui_Dialog()
    window.show()
    window.setWindowTitle("MultiBootUSB - " + mbusb_version())
    window.setWindowIcon(QtGui.QIcon(resource_path(os.path.join("data", "tools", "multibootusb.png"))))
    sys.exit(app.exec_())
