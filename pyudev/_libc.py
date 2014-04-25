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


"""
    pyudev._libc
    ============

    Wrapper types for libudev.  Use ``libudev`` attribute to access libudev
    functions.

    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@gmail.com>
"""


from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ctypes import CDLL, c_int
from ctypes.util import find_library

from pyudev._errorcheckers import check_errno_on_nonzero_return


fd_pair = c_int * 2


SIGNATURES = dict(
    pipe2=([fd_pair, c_int], c_int),
)

ERROR_CHECKERS = dict(
    pipe2=check_errno_on_nonzero_return,
)

def load_c_library():
    """Load the ``libc`` library and return a :class:`ctypes.CDLL` object for it.
 The library has errno handling enabled.

    Important functions are given proper signatures and return types to support
    type checking and argument conversion.

    Raise :exc:`~exceptions.ImportError`, if the library was not found.

    """
    library_name = find_library('c')
    if not library_name:
        raise ImportError('No library named c')
    libc = CDLL(library_name, use_errno=True)
    # Add function signatures
    for name, signature in SIGNATURES.items():
        function = getattr(libc, name, None)
        if function:
            argtypes, restype = signature
            function.argtypes = argtypes
            function.restype = restype
            errorchecker = ERROR_CHECKERS.get(name)
            if errorchecker:
                function.errcheck = errorchecker
    return libc
