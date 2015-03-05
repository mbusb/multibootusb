#!/usr/bin/env python
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4
# Name:     admin.py
# Purpose:  Module to ask for admin rights under Linux and Windows
# Authors:  Originally developed by Preston Landers (for windows) and modified for multibootusb by Sundar
# Licence:  This file is a part of multibootusb package. You can redistribute it or modify
# under the terms of the same license as Python 2.6.5

##
## (C) COPYRIGHT © Preston Landers 2010
## Released under the same license as Python 2.6.5
##

"""
User Access Control for Microsoft Windows Vista and higher.  This is
only for the Windows platform.

This will relaunch either the current script - with all the same command
line parameters - or else you can provide a different script/program to
run.  If the current user doesn't normally have admin rights, he'll be
prompted for an admin password. Otherwise he just gets the UAC prompt.

This is meant to be used something like this::

    if not pyuac.isUserAdmin():
        return pyuac.runAsAdmin()

    # otherwise carry on doing whatever...

See L{runAsAdmin} for the main interface.

"""
import os
import traceback
import types
import platform


def isUserAdmin():
    """
    @return: True if the current user is an 'Admin' whatever that means
    (root on Unix), otherwise False.

    Warning: The inner function fails unless you have Windows XP SP2 or
    higher. The failure causes a traceback to be printed and this
    function to return False.
    """

    if platform.system() == "Windows":
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            traceback.print_exc()
            print "Admin check failed, assuming not an admin."
            return False
    elif platform.system() == "Linux":
        return os.getuid() == 0
    else:
        raise RuntimeError, "Unsupported operating system for this module: %s" % (os.name,)


def runAsAdmin(cmdLine=None, wait=True):
    """
    Attempt to relaunch the current script as an admin using the same
    command line parameters.  Pass cmdLine in to override and set a new
    command.  It must be a list of [command, arg1, arg2...] format.

    Set wait to False to avoid waiting for the sub-process to finish. You
    will not be able to fetch the exit code of the process if wait is
    False.

    Returns the sub-process return code, unless wait is False in which
    case it returns None.

    @WARNING: this function only works on Windows.
    """

    #if os.name == 'nt':
    #    raise RuntimeError, "This function is only implemented on Windows."
    if platform.system() == "Windows":

        import win32api, win32con, win32event, win32process
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon

        python_exe = sys.executable

        if cmdLine is None:
            cmdLine = [python_exe] + sys.argv
        elif type(cmdLine) not in (types.TupleType, types.ListType):
            raise ValueError, "cmdLine is not a sequence."
        cmd = '"%s"' % (cmdLine[0],)
        # XXX TODO: isn't there a function or something we can call to massage command line params?
        params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
        cmdDir = ''
        showCmd = win32con.SW_SHOWNORMAL
        #showCmd = win32con.SW_HIDE
        lpVerb = 'runas'  # causes UAC elevation prompt.

        # print "Running", cmd, params

        # ShellExecute() doesn't seem to allow us to fetch the PID or handle
        # of the process, so we can't get anything useful from it. Therefore
        # the more complex ShellExecuteEx() must be used.

        # procHandle = win32api.ShellExecute(0, lpVerb, cmd, params, cmdDir, showCmd)

        procInfo = ShellExecuteEx(nShow=showCmd,
                                  fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                  lpVerb=lpVerb,
                                  lpFile=cmd,
                                  lpParameters=params)

        if wait:
            procHandle = procInfo['hProcess']
            obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
            rc = win32process.GetExitCodeProcess(procHandle)
            #print "Process handle %s returned code %s" % (procHandle, rc)
        else:
            rc = None

        return rc


from PyQt4 import QtGui
from gui.ui_password import Ui_Dialog
import sys


class PasswordGui(QtGui.QDialog, Ui_Dialog):
    """
    GUI to get user password.
    """
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancel.clicked.connect(self.reject)

        self.ui.enter.clicked.connect(self.get_password)

        self.close()

    def password(self):
        out = str(self.ui.lineEdit.text())

        return out

    def get_password(self):
        self.password()
        QtGui.qApp.closeAllWindows()
        return self.password()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = PasswordGui()
    myapp.show()
    sys.exit(app.exec_())


def get_password():
    """
    This simple function checks for sudo and return the user password as string.
    If sudo is not found, this function try to launch main script with root access using gksu/gksudo/kdesu/kdesudo, \n
    if any of the program is already installed.
    PyQt4 is used as GUI.
    Author : sundar
    """
    if os.system('which sudo') == 0:
        password_window = PasswordGui()
        for x in xrange(3):
            password_window.exec_()
            password = str(password_window.get_password()).strip()
            if password:
                if os.popen('echo ' + str(password) + ' | sudo -S id -u').read().strip() == '0':
                    return password
                if x == 2:
                    print "You have entered wrong password 3 times. Exiting now. "
                    QtGui.QMessageBox.warning(None, 'Wrong Password...',
                                                    "You have entered wrong password for 3 times.\n\n Exiting now.")
                    sys.exit(0)
            else:
                print "Password not entered. Exiting now."
                sys.exit(0)

    elif os.system('which gksu') == 0:
        os.system("gksu -d " + sys.executable + " " + sys.argv[0])
        sys.exit(0)
    elif os.system('which gksudo') == 0:
        os.system("gksudo -d " + sys.executable + " " + sys.argv[0])
        sys.exit(0)
    elif os.system('which kdesu') == 0:
        os.system("kdesu -t " + sys.executable + " " + sys.argv[0])
        sys.exit(0)
    elif os.system('which kdesudo') == 0:
        os.system("kdesudo -t " + sys.executable + " " + sys.argv[0])
        sys.exit(0)

    else:
        QtGui.QMessageBox.information('No root...',
                                      'Please install sudo or gksu or kdesu or gksudo or kdesudo then restart multibootusb.')
        sys.exit(0)