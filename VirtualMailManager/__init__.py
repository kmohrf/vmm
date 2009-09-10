# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2009, VEB IT
# See COPYING for distribution information.
# package initialization code
#

import os
import re
import locale

from constants.VERSION import *
import constants.ERROR as ERR

# Try to set all of the locales according to the current
# environment variables and get the character encoding.
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')
ENCODING = locale.nl_langinfo(locale.CODESET)

def w_std(*args):
    """Writes each arg of args, encoded in the current ENCODING, to stdout and
    appends a newline."""
    _write = os.sys.stdout.write
    for arg in args:
        _write(arg.encode(ENCODING, 'replace'))
        _write('\n')

def w_err(code, *args):
    """Writes each arg of args, encoded in the current ENCODING, to stderr and
    appends a newline.
    This function additional interrupts the program execution and uses 'code'
    system exit status."""
    _write = os.sys.stderr.write
    for arg in args:
        _write(arg.encode(ENCODING, 'replace'))
        _write('\n')
    os.sys.exit(code)

__all__ = [
        # imported modules
        'os', 're', 'locale',
        # version information from VERSION
        '__author__', '__date__', '__version__',
        # error codes
        'ERR',
        # defined stuff
        'ENCODING', 'w_std', 'w_err'
        ]
# EOF
