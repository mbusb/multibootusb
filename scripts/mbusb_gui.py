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
from scripts.gui.ui_multibootusb import Ui_MainWindow
from scripts.gui.ui_about import Ui_About
from . import usb
from .gen import *
from .install import *
from .uninstall_distro import *
from .syslinux import *
from .distro import *
from .qemu import *
from .iso import *
#from .imager import *
from .imager import Imager, dd_linux, dd_win
from . import persistence
from . import config
from . import admin
from . import qemu
from .update_cfg_file import update_distro_cfg_files

class AppGui(qemu.Qemu, Imager, QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Main multibootusb GUI manipulation class.
    """

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tabWidget.setCurrentIndex(0)
 #       self.qemu = Qemu()

        self.ui.label_persistence_value.setVisible(False)
        self.ui.label_persistence.setVisible(False)
        self.ui.slider_persistence.setVisible(False)

        config.usb_disk = None
        config.image_path = None

        #  Main Tab
        self.ui.checkbox_all_drives.clicked.connect(self.onAllDrivesClicked)
        self.ui.button_detect_drives.clicked.connect(self.onRefreshClick)
        self.ui.action_Quit.triggered.connect(self.on_close_Click)
        self.ui.action_About.triggered.connect(self.onAboutClick)
        self.ui.button_browse_image.clicked.connect(self.browse_iso)
#         self.ui.combo_drives.activated[str].connect(self.onComboChange)
        self.ui.combo_drives.currentIndexChanged.connect(self.onComboChange)
        self.ui.button_install_distro.clicked.connect(self.onCreateClick)
        self.ui.button_uninstall_distro.clicked.connect(self.OnUninstallClick)
        self.ui.slider_persistence.valueChanged.connect(self.update_slider_text)
#         self.ui.slider_persistence.sliderReleased.connect(self.ui_update_persistence)

        # ISO Imager Tab
        self.ui.button_write_image_to_disk.clicked.connect(self.dd_write)

        #  Syslinux Tab
        self.ui.button_install_syslinux.clicked.connect(self.onInstall_syslinuxClick)
        self.ui.button_edit_syslinux.clicked.connect(self.onedit_syslinux)

        # QEMU Tab
        self.ui.boot_iso_qemu.clicked.connect(self.on_Qemu_Boot_iso_Click)
        self.ui.boot_usb_qemu.clicked.connect(self.on_Qemu_Boot_usb_Click)
#         self.ui.combo_iso_boot_ram.activated[str].connect(self.qemu_iso_ram)
#         self.ui.combo_usb_boot_ram.activated[str].connect(self.qemu_usb_ram)
#         self.ui.boot_usb_qemu.clicked.connect(lambda: self.on_Qemu_Boot_usb_Click(str(self.ui.combo_drives.currentText())))
        #  Update progressbar and status  (Main ISO install)
        self.progress_thread_install = GuiInstallProgress()
        self.progress_thread_install.finished.connect(self.install_syslinux)
        self.progress_thread_install.update.connect(self.ui.progressbar.setValue)
        self.progress_thread_install.status.connect(self.ui.statusbar.showMessage)

        #  Update progressbar and status  (Uninstall from previous install)
        self.progress_thread_uninstall = GuiUninstallProgress()
        self.progress_thread_uninstall.finished.connect(self.uninstall_sys_file_update)
        self.progress_thread_uninstall.update.connect(self.ui.progressbar.setValue)
        self.progress_thread_uninstall.status.connect(self.ui.statusbar.showMessage)

        #  Update progressbar and status  (dd ISO)
        self.progress_thread_dd = DD_Progress()
        self.progress_thread_dd.update.connect(self.ui.progressbar.setValue)
        self.progress_thread_dd.finished.connect(self.dd_finished)
        self.progress_thread_dd.status.connect(self.ui.statusbar.showMessage)

        prepare_mbusb_host_dir()
        self.onRefreshClick()

    def onAllDrivesClicked(self):
        """
        Include fixed drives to available USB devices.
        :return:
        """
        if self.ui.checkbox_all_drives.isChecked() is False:
            self.onRefreshClick()
            return

        reply = QtWidgets.QMessageBox.warning(self, "WARNING!",
"This option enables working with fixed drives\n\
and is potentially VERY DANGEROUS\n\n\
Are you SURE you want to enable it?",
                           QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            self.ui.checkbox_all_drives.setChecked(False)
        elif reply == QtWidgets.QMessageBox.Yes:
            self.ui.checkbox_all_drives.setChecked(True)
            self.onRefreshClick()


    def onAboutClick(self):
        about = QtWidgets.QDialog()
        about.ui = Ui_About()
        about.ui.setupUi(about)
        about.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        about.setWindowTitle("About MultiBootUSB - " + mbusb_version())
        about.setWindowIcon(QtGui.QIcon(resource_path(os.path.join("data", "tools", "multibootusb.png"))))
        about.ui.button_close.clicked.connect(about.close)

        about.exec_()

    def onComboChange(self):
        """
        Detects and updates GUI with populated USB device details.
        :return:
        """
        self.ui.installed_distros.clear()
        config.usb_disk = str(self.ui.combo_drives.currentText())
        config.imager_usb_disk = str(self.ui.combo_drives.currentText())

        if config.usb_disk:
            log("Selected device " + config.usb_disk)
            config.persistence_max_size = persistence.max_disk_persistence(config.usb_disk)

            self.usb_details = usb.details(config.usb_disk)
#             print(self.usb_details)
            config.usb_mount = self.usb_details.get('mount_point', "")
            self.ui.usb_dev.setText(config.usb_disk)

#             if platform.system() == 'Windows':
#                 self.ui.label_usb_vendor.setText("FileSystem:")
#                 self.ui.usb_vendor.setText(self.usb_details['file_system'])
#                 self.ui.label_usb_model.setText("Label: ")
#                 self.ui.usb_model.setText(self.usb_details['label'])
#             else:
#                 self.ui.usb_vendor.setText(self.usb_details['vendor'])
#                 self.ui.usb_model.setText(self.usb_details['model'])

            self.ui.usb_vendor.setText(self.usb_details.get('vendor', ""))
            self.ui.usb_model.setText(self.usb_details.get('model', ""))
            self.ui.usb_size.setText(str(usb.bytes2human(self.usb_details.get('size_total', ""))))
            self.ui.usb_mount.setText(self.usb_details.get('mount_point', ""))
            self.ui.usb_type.setText(self.usb_details.get('devtype', ""))
            self.ui.usb_fs.setText(self.usb_details.get('file_system', ""))

            self.update_list_box(config.usb_disk)
            self.ui_update_persistence()
        else:
            self.ui.usb_dev.clear()
            self.ui.usb_vendor.clear()
            self.ui.usb_model.clear()
            self.ui.usb_size.clear()
            self.ui.usb_mount.clear()
            self.ui.usb_type.clear()
            self.ui.usb_fs.clear()

            log("No USB disk found...")

    def onRefreshClick(self):
        """
        Calls function to detect USB devices.
        :return:
        """
        self.ui.combo_drives.clear()
#        self.ui.imager_disk_label.clear()
#        self.ui.label_imager_disk_label.setVisible(False)
#        self.ui.imager_total_size.clear()
#        self.ui.label_imager_total_size.setVisible(False)
#        self.ui.imager_uuid.clear()
#        self.ui.label_imager_uuid.setVisible(False)
#        self.ui.usb_dev.clear()
#        self.ui.label_usb_dev.setVisible(False)
#        self.ui.usb_vendor.clear()
#        self.ui.label_usb_vendor.setVisible(False)
#        self.ui.usb_model.clear()
#        self.ui.label_usb_model.setVisible(False)
#        self.ui.usb_size.clear()
#        self.ui.label_usb_size.setVisible(False)
#        self.ui.usb_mount.clear()
#        self.ui.label_usb_mount.setVisible(False)

        self.ui.combo_drives.clear()
        if self.ui.checkbox_all_drives.isChecked():
            detected_devices = usb.list_devices(partition=1, fixed=True)
        else:
            detected_devices = usb.list_devices()

        if detected_devices:
            for device in detected_devices:
                    self.ui.combo_drives.addItem(str(device))
            self.ui.combo_drives.setCurrentIndex(0)

    def update_list_box(self, usb_disk):
        """
        Updates listbox with installed distros on selected USB disk.
        :param usb_mount: Selected USB disk from combobox.
        :return:
        """
        distro_list = install_distro_list()
        #sys_cfg_file = os.path.join(str(usb_mount), "multibootusb", "syslinux.cfg")
        if distro_list is not None:
            self.ui.installed_distros.clear()
            for name in distro_list:
                self.ui.installed_distros.addItem(name)
        else:
            if not config.usb_mount:
                log("USB disk is not mounted and can't update list widget...")
            #QtWidgets.QMessageBox.information(self, 'No Install...',
            #                                  'syslinux.cfg does not exist for updating list widget.')

    def browse_iso(self):
        if str(self.ui.image_path.text()):
            self.ui.image_path.clear()
        preference_file_path = os.path.join(multibootusb_host_dir(), "preference", "iso_dir.txt")
        dir_path = ''
        if os.path.exists(preference_file_path):
            dir_path = open(preference_file_path, 'r').read()

        config.image_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select an iso...', dir_path, 'ISO Files (*.iso)')[0]

        if config.image_path:
            default_dir_path = os.path.dirname(config.image_path)
            gen.write_to_file(preference_file_path, default_dir_path)

            if platform.system() == "Windows":
                if "/" in config.image_path:
                    config.image_path = config.image_path.strip().replace("/", "\\")

            self.ui.image_path.insert(str(config.image_path))
            self.ui.label_image_size_value.setText(str(bytes2human(iso_size(config.image_path))))
            self.ui.label_image_size_value.setVisible(True)
            self.ui.label_image_bootable_value.setText(str(is_bootable(config.image_path)))
            self.ui.label_image_bootable_value.setVisible(True)

            if os.path.exists(config.image_path):
                clean_iso_cfg_ext_dir(os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir"))  # Need to be cleaned.
                extract_cfg_file(config.image_path)
                config.distro = distro(iso_cfg_ext_dir(), config.image_path)  # Detect supported distro
                self.ui.label_image_type_value.setText(str(config.distro))
                self.ui.label_image_type_value.setVisible(True)
                if config.distro:
                    per_availability = persistence.persistence_distro(config.distro, config.image_path)
                    if per_availability is not None:
                        config.persistence_available = True
                        if config.usb_disk:
                            per_max_size = persistence.max_disk_persistence(config.usb_disk)
                            config.persistence_max_size = per_max_size
                            log('Persistence Max Size: ' + str(bytes2human(per_max_size)))
                    else:
                        config.persistence_available = False
                        log('Persistence is not available for ' + iso_name(config.image_path))

                    self.ui_update_persistence()
        else:
            log("File not selected...")

    def ui_update_persistence(self):
#         log("===== config.persistence_available = " + str(config.persistence_available))
#         log("===== config.persistence_max_size = " + str(config.persistence_max_size))
#         log("===== config.persistence = " + str(config.persistence))
        if config.persistence_available and config.persistence_max_size:
            self.ui.label_persistence_value.setVisible(True)
            self.ui.label_persistence.setVisible(True)
            self.ui.slider_persistence.setVisible(True)
            self.ui.label_persistence_value.setEnabled(True)
            self.ui.label_persistence.setEnabled(True)
            self.ui.slider_persistence.setEnabled(True)
            self.ui.slider_persistence.setTickInterval(10)
            self.ui.slider_persistence.setSingleStep(10)
            self.ui.slider_persistence.setMaximum(config.persistence_max_size / 1024 / 1024)
#             log("===== getMaximum = " + self.ui.slider_persistence.getMaximum()
        else:
            self.ui.label_persistence_value.setEnabled(False)
            self.ui.label_persistence.setEnabled(False)
            self.ui.slider_persistence.setEnabled(False)
            self.ui.label_persistence_value.setVisible(False)
            self.ui.label_persistence.setVisible(False)
            self.ui.slider_persistence.setVisible(False)

    def ui_disable_persistence(self):
        self.ui.label_persistence_value.setEnabled(False)
        self.ui.label_persistence.setEnabled(False)
        self.ui.slider_persistence.setEnabled(False)
        self.ui.label_persistence_value.setVisible(False)
        self.ui.label_persistence.setVisible(False)
        self.ui.slider_persistence.setVisible(False)


    def update_slider_text(self):
        slide_value = self.ui.slider_persistence.value() * 1024 * 1024
        self.ui.label_persistence_value.setText(bytes2human(slide_value))
        config.persistence = slide_value

    def install_syslinux(self):
        """
        Function to install syslinux on distro directory and on selected USB disks.
        :return:
        """
        self.ui.statusbar.showMessage(str("Status: Installing Syslinux..."))
        syslinux_distro_dir(config.usb_disk, config.image_path, config.distro)
        syslinux_default(config.usb_disk)
        update_distro_cfg_files(config.image_path, config.usb_disk, config.distro, config.persistence)
        self.update_list_box(config.usb_disk)
        if sys.platform.startswith("linux"):
            self.ui.statusbar.showMessage("Status: Sync is in progress...")
            os.system('sync')
        self.ui.statusbar.showMessage("Status: Idle")
        self.ui_disable_persistence()
        log(iso_name(config.image_path) + ' has been successfully installed.')
        QtWidgets.QMessageBox.information(self, 'Finished...', iso_name(config.image_path) + ' has been successfully installed.')
        config.process_exist = None

    def onInstall_syslinuxClick(self):
        """
        Function to install syslinux/extlinux on selected USB disk.
        :return:
        """
        if platform.system() == "Linux" or platform.system() == "Windows":

            if self.ui.install_sys_all.isChecked() or self.ui.install_sys_only.isChecked():
                log("Installing default syslinux on ", config.usb_disk)
                ret = syslinux_default(config.usb_disk)
                if ret is True:
                    if self.ui.install_sys_all.isChecked():
                        log("Copying multibootusb directory to " + config.usb_mount)
                        for dirpath, dirnames, filenames in os.walk(resource_path(os.path.join("tools", "multibootusb"))):
                            for f in filenames:
                                log("Copying " + f)
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
        log("Locating " + sys_cfg_file)
        editor = ''
        if not os.path.exists(sys_cfg_file):
            log("syslinux.cfg file not found...")
            QtWidgets.QMessageBox.information(self, 'File not found...', 'Sorry. Unable to locate syslinux.cfg file.\n'
                                                                     'You can only edit syslinux.cfg file generated by multibootusb.')
        else:
            if platform.system() == "Linux":
                for e in config.editors_linux:
                    if subprocess.call('which ' + e, shell=True) == 0:
                        log("Editor found is " + e)
                        editor = e
                        break
            elif platform.system() == "Windows":
                for e in config.editors_win:
                    if not shutil.which(e) is None:
                        log("Editor found is " + e)
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
        if self.ui.installed_distros.currentItem() is None:
            log("Please select a distro from the list.")
            QtWidgets.QMessageBox.information(self, 'No selection.', 'Please select a distro from the list.')
        else:
            config.uninstall_distro_dir_name = str(self.ui.installed_distros.currentItem().text()).strip()
            reply = QtWidgets.QMessageBox.question(self, "Review selection...",
                                               "Are you sure to uninstall " + config.uninstall_distro_dir_name,
                                                   QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:

                if not os.path.exists(os.path.join(config.usb_mount, 'multibootusb', config.uninstall_distro_dir_name)):
                    log("Distro install directory not found. Just updating syslinux.cfg file.")
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
            self.ui.statusbar.showMessage("Status: Sync in progress...")
            os.system('sync')
        self.ui.statusbar.showMessage("Status: Idle")
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
            log("ERROR: No USB device found.")
            QtWidgets.QMessageBox.information(self, "No Device...",
                                          "No USB device found.\n\nInsert USB and use Refresh USB button to detect USB.")
        elif not config.image_path:
            log("No ISO selected.")
            QtWidgets.QMessageBox.information(self, "No ISO...", "No ISO found.\n\nPlease select an ISO.")
        elif usb.details(config.usb_disk)['mount_point'] == 'No_Mount':
            log("ERROR: USB disk is not mounted.")
            QtWidgets.QMessageBox.information(self, "No Mount...", "USB disk is not mounted.\n"
                                                                   "Please mount USB disk and press refresh USB button.")
        else:
            # clean_iso_cfg_ext_dir(os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir"))  # Need to be cleaned.
            # extract_cfg_file(config.image_path)  # Extract files from ISO
            # config.distro = distro(iso_cfg_ext_dir(), config.image_path)  # Detect supported distro
            usb_details = usb.details(config.usb_disk)
            log("MultiBoot Install: USB Disk: " + config.usb_disk)
            log("MultiBoot Install: USB Label: " + config.usb_label)
            log("MultiBoot Install: USB UUID: " + config.usb_uuid)
            log("MultiBoot Install: USB mount path: " + config.usb_mount)
            log("MultiBoot Install: Disk total size: " + str(usb.bytes2human(usb_details['size_total'])))
            log("MultiBoot Install: Disk used size: " + str(usb.bytes2human(usb_details['size_used'])))
            log("MultiBoot Install: Disk free size: " + str(usb.bytes2human(usb_details['size_free'])))
            log("MultiBoot Install: Filesystem: " + usb_details['file_system'])
            log("MultiBoot Install: Disk vendor: " + usb_details['vendor'])
            log("MultiBoot Install: Disk model: " + usb_details['model'])
            log("MultiBoot Install: ISO file: " + iso_name(config.image_path))

            if os.path.exists(config.image_path):
                self.ui.image_path.clear()
                if config.distro:
                    log("MultiBoot Install: Distro type detected: " + config.distro)
                    copy_mbusb_dir_usb(config.usb_disk)
                    if not os.path.exists(os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path))):
                        config.persistence = self.ui.slider_persistence.value() * 1024 * 1024
                        log("Persistence chosen is " + str(bytes2human(config.persistence)))
                        install_size = iso_size(config.image_path) + config.persistence
                        if install_size >= disk_usage(config.usb_mount).free:
                            log("ERROR: Not enough space available on " + config.usb_disk)
                            QtWidgets.QMessageBox.information(self, "No Space.", "No space available on " + config.usb_disk)
                        else:
                            reply = QtWidgets.QMessageBox.question(self, 'Review selection...',
                                                       'Selected USB disk: %s\n' % config.usb_disk +
                                                       'USB mount point: %s\n' % config.usb_mount +
                                                       'Selected distro: %s\n\n' % iso_name(config.image_path) +
                                                       'Proceed with installation?',
                                                       QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

                            if reply == QtWidgets.QMessageBox.Yes:
                                self.ui.slider_persistence.setEnabled(False)
                                config.process_exist = True
                                self.progress_thread_install.start()

                    else:
                        QtWidgets.QMessageBox.information(self, 'Already exists...',
                                                      os.path.basename(config.image_path) + ' is already installed.')
                else:
                    QtWidgets.QMessageBox.information(self, 'No support...',
                                                  'Sorry.\n' + os.path.basename(config.image_path) +
                                                  ' is not supported at the moment.\n'
                                                  'Please email this issue to feedback.multibootusb@gmail.com')

        # Added to refresh usb disk remaining size after distro installation
        # self.update_gui_usb_info()

    def dd_finished(self):
        """
        Re-enable the blocked widgets for newer use.
        :return:
        """
        self.ui.progressbar.setValue(0)
        self.ui.statusbar.showMessage("Status: Idle")
        self.ui.combo_drives.setEnabled(True)
        self.ui.button_browse_image.setEnabled(True)
#        self.ui.pushbtn_imager_refreshusb.setEnabled(True)
#         self.ui.imager_bootable.setText("Bootable ISO: ")
#         self.ui.imager_iso_size.setText("Image Size: ")
        config.process_exist = None

        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Image succesfully written to USB disk.")
        msgBox.setInformativeText("Reboot to boot from USB or test it from <b>Boot ISO/USB</b> tab.");
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.exec()

    def dd_start(self):
        """
        Function to block the widgets under ISO Imager tab...
        :return:
        """
        self.ui.progressbar.setValue(0)
        self.ui.statusbar.showMessage("Status: Idle")
# FIXME        self.ui.lineEdit_3.clear()
        self.ui.button_browse_image.setEnabled(False)
        self.ui.combo_drives.setEnabled(False)
# FIXME self.ui.pushbtn_imager_refreshusb.setEnabled(False)
        status_text = ("Status: Writing " + os.path.basename(config.image_path) + " to " + config.usb_disk)
        self.ui.statusbar.showMessage(status_text)

    def dd_quit(self):
        self.ui.progressbar.setValue(0)
        self.ui.statusbar.showMessage("Status: Idle")
        self.ui.combo_drives.setEnabled(True)
        self.ui.button_browse_image.setEnabled(True)
        QtWidgets.QMessageBox.information(self, 'Failed!', 'Failed writing image.')

    def dd_write(self):
        if not config.usb_disk:
            QtWidgets.QMessageBox.information(self, 'No USB...', 'Please Insert USB disk and rerun multibootusb.')
        elif not config.image_path:
            QtWidgets.QMessageBox.information(self, 'No ISO...', 'Please select an ISO.')
        else:
            imager = Imager()
            usb_disk_size = int(imager.imager_usb_detail(config.usb_disk, partition=0).total_size)
            self.iso_size = os.path.getsize(config.image_path)
            if self.iso_size >= usb_disk_size:
                QtWidgets.QMessageBox.information(self, "No enough space on disk.", os.path.basename(config.image_path) +
                                              " size is larger than the size of " + config.usb_disk)
            elif gen.process_exist('explorer.exe') is not False:
                # Check if windows explorer is running and inform user to close it.
                QtWidgets.QMessageBox.information(self, "Windows Explorer", "Windows Explorer is running\n"
                                                                            "You need to close it before writing ISO "
                                                                            "image to disk...")
            else:
                reply = QtWidgets.QMessageBox.question \
                    (self, 'Review selection',
                     'Selected disk: %s\n' % config.usb_disk +
                     'Selected image: %s\n\n' % os.path.basename(config.image_path) +
                     'Proceed with writing image to disk?',
                     QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

                if reply == QtWidgets.QMessageBox.Yes:
                    self.dd_start()
                    config.process_exist = True
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
        if config.process_exist == None:
            event.accept()
        else:
            reply = QtWidgets.QMessageBox.question(self, 'Exit MultiBootUSB...',
                                               "A process is still running.\n"
                                               "Do you really want to quit multibootusb?", QtWidgets.QMessageBox.Yes,
                                                QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                log("Closing multibootusb...")
                event.accept()
                sys.exit(0)
            else:
                log("Close event cancelled.")
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
        install_dir = os.path.join(config.usb_mount, "multibootusb", iso_basename(config.image_path))
        self.thread = GenericThread(install_progress)
        status_text = "Status: "
        self.thread.start()
        while self.thread.isRunning():
            if config.status_text.strip():
                config.status_text = config.status_text.replace(install_dir + "/", "Extracting ")
            self.update.emit(config.percentage)
            self.status.emit(config.status_text)
            if not self.thread.isFinished() and config.percentage == 100:
                config.status_text = "Status: Please wait..."
                self.status.emit("Status: Please wait...")

        self.update.emit(100)
        self.update.emit(0)

        self.status.emit("Status: Installing boot loader...")

        if self.thread.isFinished():
            config.status_text = ""
            self.finished.emit()

        log("Distro extraction completed...")

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

        log("Distro uninstall is complete...")

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


def show_admin_info():
    """
    Show simple information box reminding user to run the software with admin/root privilege.
    Only required under Linux as the windows executable always will start with admin privilege.
    :return:
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText('Admin privilege is required to run multibootusb.\n If you are running from source try '
                '\'sudo python3 ./multibootusb\'\n or you can try \'multibootusb-pkexec\' (post install)')
    msg.exec_()


def main_gui():
    app = QtWidgets.QApplication(sys.argv)
#    ui_about = Ui_About()
#    ui = Ui_MainWindow()

    window = AppGui()
    window.show()
    window.setWindowTitle("MultiBootUSB - " + mbusb_version())
    window.setWindowIcon(QtGui.QIcon(resource_path(os.path.join("data", "tools", "multibootusb.png"))))

    if platform.system() == 'Linux':
        if os.getuid() != 0:
            show_admin_info()
    sys.exit(app.exec_())
