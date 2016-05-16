# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'progress.ui'
#
# Created: Tue Jan 20 21:19:13 2015
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
        Dialog.resize(400, 100)
        self.gridLayout_2 = QtGui.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout_2.addWidget(self.progressBar, 1, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout_2.addWidget(self.pushButton, 2, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label.setText(_translate("Dialog", "File copy info here.", None))
        self.pushButton.setText(_translate("Dialog", "Start", None))

