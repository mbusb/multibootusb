# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'about.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(498, 369)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(About.sizePolicy().hasHeightForWidth())
        About.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(About)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout_11 = QtWidgets.QGridLayout()
        self.gridLayout_11.setObjectName("gridLayout_11")
        self.label_6 = QtWidgets.QLabel(About)
        self.label_6.setObjectName("label_6")
        self.gridLayout_11.addWidget(self.label_6, 1, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_11.addItem(spacerItem, 1, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_11.addItem(spacerItem1, 1, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_11.addItem(spacerItem2, 0, 1, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_11.addItem(spacerItem3, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_11)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.button_close = QtWidgets.QPushButton(About)
        self.button_close.setObjectName("button_close")
        self.horizontalLayout.addWidget(self.button_close)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(About)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "Dialog"))
        self.label_6.setText(_translate("About", "<html><head/><body><p align=\"center\">An advanced bootable usb creator with option to install/uninstall multiple distros.</p><p align=\"center\">This software is written in Python and PyQt. </p><p align=\"center\">Copyright  2010-2017  Sundar</p><p align=\"center\"><span style=\" font-weight:600;\">Author(s)</span>: Sundar, Ian Bruce, LiQiong Lee and Alin Trăistaru (alindt)</p><p align=\"center\"><span style=\" font-weight:600;\">Licence</span>: GPL version 2 or later</p><p align=\"center\"><span style=\" font-weight:600;\">Home page</span>: <a href=\"http://multibootusb.org\"><span style=\" text-decoration: underline; color:#0000ff;\">http://multibootusb.org</span></a></p><p align=\"center\"><span style=\" font-weight:600;\">Help/Email</span>: feedback.multibootusb@gmail.com</p><p align=\"center\"><span style=\" font-weight:600;\">Source Code</span>: <a href=\"https://github.com/mbusb/multibootusb\"><span style=\" text-decoration: underline; color:#0000ff;\">https://github.com/mbusb/multibootusb</span></a></p><p><br/></p></body></html>"))
        self.button_close.setText(_translate("About", "Close"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    About = QtWidgets.QDialog()
    ui = Ui_About()
    ui.setupUi(About)
    About.show()
    sys.exit(app.exec_())
