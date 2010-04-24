# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.common

    Some common functions
"""

import os

from VirtualMailManager import ENCODING
from VirtualMailManager.constants.ERROR import \
     NOT_EXECUTABLE, NO_SUCH_BINARY, NO_SUCH_DIRECTORY
from VirtualMailManager.errors import VMMError

_ = lambda msg: msg


def expand_path(path):
    """Expands paths, starting with ``.`` or ``~``, to an absolute path."""
    if path.startswith('.'):
        return os.path.abspath(path)
    if path.startswith('~'):
        return os.path.expanduser(path)
    return path


def get_unicode(string):
    """Converts `string` to `unicode`, if necessary."""
    if isinstance(string, unicode):
        return string
    return unicode(string, ENCODING, 'replace')


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


def version_hex(version_string):
    """Convert the version string '1.2.3' to an int.
    hex(version_hex('1.2.3')) -> '0x10203'
    """
    major, minor, patch = map(int, version_string.split('.'))
    return (major << 16) + (minor << 8) + patch

del _
