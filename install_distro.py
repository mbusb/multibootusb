#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os,  re,  var,  psutil,  threading,  shutil
from PyQt4 import QtGui
from multibootusb_ui import Ui_Dialog

class AppGui(QtGui.QDialog,Ui_Dialog):
	def install_distro(self):
		
