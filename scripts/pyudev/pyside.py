# -*- coding: utf-8 -*-
# Copyright (C) 2010, 2011, 2012 Sebastian Wiesner <lunaryorn@gmail.com>

# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.

# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

"""
    pyudev.pyside
    =============

    PySide integration.

    :class:`QUDevMonitorObserver` integrates device monitoring into the PySide_
    mainloop by turing device events into Qt signals.

    :mod:`PySide.QtCore` from PySide_ must be available when importing this
    module.

    .. _PySide: http://www.pyside.org

    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@gmail.com>
    .. versionadded:: 0.6
"""


from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from PySide.QtCore import QSocketNotifier, QObject, Signal

from pyudev._util import text_type
from pyudev.core import Device
from pyudev._qt_base import QUDevMonitorObserverMixin


class QUDevMonitorObserver(QObject, QUDevMonitorObserverMixin):
    """
    An observer for device events integrating into the :mod:`PySide` mainloop.

    This class inherits :class:`~PySide.QtCore.QObject` to turn device events
    into Qt signals:

    >>> from pyudev import Context, Monitor
    >>> from pyudev.pyqt4 import QUDevMonitorObserver
    >>> context = Context()
    >>> monitor = Monitor.from_netlink(context)
    >>> monitor.filter_by(subsystem='input')
    >>> observer = QUDevMonitorObserver(monitor)
    >>> def device_connected(device):
    ...     print('{0!r} added'.format(device))
    >>> observer.deviceAdded.connect(device_connected)
    >>> monitor.start()

    This class is a child of :class:`~PySide.QtCore.QObject`.
    """

    #: emitted upon arbitrary device events
    deviceEvent = Signal(text_type, Device)
    #: emitted, if a device was added
    deviceAdded = Signal(Device)
    #: emitted, if a device was removed
    deviceRemoved = Signal(Device)
    #: emitted, if a device was changed
    deviceChanged = Signal(Device)
    #: emitted, if a device was moved
    deviceMoved = Signal(Device)

    def __init__(self, monitor, parent=None):
        """
        Observe the given ``monitor`` (a :class:`~pyudev.Monitor`):

        ``parent`` is the parent :class:`~PySide.QtCore.QObject` of this
        object.  It is passed unchanged to the inherited constructor of
        :class:`~PySide.QtCore.QObject`.
        """
        QObject.__init__(self, parent)
        self._setup_notifier(monitor, QSocketNotifier)
