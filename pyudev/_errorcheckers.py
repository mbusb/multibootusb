# -*- coding: utf-8 -*-
# Copyright (C) 2013 Sebastian Wiesner <lunaryorn@gmail.com>

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


from __future__ import (print_function, division, unicode_literals,
                        absolute_import)


"""
    pyudev._errorcheckers
    =====================

    Error checkers for ctypes wrappers.
"""


import os
import errno
from ctypes import get_errno


ERRNO_EXCEPTIONS = {
    errno.ENOMEM: MemoryError,
    errno.EOVERFLOW: OverflowError,
    errno.EINVAL: ValueError
}


def exception_from_errno(errno):
    """Create an exception from ``errno``.

    ``errno`` is an integral error number.

    Return an exception object appropriate to ``errno``.

    """
    exception = ERRNO_EXCEPTIONS.get(errno)
    if exception is not None:
        return exception()
    else:
        return EnvironmentError(errno, os.strerror(errno))


def check_negative_errorcode(result, func, *args):
    """Error checker for funtions, which return negative error codes.

    If ``result`` is smaller than ``0``, it is interpreted as negative error
    code, and an appropriate exception is raised:

    - ``-ENOMEM`` raises a :exc:`~exceptions.MemoryError`
    - ``-EOVERFLOW`` raises a :exc:`~exceptions.OverflowError`
    - all other error codes raise :exc:`~exceptions.EnvironmentError`

    If result is greater or equal to ``0``, it is returned unchanged.

    """
    if result < 0:
        # udev returns the *negative* errno code at this point
        errno = -result
        raise exception_from_errno(errno)
    else:
        return result


def check_errno_on_nonzero_return(result, func, *args):
    """Error checker to check the system ``errno`` as returned by
    :func:`ctypes.get_errno()`.

    If ``result`` is not ``0``, an exception according to this errno is raised.
    Otherwise nothing happens.

    """
    if result != 0:
        errno = get_errno()
        if errno != 0:
            raise exception_from_errno(errno)
    return result


def check_errno_on_null_pointer_return(result, func, *args):
    """Error checker to check the system ``errno`` as returned by
    :func:`ctypes.get_errno()`.

    If ``result`` is a null pointer, an exception according to this errno is
    raised.  Otherwise nothing happens.

    """
    if not result:
        errno = get_errno()
        if errno != 0:
            raise exception_from_errno(errno)
    return result
