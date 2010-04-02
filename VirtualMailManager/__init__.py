# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager

    VirtualMailManager package initialization code
"""

import gettext
import os
import re
import locale

from encodings.idna import ToASCII, ToUnicode

from VirtualMailManager.constants.ERROR import \
     DOMAIN_INVALID, DOMAIN_TOO_LONG, LOCALPART_INVALID, LOCALPART_TOO_LONG, \
     NOT_EXECUTABLE, NO_SUCH_BINARY, NO_SUCH_DIRECTORY
from VirtualMailManager.constants.version import __author__, __date__, \
     __version__
from VirtualMailManager.errors import VMMError


__all__ = [
    # version information from VERSION
    '__author__', '__date__', '__version__',
    # defined stuff
    'ENCODING', 'ace2idna', 'check_domainname', 'check_localpart', 'exec_ok',
    'expand_path', 'get_unicode', 'idn2ascii', 'is_dir',
]


# Try to set all of the locales according to the current
# environment variables and get the character encoding.
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')
ENCODING = locale.nl_langinfo(locale.CODESET)

# there may be many domain and e-mail address checks
RE_DOMAIN = re.compile(r"^(?:[a-z0-9-]{1,63}\.){1,}[a-z]{2,6}$")
RE_LOCALPART = re.compile(r"[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]")

gettext.install('vmm', '/usr/local/share/locale', unicode=1)


_ = lambda msg: msg


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


def idn2ascii(domainname):
    """Converts the idn domain name `domainname` into punycode."""
    return '.'.join([ToASCII(lbl) for lbl in domainname.split('.') if lbl])


def ace2idna(domainname):
    """Converts the domain name `domainname` from ACE according to IDNA."""
    return u'.'.join([ToUnicode(lbl) for lbl in domainname.split('.') if lbl])


def check_domainname(domainname):
    """Returns the validated domain name `domainname`.

    It also converts the name of the domain from IDN to ASCII, if
    necessary.

    Throws an `VMMError`, if the domain name is too long or doesn't
    look like a valid domain name (label.label.label).

    """
    if not RE_DOMAIN.match(domainname):
        domainname = idn2ascii(domainname)
    if len(domainname) > 255:
        raise VMMError(_(u'The domain name is too long'), DOMAIN_TOO_LONG)
    if not RE_DOMAIN.match(domainname):
        raise VMMError(_(u'The domain name %r is invalid') % domainname,
                       DOMAIN_INVALID)
    return domainname


def check_localpart(localpart):
    """Returns the validated local-part `localpart`.

    Throws a `VMMError` if the local-part is too long or contains
    invalid characters.

    """
    if len(localpart) > 64:
        raise VMMError(_(u"The local-part '%s' is too long") % localpart,
                       LOCALPART_TOO_LONG)
    invalid_chars = set(RE_LOCALPART.findall(localpart))
    if invalid_chars:
        i_chars = u''.join((u'"%s" ' % c for c in invalid_chars))
        raise VMMError(_(u"The local-part '%(l_part)s' contains invalid \
characters: %(i_chars)s") %
                       {'l_part': localpart, 'i_chars': i_chars},
                       LOCALPART_INVALID)
    return localpart


del _
