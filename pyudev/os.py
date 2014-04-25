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
    pyudev.os
    =========

    Operating system interface for pyudev.

    .. moduleauthor:: Sebastian Wiesner  <lunaryorn@gmail.com>
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
import fcntl
import select
from functools import partial

from pyudev._libc import load_c_library, fd_pair


# Define O_CLOEXEC, if not present in os already
O_CLOEXEC = getattr(os, 'O_CLOEXEC', 0o2000000)


def _pipe2_ctypes(libc, flags):
    """A ``pipe2`` implementation using ``pipe2`` from ctypes.

    ``libc`` is a :class:`ctypes.CDLL` object for libc.  ``flags`` is an
    integer providing the flags to ``pipe2``.

    Return a pair of file descriptors ``(r, w)``.

    """
    fds = fd_pair()
    libc.pipe2(fds, flags)
    return fds[0], fds[1]


def _pipe2_by_pipe(flags):
    """A ``pipe2`` implementation using :func:`os.pipe`.

    ``flags`` is an integer providing the flags to ``pipe2``.

    .. warning::

       This implementation is not atomic!

    Return a pair of file descriptors ``(r, w)``.

    """
    fds = os.pipe()
    if flags & os.O_NONBLOCK != 0:
        for fd in fds:
            set_fd_status_flag(fd, os.O_NONBLOCK)
    if flags & O_CLOEXEC != 0:
        for fd in fds:
            set_fd_flag(fd, O_CLOEXEC)
    return fds


def _get_pipe2_implementation():
    """Find the appropriate implementation for ``pipe2``.

Return a function implementing ``pipe2``."""
    if hasattr(os, 'pipe2'):
        return os.pipe2
    else:
        try:
            libc = load_c_library()
            return (partial(_pipe2_ctypes, libc)
                    if hasattr(libc, 'pipe2') else
                    _pipe2_by_pipe)
        except ImportError:
            return _pipe2_by_pipe


_pipe2 = _get_pipe2_implementation()


def set_fd_flag(fd, flag):
    """Set a flag on a file descriptor.

    ``fd`` is the file descriptor or file object, ``flag`` the flag as integer.

    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFD, 0)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags | flag)


def set_fd_status_flag(fd, flag):
    """Set a status flag on a file descriptor.

    ``fd`` is the file descriptor or file object, ``flag`` the flag as integer.

    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | flag)


class Pipe(object):
    """A unix pipe.

    A pipe object provides two file objects: :attr:`source` is a readable file
    object, and :attr:`sink` a writeable.  Bytes written to :attr:`sink` appear
    at :attr:`source`.

    Open a pipe with :meth:`open()`.

    """

    @classmethod
    def open(cls):
        """Open and return a new :class:`Pipe`.

        The pipe uses non-blocking IO."""
        source, sink = _pipe2(os.O_NONBLOCK | O_CLOEXEC)
        return cls(source, sink)

    def __init__(self, source_fd, sink_fd):
        """Create a new pipe object from the given file descriptors.

        ``source_fd`` is a file descriptor for the readable side of the pipe,
        ``sink_fd`` is a file descriptor for the writeable side."""
        self.source = os.fdopen(source_fd, 'rb', 0)
        self.sink = os.fdopen(sink_fd, 'wb', 0)

    def close(self):
        """Closes both sides of the pipe."""
        try:
            self.source.close()
        finally:
            self.sink.close()


class Poll(object):
    """A poll object.

    This object essentially provides a more convenient interface around
    :class:`select.poll`.

    """

    _EVENT_TO_MASK = {'r': select.POLLIN,
                      'w': select.POLLOUT}

    @staticmethod
    def _has_event(events, event):
        return events & event != 0

    @classmethod
    def for_events(cls, *events):
        """Listen for ``events``.

        ``events`` is a list of ``(fd, event)`` pairs, where ``fd`` is a file
        descriptor or file object and ``event`` either ``'r'`` or ``'w'``.  If
        ``r``, listen for whether that is ready to be read.  If ``w``, listen
        for whether the channel is ready to be written to.

        """
        notifier = select.poll()
        for fd, event in events:
            mask = cls._EVENT_TO_MASK.get(event)
            if not mask:
                raise ValueError('Unknown event type: {0!r}'.format(event))
            notifier.register(fd, mask)
        return cls(notifier)

    def __init__(self, notifier):
        """Create a poll object for the given ``notifier``.

        ``notifier`` is the :class:`select.poll` object wrapped by the new poll
        object.

        """
        self._notifier = notifier

    def poll(self, timeout=None):
        """Poll for events.

        ``timeout`` is an integer specifying how long to wait for events (in
        milliseconds).  If omitted, ``None`` or negative, wait until an event
        occurs.

        Return a list of all events that occurred before ``timeout``, where
        each event is a pair ``(fd, event)``. ``fd`` is the integral file
        descriptor, and ``event`` a string indicating the event type.  If
        ``'r'``, there is data to read from ``fd``.  If ``'w'``, ``fd`` is
        writable without blocking now.  If ``'h'``, the file descriptor was
        hung up (i.e. the remote side of a pipe was closed).

        """
        # Return a list to allow clients to determine whether there are any
        # events at all with a simple truthiness test.
        return list(self._parse_events(self._notifier.poll(timeout)))

    def _parse_events(self, events):
        """Parse ``events``.

        ``events`` is a list of events as returned by
        :meth:`select.poll.poll()`.

        Yield all parsed events.

        """
        for fd, event_mask in events:
            if self._has_event(event_mask, select.POLLNVAL):
                raise IOError('File descriptor not open: {0!r}'.format(fd))
            elif self._has_event(event_mask, select.POLLERR):
                raise IOError('Error while polling fd: {0!r}'.format(fd))

            if self._has_event(event_mask, select.POLLIN):
                yield fd, 'r'
            if self._has_event(event_mask, select.POLLOUT):
                yield fd, 'w'
            if self._has_event(event_mask, select.POLLHUP):
                yield fd, 'h'
