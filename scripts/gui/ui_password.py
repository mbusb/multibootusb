# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'password.ui'
#
# Created: Mon Feb  2 14:14:32 2015
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
        Dialog.resize(228, 88)
        self.gridLayout_2 = QtGui.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cancel = QtGui.QPushButton(Dialog)
        self.cancel.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cancel.setObjectName(_fromUtf8("cancel"))
        self.gridLayout.addWidget(self.cancel, 3, 0, 1, 1)
        self.lineEdit = QtGui.QLineEdit(Dialog)
        self.lineEdit.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.lineEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.gridLayout.addWidget(self.lineEdit, 1, 0, 1, 2)
        self.enter = QtGui.QPushButton(Dialog)
        self.enter.setObjectName(_fromUtf8("enter"))
        self.gridLayout.addWidget(self.enter, 3, 1, 1, 1)
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Enter Password...", None))
        self.cancel.setText(_translate("Dialog", "Cancel", None))
        self.enter.setText(_translate("Dialog", "Enter", None))
        self.label.setText(_translate("Dialog", "Enter user (sudo) password ::", None))

