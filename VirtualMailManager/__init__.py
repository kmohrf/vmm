# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager

    VirtualMailManager package initialization code
"""

import gettext
import locale

from VirtualMailManager.constants.version import __author__, __date__, \
     __version__

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
    locale.setlocale(locale.LC_ALL, 'C')
ENCODING = locale.nl_langinfo(locale.CODESET)

gettext.install('vmm', '/usr/local/share/locale', unicode=1)
