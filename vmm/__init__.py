# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm
    ~~~~~~~~~~~~~~~~~~

    vmm package initialization code
"""

import gettext
import locale
import sys

from vmm.constants import __author__, __date__, __version__

__all__ = [
    # version information from VERSION
    '__author__', '__date__', '__version__',
    # defined stuff
    'ENCODING',
]


# Try to set all of the locales according to the current
# environment variables and get the character encoding.
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    sys.stderr.write('warning: unsupported locale setting - '
                     'that may cause encoding problems.\n\n')
    locale.setlocale(locale.LC_ALL, 'C')
ENCODING = locale.nl_langinfo(locale.CODESET)

gettext.install('vmm', '/usr/local/share/locale')
