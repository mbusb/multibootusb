#!/usr/bin/env python3
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
import sys
import subprocess
from PyQt5 import QtWidgets
from . import gen


def isUserAdmin():
    """
    @return: True if the current user is an 'Admin' whatever that means
    (root on Unix), otherwise False.

    Warning: The inner function fails unless you have Windows XP SP2 or
    higher. The failure causes a traceback to be gen.loged and this
    function to return False.
    """

    if platform.system() == "Windows":
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            traceback.print_exc()
            gen.log("Admin check failed, assuming not an admin.")
            return False
    elif platform.system() == "Linux":
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: %s" % (os.name,))


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

        import win32api
        import win32con
        import win32event
        import win32process
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon

        python_exe = sys.executable

        if cmdLine is None:
            cmdLine = [python_exe] + sys.argv
        elif type(cmdLine) not in (types.TupleType, types.ListType):
            raise ValueError("cmdLine is not a sequence.")
        cmd = '"%s"' % (cmdLine[0],)
        # XXX TODO: isn't there a function or something we can call to massage command line params?
        params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
#         cmdDir = ''
        showCmd = win32con.SW_SHOWNORMAL
        #showCmd = win32con.SW_HIDE
        lpVerb = 'runas'  # causes UAC elevation prompt.

        #gen.log("Running", cmd, params)

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
            #gen.log "Process handle %s returned code %s" % (procHandle, rc)
        else:
            rc = None

        return rc


def adminCmd(cmd, fork=False, gui=False):
    """
    This simple function checks for a sudo command and runs a command using it.
    This function tries to launch given script with root access using pkexec/gksu/gksudo/kdesu/kdesudo,
    if one of them is already installed.
    PyQt4 is used as GUI.
    Author : sundar
    """
    sudo_cmd = ''
    if os.getuid() == 0:
        sudo_cmd = cmd
    else:
        if os.system('which pkexec') == 0:
            if gui:
                # By default, pkexec disallows X11 apps. Restore DISPLAY & XAUTHORITY
                # to allow it. man 1 pkexec/"SECURITY NOTES" section
                cmd = ['export DISPLAY=$DISPLAY; export XAUTHORITY=$XAUTHORITY; '] + cmd
            sudo_cmd = ['pkexec', '/bin/sh', '-c']
        elif os.system('which gksudo') == 0:
            sudo_cmd = ["gksudo", "--", "/bin/sh", "-c"]
        elif os.system('which gksu') == 0:
            sudo_cmd = ["gksu"]
        elif os.system('which kdesudo') == 0:
            sudo_cmd = ["kdesudo", "-t", "-c"]    # http://www.unix.com/man-page/debian/1/kdesudo/
        elif os.system('which kdesu') == 0:
            sudo_cmd = ["kdesu", "-t", "-c"]      # http://linux.die.net/man/1/kdesu
        else:
            QtWidgets.QMessageBox.information('No root...',
                                          'Could not find any of: pkexec, sudo, gksu, kdesu, gksudo, or kdesudo.\n'
                                          'Please install one then restart multibootusb.')
            sys.exit(0)
    final_cmd = ' '.join(sudo_cmd + ['"' + ' '.join(cmd).replace('"', '\\"') + '"'])
    gen.log("Executing ==>  " + final_cmd)
    if fork:
        return subprocess.Popen(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, shell=True)
    else:
        ret = subprocess.call(final_cmd, shell=True)
        gen.log("Process returned ==>   " + str(ret))
        return ret
