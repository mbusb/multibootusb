#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from ui_persistence_size import Ui_Dialog
import sys
import var
import tarfile
import os

def persistence_distro(distro):
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


def extract_file(file_path, to_directory):
    tar = tarfile.open(file_path, "r:bz2")
    tar.extractall(to_directory)
    tar.close()

def persistence_extract(mbusb_dir, install_dir):
    if var.distro == "ubuntu" or var.distro == "debian":
        extension = ".ext4.tar.bz2"
    elif var.distro == "fedora":
        extension = ".tar.bz2"
    persistence_host_file_path = os.path.join(mbusb_dir, "persistence_data", var.persistence_size + extension)
    extract_file(persistence_host_file_path, install_dir, )
    if os.path.exists(os.path.join(install_dir, var.persistence_size + ".ext4")):
        if var.distro == "ubuntu":
            os.rename(os.path.join(install_dir, var.persistence_size + ".ext4"), os.path.join(install_dir, "casper-rw"))
        elif var.distro == "debian":
            os.rename(os.path.join(install_dir, var.persistence_size + ".ext4"), os.path.join(install_dir, "live-rw"))
    elif os.path.exists(os.path.join(install_dir, var.persistence_size)):
        if var.distro == "fedora":
            os.rename(os.path.join(install_dir, var.persistence_size),
                      os.path.join(install_dir, "overlay-UUID-" + var.gbl_usb_uuid))


class PersistenceGui(QtGui.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancel.clicked.connect(self.handleCloseClicked)
        self.ui.choose.clicked.connect(self.handleChooseClicked)

    def handleCloseClicked(self):
        print "Closing the persistence size chooser window."
        QtGui.qApp.closeAllWindows()
        return None


    def handleChooseClicked(self):
        size = self.gui_persistence_size()
        if size:
            var.persistence_size = size
            print var.persistence_size
            self.close()
        else:
            QtGui.QMessageBox.information(self, 'No size...',
                                      "No persistence size selected.\n\n"
                                      "Please choose persistence size and click Choose.")

    def gui_persistence_size(self):
        if self.ui.size_256.isChecked():
            print "Chosen 256MB persistence size."
            return str(256)
        elif self.ui.size_512.isChecked():
            print "Chosen 512MB persistence size."
            return str(512)
        elif self.ui.size_768.isChecked():
            print "Chosen 768MB persistence size."
            return str(768)
        elif self.ui.size_1gb.isChecked():
            print "Chosen 1GB persistence size."
            return "1g"
        elif self.ui.size_2gb.isChecked():
            print "Chosen 2GB persistence size."
            return "2g"
        elif self.ui.size_3gb.isChecked():
            print "Chosen 3GB persistence size."
            return "3g"
        elif self.ui.size_4gb.isChecked():
            print "Chosen 4GB persistence size."
            return "4g"
        else:
            return None

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = PersistenceGui()
    myapp.show()
    sys.exit(app.exec_())
