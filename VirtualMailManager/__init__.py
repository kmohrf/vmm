# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager

    VirtualMailManager package initialization code
"""

import gettext
import os
import locale


from VirtualMailManager.constants.ERROR import \
     NOT_EXECUTABLE, NO_SUCH_BINARY, NO_SUCH_DIRECTORY
from VirtualMailManager.constants.version import __author__, __date__, \
     __version__
from VirtualMailManager.errors import VMMError


__all__ = [
    # version information from VERSION
    '__author__', '__date__', '__version__',
    # defined stuff
    'ENCODING', 'Configuration', 'exec_ok', 'expand_path', 'get_unicode',
    'is_dir', 'set_configuration',
]


# Try to set all of the locales according to the current
# environment variables and get the character encoding.
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')
ENCODING = locale.nl_langinfo(locale.CODESET)

Configuration = None

gettext.install('vmm', '/usr/local/share/locale', unicode=1)


_ = lambda msg: msg


def set_configuration(cfg_obj):
    """Assigns the *cfg_obj* to the global `Configuration`.
    *cfg_obj* has to be a `VirtualMailManager.Config.Config` instance."""
    from VirtualMailManager.Config import Config
    assert isinstance(cfg_obj, Config)
    global Configuration
    Configuration = cfg_obj


def get_unicode(string):
    """Converts `string` to `unicode`, if necessary."""
    if isinstance(string, unicode):
        return string
    return unicode(string, ENCODING, 'replace')


def expand_path(path):
    """Expands paths, starting with ``.`` or ``~``, to an absolute path."""
    if path.startswith('.'):
        return os.path.abspath(path)
    if path.startswith('~'):
        return os.path.expanduser(path)
    return path


def is_dir(path):
    """Checks if `path` is a directory.

    Throws a `VMMError` if `path` is not a directory.

    """
    path = expand_path(path)
    if not os.path.isdir(path):
        raise VMMError(_(u"'%s' is not a directory") % get_unicode(path),
                       NO_SUCH_DIRECTORY)
    return path


def exec_ok(binary):
    """Checks if the `binary` exists and if it is executable.

    Throws a `VMMError` if the `binary` isn't a file or is not
    executable.

    """
    binary = expand_path(binary)
    if not os.path.isfile(binary):
        raise VMMError(_(u"'%s' is not a file") % get_unicode(binary),
                       NO_SUCH_BINARY)
    if not os.access(binary, os.X_OK):
        raise VMMError(_(u"File is not executable: '%s'") %
                       get_unicode(binary), NOT_EXECUTABLE)
    return binary


del _
