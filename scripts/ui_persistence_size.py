# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'persistance_size2.ui'
#
# Created: Sun Dec 21 01:15:35 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(449, 129)
        self.gridLayout_2 = QtGui.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.choose = QtGui.QPushButton(self.groupBox)
        self.choose.setGeometry(QtCore.QRect(310, 68, 96, 26))
        self.choose.setObjectName(_fromUtf8("choose"))
        self.cancel = QtGui.QPushButton(self.groupBox)
        self.cancel.setGeometry(QtCore.QRect(200, 68, 96, 26))
        self.cancel.setObjectName(_fromUtf8("cancel"))
        self.size_256 = QtGui.QRadioButton(self.groupBox)
        self.size_256.setEnabled(True)
        self.size_256.setGeometry(QtCore.QRect(4, 29, 76, 22))
        self.size_256.setObjectName(_fromUtf8("size_256"))
        self.size_512 = QtGui.QRadioButton(self.groupBox)
        self.size_512.setEnabled(True)
        self.size_512.setGeometry(QtCore.QRect(90, 29, 76, 22))
        self.size_512.setObjectName(_fromUtf8("size_512"))
        self.size_768 = QtGui.QRadioButton(self.groupBox)
        self.size_768.setEnabled(True)
        self.size_768.setGeometry(QtCore.QRect(180, 29, 76, 22))
        self.size_768.setObjectName(_fromUtf8("size_768"))
        self.size_1gb = QtGui.QRadioButton(self.groupBox)
        self.size_1gb.setEnabled(True)
        self.size_1gb.setGeometry(QtCore.QRect(260, 29, 76, 22))
        self.size_1gb.setObjectName(_fromUtf8("size_1gb"))
        self.size_2gb = QtGui.QRadioButton(self.groupBox)
        self.size_2gb.setEnabled(True)
        self.size_2gb.setGeometry(QtCore.QRect(348, 29, 76, 22))
        self.size_2gb.setObjectName(_fromUtf8("size_2gb"))
        self.size_3gb = QtGui.QRadioButton(self.groupBox)
        self.size_3gb.setGeometry(QtCore.QRect(4, 68, 76, 22))
        self.size_3gb.setObjectName(_fromUtf8("size_3gb"))
        self.size_4gb = QtGui.QRadioButton(self.groupBox)
        self.size_4gb.setEnabled(True)
        self.size_4gb.setGeometry(QtCore.QRect(90, 68, 76, 22))
        self.size_4gb.setObjectName(_fromUtf8("size_4gb"))
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Persistence Size Chooser...", None))
        self.groupBox.setTitle(_translate("Dialog", "Choose Persistence Size..", None))
        self.choose.setToolTip(_translate("Dialog", "<html><head/><body><p>Choose selected persistance size...</p></body></html>", None))
        self.choose.setText(_translate("Dialog", "Choose", None))
        self.cancel.setToolTip(_translate("Dialog", "<html><head/><body><p>Do not choose anything and close the window.</p></body></html>", None))
        self.cancel.setText(_translate("Dialog", "Cancel", None))
        self.size_256.setText(_translate("Dialog", "256MB", None))
        self.size_512.setText(_translate("Dialog", "512MB", None))
        self.size_768.setText(_translate("Dialog", "768MB", None))
        self.size_1gb.setText(_translate("Dialog", "1GB", None))
        self.size_2gb.setText(_translate("Dialog", "2GB", None))
        self.size_3gb.setText(_translate("Dialog", "3GB", None))
        self.size_4gb.setText(_translate("Dialog", "4GB", None))

