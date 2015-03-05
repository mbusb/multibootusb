#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Name:     persistence.py
# Purpose:  Module to deal with persistence of a selected distro.
# Authors:  Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of GNU General Public License, v.2 or above
from PyQt4 import QtGui
from gui.ui_persistence_size import Ui_Dialog
import sys
import tarfile
import os
import gen_fun

def persistence_distro(distro):
    """
    Function to detect if distro can have persistence option.
    :param distro: Detected distro name.
    :return: Distro name as string or None otherwise.
    """
    if distro == "ubuntu":
        print "Persistence option is available."
        return "ubuntu"
    else:
        return None
    # FIXME to get debian and fedora persistence workable...
    # Able to add successfully but unable to keep persistence data.
    '''
    elif distro == "debian":
        print "Persistence option is available."
        return "debian"
    elif distro == "fedora":
        print "Persistence option is available."
        return "fedora"
    '''


def extract_file(file_path, install_dir):
    """
    Function to extract persistence files to distro install directory.
    :param file_path: Path to persistence file.
    :param install_dir: Path to distro install directory.
    :return:
    """
    tar = tarfile.open(file_path, "r:bz2")
    tar.extractall(install_dir)
    tar.close()


def persistence_extract(distro, persistence_size, mbusb_dir, install_dir):
    """
    Function to detect and extract persistence files to distro install directory.
    :param distro: Detected distro name.
    :param persistence_size: Size of the choosen persistence size.
    :param mbusb_dir: Path to multibootusb directory on host system.
    :param install_dir: Path to distro install directory.
    :return:
    """
    if distro == "ubuntu" or distro == "debian":
        extension = ".ext4.tar.bz2"
    elif distro == "fedora":
        extension = ".tar.bz2"
    persistence_host_file_path = gen_fun.resource_path(os.path.join(mbusb_dir, "persistence_data", persistence_size + extension))
    extract_file(persistence_host_file_path, install_dir)
    if os.path.exists(os.path.join(install_dir, persistence_size + ".ext4")):
        if distro == "ubuntu":
            os.rename(os.path.join(install_dir, persistence_size + ".ext4"), os.path.join(install_dir, "casper-rw"))
        elif distro == "debian":
            os.rename(os.path.join(install_dir, persistence_size + ".ext4"), os.path.join(install_dir, "live-rw"))
    elif os.path.exists(os.path.join(install_dir, persistence_size)):
        if distro == "fedora":
            os.rename(os.path.join(install_dir, persistence_size),
                      os.path.join(install_dir, "overlay-UUID-" + gbl_usb_uuid))


class PersistenceGui(QtGui.QDialog, Ui_Dialog):
    """
    Get persistence size using GUI.
    """
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancel.clicked.connect(self.handleCloseClicked)
        self.ui.choose.clicked.connect(self.handleChooseClicked)

    def handleCloseClicked(self):
        """
        Close GUI.
        :return:
        """
        print "Closing the persistence size chooser window."
        self.close()

    def handleChooseClicked(self):
        """
        Function to return the choosen persistence size.
        :return: Choosen persistence size.
        """
        size = self.gui_persistence_size()
        if size:
            persistence_size = size
            #print persistence_size
            self.close()
            return size

        else:
            QtGui.QMessageBox.information(self, 'No size...',
                                      "No persistence size selected.\n\n"
                                      "Please choose persistence size and click Choose.")

    def gui_persistence_size(self):
        """
        Function to return the choosen persistence size through GUI.
        :return: Choosen persistence size.
        """
        if self.ui.size_256.isChecked():
            return str(256)
        elif self.ui.size_512.isChecked():
            return str(512)
        elif self.ui.size_768.isChecked():
            return str(768)
        elif self.ui.size_1gb.isChecked():
            return str(1024)
        elif self.ui.size_2gb.isChecked():
            return str(2048)
        elif self.ui.size_3gb.isChecked():
            return str(3072)
        elif self.ui.size_4gb.isChecked():
            return str(4096)
        else:
            return False

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = PersistenceGui()
    myapp.show()
    sys.exit(app.exec_())


def get_persistence_size():
    persistance_window = PersistenceGui()
    persistance_window.exec_()
    persistence = persistance_window.gui_persistence_size()
    if persistence is not False:
        return persistence.strip()
    else:
        return 0
