#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Name:     mbusb_gui.py
# Purpose:  Module to handle multibootusb through gui
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
from functools import partial
import io
import os
import platform
import sys
import signal
from PyQt5 import QtCore, QtGui, QtWidgets
import subprocess
import time
import traceback
import webbrowser

if platform.system() == 'Linux':
        import dbus

from scripts.gui.ui_multibootusb import Ui_MainWindow
from scripts.gui.ui_about import Ui_About
from . import usb
from .gen import *
from .install import *
from . import uninstall_distro
from .syslinux import *
from .distro import *
from .qemu import *
from .iso import *
# from .imager import *
from .imager import Imager, dd_iso_image
from . import persistence
from . import config
from . import admin
from . import qemu
from . import osdriver
from .update_cfg_file import update_distro_cfg_files
import scripts.gui.resources


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

		self.ui.run_fsck_repair.clicked.connect(
            partial(self.onFsckClick, usb.repair_vfat_filesystem))
		self.ui.run_fsck_check.clicked.connect(
            partial(self.onFsckClick, usb.check_vfat_filesystem))

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

		if platform.system() == 'Windows' or os.system('which fsck.vfat') != 0:
			i = self.ui.tabWidget.indexOf(self.ui.tab_fsck)
			if 0<=i:
				self.ui.tabWidget.removeTab(i)

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

		if getattr(config, 'protected_drives', []):
			reply = QtWidgets.QMessageBox.Yes
		else:
			reply = QtWidgets.QMessageBox.warning(
				self, "WARNING!",
				"This option enables working with fixed drives\n"
				"and is potentially VERY DANGEROUS\n\n"
				"Are you SURE you want to enable it?",
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
				QtWidgets.QMessageBox.No)

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
		about.ui.label_6.linkActivated.connect(webbrowser.open_new_tab)
		about.exec_()

	def onComboChange(self):
		"""
		Detects and updates GUI with populated USB device details.
		:return:
		"""
		self.ui.installed_distros.clear()
		config.usb_disk = osdriver.listbox_entry_to_device(
                        self.ui.combo_drives.currentText())
		if config.usb_disk == 0 or config.usb_disk:
			# Get the GPT status of the disk and store it on a variable
			try:
				usb.gpt_device(config.usb_disk)
				config.imager_usb_disk \
					= self.ui.combo_drives.currentText()
				config.usb_details \
					= usb.details(config.usb_disk)
			except Exception as e:
				o = io.StringIO()
				traceback.print_exc(None, o)
				log(o.getvalue())
				QtWidgets.QMessageBox.critical(
				    self, "The disk/partition is not usable.",
				    str(e))
				self.ui.combo_drives.setCurrentIndex(0)
				# Above statement triggers call to this method.
				return
			log("Selected device " +
                            osdriver.usb_disk_desc(config.usb_disk))
			self.update_target_info()
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
		detected_devices = usb.list_devices(
			fixed=self.ui.checkbox_all_drives.isChecked())
		if not detected_devices:
			return
		protected_drives = getattr(config, 'protected_drives', [])
		for device in detected_devices:
			if all(not device.startswith(d) for d in protected_drives):
				self.ui.combo_drives.addItem(str(device))
		self.ui.combo_drives.setCurrentIndex(0)

	def update_list_box(self, usb_disk):
		"""
		Updates listbox with installed distros on selected USB disk.
		:param usb_mount: Selected USB disk from combobox.
		:return:
		"""
		distro_list = uninstall_distro.install_distro_list()
		if distro_list is not None:
			self.ui.installed_distros.clear()
			for name in distro_list:
				self.ui.installed_distros.addItem(name)
		else:
			if not config.usb_mount:
				log("USB disk is not mounted and can't update list widget...")

	def browse_iso(self):
		if str(self.ui.image_path.text()):
			self.ui.image_path.clear()
		preference_file_path = os.path.join(multibootusb_host_dir(),
											"preference", "iso_dir.txt")
		dir_path = ''
		if os.path.exists(preference_file_path):
			dir_path = open(preference_file_path, 'r').read()

		config.image_path = QtWidgets.QFileDialog.getOpenFileName(
			self, 'Select an iso...', dir_path,
			'ISO Files (*.iso);; Zip Files(*.zip);; '
			'Img Files(*.img);; All Files(*.*)')[0]

		if config.image_path:
			# sanity checks
			if not is_readable(config.image_path):
				QtWidgets.QMessageBox.critical(
					self,
					"ISO Not readable",
					"Sorry, the file \"{0}\" is not readable.".format(
						config.image_path)
				)
				return
			if iso_size(config.image_path) == 0:
				QtWidgets.QMessageBox.critical(
					self,
					"ISO is an empty file",
					"Sorry, the file \"{0}\" contains no data.".format(
						config.image_path)
				)
				return
			default_dir_path = os.path.dirname(config.image_path)
			gen.write_to_file(preference_file_path, default_dir_path)

			# Detect supported distro
			try:
				clean_iso_cfg_ext_dir(	 # Need to be cleaned.
					os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir"))
				extract_cfg_file(config.image_path)
				config.distro = distro(iso_cfg_ext_dir(), config.image_path,
									   expose_exception=True)
			except Exception as exc:
				QtWidgets.QMessageBox.critical(
					self,
					"Failure to detect distro type",
					'Sorry, failed in examining "{0}" to detect distro type '
					'due to the following reason.\n\n"{1}".'
					.format(config.image_path, exc)
				)
				return

			if platform.system() == "Windows":
				if "/" in config.image_path:
					config.image_path = config.image_path.strip().replace("/", "\\")

			self.ui.image_path.insert(str(config.image_path))
			self.ui.label_image_size_value.setText(str(bytes2human(iso_size(config.image_path))))
			self.ui.label_image_size_value.setVisible(True)
			self.ui.label_image_bootable_value.setText(str(is_bootable(config.image_path)))
			self.ui.label_image_bootable_value.setVisible(True)

			if os.path.exists(config.image_path):
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
						log('Persistence support is not available for '
							+ iso_name(config.image_path))

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

	def get_controls(self):
		return [
			self.ui.combo_drives,
			self.ui.checkbox_all_drives,
			self.ui.button_detect_drives,
			self.ui.button_browse_image,
			self.ui.image_path,
			self.ui.tabWidget,
			self.ui.button_install_distro,
			self.ui.button_uninstall_distro,
		]

	def ui_disable_controls(self):
		[c.setEnabled(False) for c in self.get_controls()]

	def ui_enable_controls(self):
		[c.setEnabled(True) for c in self.get_controls()]

	def update_slider_text(self):
		slide_value = self.ui.slider_persistence.value() * 1024 * 1024
		self.ui.label_persistence_value.setText(bytes2human(slide_value))
		config.persistence = slide_value

	def install_syslinux(self):
		try:
			try:
				self.install_syslinux_impl()
			finally:
				config.process_exist = None
				self.ui_enable_controls()
		except (KeyboardInterrupt, SystemExit):
			raise
		except:
			uninstall_distro.do_uninstall_distro(
				config.distro, iso_basename(config.image_path))
			o = io.StringIO()
			traceback.print_exc(None, o)
			QtWidgets.QMessageBox.information(
				self, 'install_syslinux() failed',
				o.getvalue())
			log("install_syslinux() failed.")
			log(o.getvalue())

	def install_syslinux_impl(self):
		"""
		Function to install syslinux on distro directory and on selected USB disks.
		:return:
		"""
		self.ui.statusbar.showMessage(str("Status: Installing Syslinux..."))
		syslinux_distro_dir(config.usb_disk, config.image_path, config.distro)
		syslinux_default(config.usb_disk)
		replace_grub_binary()
		update_distro_cfg_files(config.image_path, config.usb_disk,
					config.distro, config.persistence)
		self.update_list_box(config.usb_disk)
		self.ui.statusbar.showMessage("Status: Idle")
		self.ui_disable_persistence()
		log(iso_name(config.image_path) + ' has been successfully installed.')
		QtWidgets.QMessageBox.information(self, 'Finished...',
										  iso_name(config.image_path) + ' has been successfully installed.')

	def onInstall_syslinuxClick(self):
		"""
		Function to install syslinux/extlinux on selected USB disk, except extlinux.cfg and syslinux.cfg.
		:return:
		"""

		self.ui_disable_controls()
		if not config.usb_disk:
			log("ERROR Syslinux Install :  No USB device found.")
			QtWidgets.QMessageBox.information(self, "No Device...",
											  "No USB device found.\n\nInsert USB and use Refresh USB button to detect USB.")
		elif platform.system() == "Linux" or platform.system() == "Windows":
			if self.ui.check_install_sys_all.isChecked() or self.ui.check_install_sys_only.isChecked():
				if platform.system() == 'Linux' and config.usb_disk[-1].isdigit() is False:
					gen.log('Selected USB is a disk. Please select a disk partition from the drop down list')
					QtWidgets.QMessageBox.information(self, 'No Partition...!',
													  'USB disk selected doesn\'t contain a partition.\n'
													  'Please select the partition (ending '
													  'with a digit eg. /dev/sdb1)\nfrom the drop down list.')

				else:
					log("Installing default syslinux on " + config.usb_disk)
					ret = syslinux_default(config.usb_disk)
					if ret is True and \
					   self.ui.check_install_sys_all.isChecked():
						log("Copying multibootusb directory to " +
							config.usb_mount)
						src_root = resource_path(
							os.path.join("data", "multibootusb"))
						cutoff = len(src_root) + 1
						dst_root = os.path.join(config.usb_mount,
												"multibootusb")
						if not os.path.exists(dst_root):
							os.makedirs(dst_root)
						excludes = ['extlinux.cfg', 'syslinux.cfg']
						for dirpath, dirnames, filenames in os.walk(src_root):
							subdir_part = dirpath[cutoff:]
							dest_dir = os.path.join(dst_root, subdir_part)
							if not os.path.exists(dest_dir):
								os.makedirs(dest_dir)
							for f in filenames:
								dest_fp = os.path.join(dest_dir, f)
								if f in excludes and os.path.exists(dest_fp):
									continue
								# log("Copying " + f)
								shutil.copy(os.path.join(dirpath, f),
											dest_fp)
						QtWidgets.QMessageBox.information(self, 'Install Success...',
														  'Syslinux installed successfully on ' + config.usb_disk)
					elif ret is False:
						QtWidgets.QMessageBox.information(self, 'Install error...',
														  'Sorry. Syslinux failed to install on ' + config.usb_disk)
			else:
				QtWidgets.QMessageBox.information(self, 'No selection...',
												  'Please select one of the option from above.')

		self.ui_enable_controls()


	def onFsckClick(self, fsck_func):
		try:
			self.onFsckClick_impl(fsck_func)
		except (KeyboardInterrupt, SystemExit):
			raise
		except:
			o = io.StringIO()
			traceback.print_exc(None, o)
			QtWidgets.QMessageBox.information(
				self, 'Failed to run fsck',
				o.getvalue())

	def onFsckClick_impl(self, fsck_func):
		if not config.usb_disk:
			QtWidgets.QMessageBox.information(
				self, 'No partition is selected',
				'Please select the partition to check.')
			return
		if not config.usb_disk[-1:].isdigit():
			QtWidgets.QMessageBox.information(
				self, 'Selected device is not partition',
				'Please select a partition not a disk.')
			return
		output = []
		with usb.UnmountedContext(config.usb_disk, self.update_usb_mount):
			fsck_func(config.usb_disk, output)
		for resultcode, msgout, cmd in output:
			QtWidgets.QMessageBox.information(
                self, 'Integrity Check',
                 cmd + ' said:\n' + str(msgout[0], 'utf-8'))

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

		self.ui_disable_controls()

		if self.ui.installed_distros.currentItem() is None:
			log("Please select a distro from the list.")
			QtWidgets.QMessageBox.information(self, 'No selection.', 'Please select a distro from the list.')
			self.ui_enable_controls()
		else:
			config.uninstall_distro_dir_name = str(
				self.ui.installed_distros.currentItem().text()).strip()
			reply = QtWidgets.QMessageBox.question(
				self, "Review selection...",
				"Are you sure to uninstall " + config.uninstall_distro_dir_name,
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
				QtWidgets.QMessageBox.No)

			if reply == QtWidgets.QMessageBox.Yes:
				if not os.path.exists(
						os.path.join(config.usb_mount, 'multibootusb',
									 config.uninstall_distro_dir_name)):
					log("Distro install directory not found. "
						"Just updating syslinux.cfg and grub.cfg.")
					uninstall_distro.update_sys_cfg_file(config.uninstall_distro_dir_name)
					uninstall_distro.update_grub_cfg_file(config.uninstall_distro_dir_name)
					self.uninstall_sys_file_update()
					# self.uninstall.update_sys_cfg_file()
					self.ui_enable_controls()
				else:
					self.progress_thread_uninstall.start()
			else:
				self.ui_enable_controls()

	def uninstall_sys_file_update(self):
		"""
		Function to remove and update uninstall distro text.
		:return:
		"""

		# This function is already called from 'do_uninstall_distro()'
		# update_sys_cfg_file(config.uninstall_distro_dir_name)

		self.update_list_box(config.usb_mount)
		self.ui.statusbar.showMessage("Status: Idle")
		QtWidgets.QMessageBox.information(self, 'Uninstall Complete...',
										  config.uninstall_distro_dir_name + ' has been successfully removed.')
		self.ui_enable_controls()

	def onCreateClick(self):
		installing = False
		self.ui_disable_controls()
		try:
			installing = self.onCreateClick_impl()
		finally:
			if not installing:
				self.ui_enable_controls()

	def onCreateClick_impl(self):
		"""
		Main function to create bootable USB disk.
		:param usb_disk: ComboBox text as detected USB disk.
		:param iso_link: LineEdit text as selected ISO link.
		:return:
		"""
		for cond, log_msg, dialog_title, dialog_msg in [
				(lambda: config.usb_disk is None,
				 'ERROR: No USB device found.',
				 'No Device...',
				 'No USB device found.\n\nInsert USB and '
				 'use Refresh USB button to detect USB.'),
				(lambda: not config.image_path,
				 'No ISO selected.',
				 'No ISO...',
				 'No ISO found.\n\nPlease select an ISO.'),
				(lambda: ' ' in
				 os.path.basename(config.image_path),
				 'Spaces in iso-file name is not allowed.',
				 'Bad ISO filename...',
				 'Filename that contains space(s) is not '
				 'supported.')]:
			if cond():
				QtWidgets.QMessageBox.information(
					self, dialog_title, dialog_msg)
				return False

		usb_details = config.usb_details
		if usb_details['mount_point'] == 'No_Mount':
			log("ERROR: USB disk is not mounted.")
			QtWidgets.QMessageBox.information(
				self, "No Mount...",
				"USB disk is not mounted.\n"
				"Please mount USB disk and press refresh "
				"USB button.")
			return False
		if config.usb_details['devtype'] == 'disk':
			gen.log('Selected USB is a physical disk. '
                                'Please select '
				'a partition or volume from the drop down list')
			QtWidgets.QMessageBox.information(
				self, 'No Partition...!',
				'Selected USB is a physical disk. '
				'Please select a partition (e.g. /dev/sdc1) '
                                'or a volume (e.g. G:) '
				'from the drop down list.')
			return False
		if 0 < config.persistence and \
			 persistence.detect_missing_tools(config.distro):
			QtWidgets.QMessageBox.information(
				self, 'Missing tools...!',
				persistence.detect_missing_tools(
				config.distro))
			return False
		if not self.check_remount():
			self.update_target_info()
			return False
		
                # clean_iso_cfg_ext_dir(os.path.join(multibootusb_host_dir(), "iso_cfg_ext_dir"))  # Need to be cleaned.
                # extract_cfg_file(config.image_path)  # Extract files from ISO
                # config.distro = distro(iso_cfg_ext_dir(), config.image_path)	# Detect supported distro
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

		if not os.path.exists(config.image_path):
			return False

		# self.ui.image_path.clear()
		if not config.distro:
			QtWidgets.QMessageBox.information(
				self, 'No support...',
				'Sorry.\n' +
				os.path.basename(config.image_path) +
				' is not supported at the moment.\n'
				'Please email this issue to '
				'feedback.multibootusb@gmail.com')
			return False

		log("MultiBoot Install: Distro type detected: " + config.distro)
		full_image_path = os.path.join(
			config.usb_mount, "multibootusb",
			iso_basename(config.image_path))
		if os.path.exists(full_image_path):
			QtWidgets.QMessageBox.information(
				self, 'Already exists...',
				os.path.basename(config.image_path) +
				' is already installed.')
			return False

		config.persistence = self.ui.slider_persistence.value() \
				     * 1024 * 1024
		log("Persistence chosen is " +
		    str(bytes2human(config.persistence)))
		install_size = iso_size(config.image_path) + config.persistence
		if install_size >= disk_usage(config.usb_mount).free:
			log("ERROR: Not enough space available on " +
			    config.usb_disk)
			QtWidgets.QMessageBox.information(
				self, "No Space.",
				"No space available on " + config.usb_disk)
			return False

		msg = '''
The ISO sleceted is not supported at the moment.
You can try booting ISO using memdisk.
Distro can be uninstalled anytime from main menu.

Proceed with installation?'''.lstrip() if config.distro == 'memdisk_iso' else \
        '''
Selected USB disk: %s
USB mount point: %s
Selected distro: %s

Log location: %s

Proceed with installation?'''.lstrip() % \
	(config.usb_disk, config.usb_mount, iso_name(config.image_path),
	 osdriver.mbusb_log_file())
		reply = QtWidgets.QMessageBox.question(
			self, 'Review selection...', msg)
		if reply == QtWidgets.QMessageBox.Yes:
			self.ui.slider_persistence.setEnabled(False)
			copy_mbusb_dir_usb(config.usb_disk)
			config.process_exist = True
			self.progress_thread_install.start()
			return True

		return False


	def dd_finished(self):
		"""
		Re-enable the blocked widgets for newer use.
		:return:
		"""
		self.ui.progressbar.setValue(0)
		self.ui.statusbar.showMessage("Status: Idle")
		config.process_exist = None

		msgBox = QtWidgets.QMessageBox()
		if self.progress_thread_dd.error:
			title = "Failed to write the iso image to the USB disk."
			msg = self.progress_thread_dd.error
		else:
			title = "Image succesfully written to USB disk."
			msg = "Reboot to boot from USB or test it from " \
			  "<b>Boot ISO/USB</b> tab."
		msgBox.setText(title)
		msgBox.setInformativeText(msg);
		msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
		msgBox.setIcon(QtWidgets.QMessageBox.Information)
		msgBox.exec_()

		self.ui_enable_controls()

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
		status_text = ("Status: Writing " +
                               os.path.basename(config.image_path) + " to " +
                               osdriver.usb_disk_desc(config.usb_disk))
		self.ui.statusbar.showMessage(status_text)

	def dd_quit(self):
		self.ui.progressbar.setValue(0)
		self.ui.statusbar.showMessage("Status: Idle")
		self.ui.combo_drives.setEnabled(True)
		self.ui.button_browse_image.setEnabled(True)
		QtWidgets.QMessageBox.information(self, 'Failed!', 'Failed writing image.')

	def dd_write(self):
		self.ui_disable_controls()

		if not config.usb_disk:
			QtWidgets.QMessageBox.information(self, 'No USB disk selected',
											  'Please insert USB disk and click "Detect Drives".')
			self.ui_enable_controls()
		elif not config.image_path:
			QtWidgets.QMessageBox.information(self, 'No ISO selected', 'Please select an ISO.')
			self.ui_enable_controls()
		else:
			imager = Imager()
			if config.usb_details['devtype'] == "partition":
				gen.log('Selected device is a partition. Please select a disk from the drop down list')
				QtWidgets.QMessageBox.information(self, 'Incompatible device', 'Selected device (%s) is a partition!\n'
																			   'ISO must be written to a whole disk.'
																			   '\n\nPlease select a disk from the drop down list.' % config.usb_disk)
				self.ui_enable_controls()
			else:
				usb_disk_size = int(imager.imager_usb_detail(config.usb_disk).total_size)
				self.iso_size = os.path.getsize(config.image_path)
				if self.iso_size >= usb_disk_size:
					QtWidgets.QMessageBox.information(self, "No enough space on disk.",
													  os.path.basename(config.image_path) +
													  " size is larger than the size of " + osdriver.usb_disk_desc(config.usb_disk))
					self.ui_enable_controls()
				# elif gen.process_exist('explorer.exe') is not False:
				#    # Check if windows explorer is running and inform user to close it.
				#    QtWidgets.QMessageBox.information(self, "Windows Explorer", "Windows Explorer is running\n"
				#                                                                "You need to close it before writing ISO "
				#                                                                "image to disk...")
				else:
					reply = QtWidgets.QMessageBox.question \
						(self, 'Review selection',
						 'Selected disk: %s\n' % osdriver.usb_disk_desc(config.usb_disk) +
						 'Selected image: %s\n\n' % os.path.basename(config.image_path) +
						 'Proceed with writing image to disk?',
						 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

					if reply == QtWidgets.QMessageBox.Yes:
						self.dd_start()
						config.process_exist = True
						self.progress_thread_dd.start()
					elif reply == QtWidgets.QMessageBox.No:
						self.ui_enable_controls()

	def on_close_Click(self):
		"""
		Closes main GUI.
		:return:
		"""
		self.close()

	def update_usb_mount(self, new_usb_details):
		config.update_usb_mount(new_usb_details)
		self.ui.usb_mount.setText(config.usb_mount)

	def check_remount(self):
		if config.usb_details['file_system'] != 'vfat':
			return True
		try:
			with UnmountedContext(config.usb_disk,
								  self.update_usb_mount) as m:
				pass
			return True
		except usb.RemountError:
			QtWidgets.QMessageBox.critical(
				self,"Remount failed.",
				"Could not remount '{0}'. "
				"Please make sure no process has open "
				"handle(s) to previously mounted filesystem."
				.format(config.usb_disk))
			return False

	def update_target_info(self):

		usb_total_size= str(usb.bytes2human(config.usb_details.get('size_total', "")))
		usb_free_size= str(usb.bytes2human(config.usb_details.get('size_free', "")))
		config.persistence_max_size = persistence.max_disk_persistence(config.usb_disk)
		config.usb_mount = config.usb_details.get('mount_point', "")
		self.ui.usb_dev.setText(osdriver.usb_disk_desc(config.usb_disk))

		self.ui.usb_vendor.setText(config.usb_details.get('vendor', ""))
		self.ui.usb_model.setText(config.usb_details.get('model', ""))
		self.ui.usb_size.setText('Free :: ' + usb_free_size + ' / Total :: ' + usb_total_size)
		self.ui.usb_mount.setText(config.usb_details.get('mount_point', ""))
		self.ui.usb_type.setText(config.usb_details.get('devtype', ""))
		self.ui.usb_fs.setText(config.usb_details.get('file_system', ""))
		
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
												   "Do you really want to quit multibootusb?",
												   QtWidgets.QMessageBox.Yes,
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
			time.sleep(0.1)

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
		self.thread = GenericThread(uninstall_distro.uninstall_progress)

	def __del__(self):
		self.wait()

	def run(self):
		self.thread.start()

		while self.thread.isRunning():
			self.update.emit(config.percentage)
			self.status.emit(config.status_text)
			if not self.thread.isFinished() and config.percentage == 100:
				config.status_text = "Please wait..."
			time.sleep(0.1)

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
		self.error = None
		self.thread = GenericThread(partial(dd_iso_image, self))

	def __del__(self):
		self.wait()

	def set_error(self, error):
		self.error = error

	def run(self):
		config.imager_percentage =  0
		self.thread.start()
		while self.thread.isRunning():
			if config.imager_percentage:
				self.update.emit(config.imager_percentage)
			if not self.thread.isFinished() and \
			   config.percentage == 100:
				config.imager_status_text = ""
				self.status.emit("Please wait...")
			time.sleep(0.1)

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
	if os.path.exists('scripts'):
		msg.setText('Admin privilege is required to run multibootusb.\n'
					'Try  \'sudo python3 ./multibootusb\'\n')
	else:
		msg.setText('Admin privilege is required to run multibootusb.\n'
					'Try  \'multibootusb-pkexec\'\n')
	msg.exec_()


def main_gui():
	app = QtWidgets.QApplication(sys.argv)
	#    ui_about = Ui_About()
	#    ui = Ui_MainWindow()

	if platform.system() == 'Linux' and os.getuid() != 0:
		show_admin_info()
		sys.exit(2)

	else:
		window = AppGui()
		window.show()
		window.setWindowTitle("MultiBootUSB - " + mbusb_version())
		window.setWindowIcon(QtGui.QIcon(resource_path(os.path.join("data", "tools", "multibootusb.png"))))
	sys.exit(app.exec_())
