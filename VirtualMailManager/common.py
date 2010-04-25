# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.common

    Some common functions
"""

import os
import re

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
    """Convert a Dovecot version, e.g.: '1.2.3' or '2.0.beta4', to an int.
    Returns 0 if the *version_string* has the wrong™ format.

    version_hex('1.2.3') -> 16909296
    hex(version_hex('1.2.3')) -> '0x10203f0'
    """
    version = 0
    version_re = r'^(\d+)\.(\d+)\.(?:(\d+)|(alpha|beta|rc)(\d+))$'
    version_level = dict(alpha=0xA, beta=0xB, rc=0xC)
    version_mo = re.match(version_re, version_string)
    if version_mo:
        major, minor, patch, level, serial = version_mo.groups()
        version += int(major) << 24
        version += int(minor) << 16
        if patch:
            version += int(patch) << 8
        version += version_level.get(level, 0xF) << 4
        if serial:
            version += int(serial)
    return version

del _
