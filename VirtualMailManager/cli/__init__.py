# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.cli

    VirtualMailManager's command line interface.
"""

from cStringIO import StringIO
from getpass import getpass
from textwrap import TextWrapper

import VirtualMailManager


__all__ = ('get_winsize', 'read_pass', 'string_io', 'w_err', 'w_std')

os = VirtualMailManager.os
_std_write = os.sys.stdout.write
_err_write = os.sys.stderr.write


def w_std(*args):
    """Writes each arg of `args`, encoded in the current ENCODING, to stdout
    and appends a newline."""
    for arg in args:
        _std_write(arg.encode(VirtualMailManager.ENCODING, 'replace'))
        _std_write('\n')


def w_err(code, *args):
    """Writes each arg of `args`, encoded in the current ENCODING, to stderr
    and appends a newline.

    This function additional interrupts the program execution and uses
    `code` system exit status."""
    for arg in args:
        _err_write(arg.encode(VirtualMailManager.ENCODING, 'replace'))
        _err_write('\n')
    os.sys.exit(code)


def get_winsize():
    """Returns a tuple of integers ``(ws_row, ws_col)`` with the height and
    width of the terminal."""
    fd = None
    for dev in (os.sys.stdout, os.sys.stderr, os.sys.stdin):
        if hasattr(dev, 'fileno') and os.isatty(dev.fileno()):
            fd = dev.fileno()
            break
    if fd is None:# everything seems to be redirected
        # fall back to environment or assume some common defaults
        ws_row, ws_col = 24, 80
        try:
            ws_col = int(os.environ.get('COLUMNS', 80))
            ws_row = int(os.environ.get('LINES', 24))
        except ValueError:
            pass
        return ws_row, ws_col

    from array import array
    from fcntl import ioctl
    from termios import TIOCGWINSZ

    #"struct winsize" with the ``unsigned short int``s ws_{row,col,{x,y}pixel}
    ws = array('H', (0, 0, 0, 0))
    ioctl(fd, TIOCGWINSZ, ws, True)
    ws_row, ws_col = ws[:2]
    return ws_row, ws_col


def read_pass():
    """Interactive 'password chat', returns the password in plain format.

    Throws a VMMException after the third failure.
    """
    # TP: Please preserve the trailing space.
    readp_msg0 = _(u'Enter new password: ').encode(ENCODING, 'replace')
    # TP: Please preserve the trailing space.
    readp_msg1 = _(u'Retype new password: ').encode(ENCODING, 'replace')
    mismatched = True
    failures = 0
    while mismatched:
        if failures > 2:
            raise VMMException(_(u'Too many failures - try again later.'),
                               ERR.VMM_TOO_MANY_FAILURES)
        clear0 = getpass(prompt=readp_msg0)
        clear1 = getpass(prompt=readp_msg1)
        if clear0 != clear1:
            failures += 1
            w_std(_(u'Sorry, passwords do not match'))
            continue
        if not clear0:
            failures += 1
            w_std(_(u'Sorry, empty passwords are not permitted'))
            continue
        mismatched = False
    return clear0


def string_io():
    """Returns a new `cStringIO.StringIO` instance."""
    return StringIO()
