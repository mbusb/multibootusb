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
    pyudev._qt_base
    ===============

    Base mixin class for Qt4 support.

    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@gmail.com>
"""


from __future__ import (print_function, division, unicode_literals,
                        absolute_import)


class QUDevMonitorObserverMixin(object):

    def _setup_notifier(self, monitor, notifier_class):
        self.monitor = monitor
        self.notifier = notifier_class(
            monitor.fileno(), notifier_class.Read, self)
        self.notifier.activated[int].connect(self._process_udev_event)
        self._action_signal_map = {
            'add': self.deviceAdded, 'remove': self.deviceRemoved,
            'change': self.deviceChanged, 'move': self.deviceMoved,
        }

    @property
    def enabled(self):
        """
        Whether this observer is enabled or not.

        If ``True`` (the default), this observer is enabled, and emits events.
        Otherwise it is disabled and does not emit any events.  This merely
        reflects the state of the ``enabled`` property of the underlying
        :attr:`notifier`.

        .. versionadded:: 0.14
        """
        return self.notifier.isEnabled()

    @enabled.setter
    def enabled(self, value):
        self.notifier.setEnabled(value)

    def _process_udev_event(self):
        """
        Attempt to receive a single device event from the monitor, process
        the event and emit corresponding signals.

        Called by ``QSocketNotifier``, if data is available on the udev
        monitoring socket.
        """
        device = self.monitor.poll(timeout=0)
        if device:
            self.deviceEvent.emit(device.action, device)
            signal = self._action_signal_map.get(device.action)
            if signal is not None:
                signal.emit(device)
