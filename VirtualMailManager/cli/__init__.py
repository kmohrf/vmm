# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2013, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.cli
    ~~~~~~~~~~~~~~~~~~~~~~

    VirtualMailManager's command line interface.
"""

import os
from array import array
from fcntl import ioctl
from getpass import getpass
from termios import TIOCGWINSZ

from VirtualMailManager import ENCODING
from VirtualMailManager.constants import VMM_TOO_MANY_FAILURES
from VirtualMailManager.errors import VMMError


__all__ = ('prog', 'get_winsize', 'read_pass', 'w_err', 'w_std')

_ = lambda msg: msg
_std_write = os.sys.stdout.write
_err_write = os.sys.stderr.write
prog = os.path.basename(os.sys.argv[0])


def w_std(*args):
    """Writes a line for each arg of *args*, encoded in the current
    ENCODING, to stdout.
    """
    _std_write('\n'.join(a.encode(ENCODING, 'replace') for a in args) + '\n')


def w_err(code, *args):
    """Writes a line for each arg of *args*, encoded in the current
    ENCODING, to stderr.
    This function optionally interrupts the program execution if *code*
    does not equal to 0. *code* will be used as the system exit status.
    """
    _err_write('\n'.join(a.encode(ENCODING, 'replace') for a in args) + '\n')
    if code:
        os.sys.exit(code)


def get_winsize():
    """Returns a tuple of integers ``(ws_row, ws_col)`` with the height and
    width of the terminal."""
    fd = None
    for dev in (os.sys.stdout, os.sys.stderr, os.sys.stdin):
        if hasattr(dev, 'fileno') and os.isatty(dev.fileno()):
            fd = dev.fileno()
            break
    if fd is None:  # everything seems to be redirected
        # fall back to environment or assume some common defaults
        ws_row, ws_col = 24, 80
        try:
            ws_col = int(os.environ.get('COLUMNS', 80))
            ws_row = int(os.environ.get('LINES', 24))
        except ValueError:
            pass
        return ws_row, ws_col
    #"struct winsize" with the ``unsigned short int``s ws_{row,col,{x,y}pixel}
    ws = array('H', (0, 0, 0, 0))
    ioctl(fd, TIOCGWINSZ, ws, True)
    ws_row, ws_col = ws[:2]
    return ws_row, ws_col


def read_pass():
    """Interactive 'password chat', returns the password in plain format.

    Throws a VMMError after the third failure.
    """
    # TP: Please preserve the trailing space.
    readp_msg0 = _(u'Enter new password: ').encode(ENCODING, 'replace')
    # TP: Please preserve the trailing space.
    readp_msg1 = _(u'Retype new password: ').encode(ENCODING, 'replace')
    mismatched = True
    failures = 0
    while mismatched:
        if failures > 2:
            raise VMMError(_(u'Too many failures - try again later.'),
                           VMM_TOO_MANY_FAILURES)
        clear0 = getpass(prompt=readp_msg0)
        clear1 = getpass(prompt=readp_msg1)
        if clear0 != clear1:
            failures += 1
            w_err(0, _(u'Sorry, passwords do not match.'))
            continue
        if not clear0:
            failures += 1
            w_err(0, _(u'Sorry, empty passwords are not permitted.'))
            continue
        mismatched = False
    return clear0

del _
