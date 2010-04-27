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


_version_re = re.compile(r'^(\d+)\.(\d+)\.(?:(\d+)|(alpha|beta|rc)(\d+))$')
_version_level = dict(alpha=0xA, beta=0xB, rc=0xC)
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
    """Converts a Dovecot version, e.g.: '1.2.3' or '2.0.beta4', to an int.
    Raises a `ValueError` if the *version_string* has the wrong™ format.

    version_hex('1.2.3') -> 270548736
    hex(version_hex('1.2.3')) -> '0x10203f00'
    """
    version = 0
    version_mo = _version_re.match(version_string)
    if not version_mo:
        raise ValueError('Invalid version string: %r' % version_string)
    major, minor, patch, level, serial = version_mo.groups()
    major = int(major)
    minor = int(minor)
    if patch:
        patch = int(patch)
    if serial:
        serial = int(serial)

    if major > 0xFF or minor > 0xFF or \
      patch and patch > 0xFF or serial and serial > 0xFF:
        raise ValueError('Invalid version string: %r' % version_string)

    version += major << 28
    version += minor << 20
    if patch:
        version += patch << 12
    version += _version_level.get(level, 0xF) << 8
    if serial:
        version += serial

    return version


def version_str(version):
    """Converts a Dovecot version previously converted with version_hex back to
    a string.
    Raises a `TypeError` if *version* is not an int/long.
    Raises a `ValueError` if *version* is an incorrect int version.
    """
    if not isinstance(version, (int, long)):
        raise TypeError('Argument is not a int/long: %r', version)
    major = (version >> 28) & 0xFF
    minor = (version >> 20) & 0xFF
    patch = (version >> 12) & 0xFF
    level = (version >> 8) & 0x0F
    serial = version & 0xFF

    levels = dict(zip(_version_level.values(), _version_level.keys()))
    if level == 0xF and not serial:
        version_string = '%u.%u.%u' % (major, minor, patch)
    elif level in levels and not patch:
        version_string = '%u.%u.%s%u' % (major, minor, levels[level], serial)
    else:
        raise ValueError('Invalid version: %r' % hex(version))

    return version_string

del _
