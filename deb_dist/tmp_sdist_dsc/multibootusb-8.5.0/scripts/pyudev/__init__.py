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
    pyudev
    ======

    A binding to libudev.

    The :class:`Context` provides the connection to the udev device database
    and enumerates devices.  Individual devices are represented by the
    :class:`Device` class.

    Device monitoring is provided by :class:`Monitor` and
    :class:`MonitorObserver`.  With :mod:`pyudev.pyqt4`, :mod:`pyudev.pyside`,
    :mod:`pyudev.glib` and :mod:`pyudev.wx` device monitoring can be integrated
    into the event loop of various GUI toolkits.

    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ._errors import DeviceNotFoundAtPathError
from ._errors import DeviceNotFoundByFileError
from ._errors import DeviceNotFoundByNameError
from ._errors import DeviceNotFoundByNumberError
from ._errors import DeviceNotFoundError
from ._errors import DeviceNotFoundInEnvironmentError

from .device import Attributes
from .device import Device
from .device import Devices
from .device import Tags

from .discover import DeviceFileHypothesis
from .discover import DeviceNameHypothesis
from .discover import DeviceNumberHypothesis
from .discover import DevicePathHypothesis
from .discover import Discovery

from .core import Context
from .core import Enumerator

from .monitor import Monitor
from .monitor import MonitorObserver

from .version import __version__
from .version import __version_info__

from ._util import udev_version
