# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2012, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.common
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Some common functions
"""

import locale
import os
import re
import stat

from VirtualMailManager import ENCODING
from VirtualMailManager.constants import NOT_EXECUTABLE, NO_SUCH_BINARY, \
     TYPE_ACCOUNT, TYPE_ALIAS, TYPE_RELOCATED
from VirtualMailManager.errors import VMMError

VERSION_RE = re.compile(r'^(\d+)\.(\d+)\.(?:(\d+)|(alpha|beta|rc)(\d+))$')

_version_level = dict(alpha=0xA, beta=0xB, rc=0xC)
_version_cache = {}
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


def lisdir(path):
    """Checks if `path` is a directory.  Doesn't follow symbolic links.
    Returns bool.
    """
    try:
        lstat = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISDIR(lstat.st_mode)


def exec_ok(binary):
    """Checks if the `binary` exists and if it is executable.

    Throws a `VMMError` if the `binary` isn't a file or is not
    executable.
    """
    binary = expand_path(binary)
    if not os.path.isfile(binary):
        raise VMMError(_(u"No such file: '%s'") % get_unicode(binary),
                       NO_SUCH_BINARY)
    if not os.access(binary, os.X_OK):
        raise VMMError(_(u"File is not executable: '%s'") %
                       get_unicode(binary), NOT_EXECUTABLE)
    return binary


def human_size(size):
    """Converts the `size` in bytes in human readable format."""
    if not isinstance(size, (long, int)):
        try:
            size = long(size)
        except ValueError:
            raise TypeError("'size' must be a positive long or int.")
    if size < 0:
        raise ValueError("'size' must be a positive long or int.")
    if size < 1024:
        return str(size)
    prefix_multiply = ((_(u'TiB'), 1 << 40), (_(u'GiB'), 1 << 30),
                       (_(u'MiB'), 1 << 20), (_(u'KiB'), 1 << 10))
    for prefix, multiply in prefix_multiply:
        if size >= multiply:
            # TP: e.g.: '%(size)s %(prefix)s' -> '118.30 MiB'
            return _(u'%(size)s %(prefix)s') % {
                    'size': locale.format('%.2f', float(size) / multiply,
                                          True),
                    'prefix': prefix}


def size_in_bytes(size):
    """Converts the string `size` to a long (size in bytes).

    The string `size` can be suffixed with *b* (bytes), *k* (kilobytes),
    *M* (megabytes) or *G* (gigabytes).
    """
    if not isinstance(size, basestring) or not size:
        raise TypeError('size must be a non empty string.')
    if size[-1].upper() in ('B', 'K', 'M', 'G'):
        try:
            num = int(size[:-1])
        except ValueError:
            raise ValueError('Not a valid integer value: %r' % size[:-1])
        unit = size[-1].upper()
        if unit == 'B':
            return num
        elif unit == 'K':
            return num << 10L
        elif unit == 'M':
            return num << 20L
        else:
            return num << 30L
    else:
        try:
            num = int(size)
        except ValueError:
            raise ValueError('Not a valid size value: %r' % size)
        return num


def version_hex(version_string):
    """Converts a Dovecot version, e.g.: '1.2.3' or '2.0.beta4', to an int.
    Raises a `ValueError` if the *version_string* has the wrong™ format.

    version_hex('1.2.3') -> 270548736
    hex(version_hex('1.2.3')) -> '0x10203f00'
    """
    global _version_cache
    if version_string in _version_cache:
        return _version_cache[version_string]
    version = 0
    version_mo = VERSION_RE.match(version_string)
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

    _version_cache[version_string] = version
    return version


def version_str(version):
    """Converts a Dovecot version previously converted with version_hex back to
    a string.
    Raises a `TypeError` if *version* is not an int/long.
    Raises a `ValueError` if *version* is an incorrect int version.
    """
    global _version_cache
    if version in _version_cache:
        return _version_cache[version]
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

    _version_cache[version] = version_string
    return version_string

def format_domain_default(domaindata):
    """Format info output when the value displayed is the domain default."""
    return _(u'%s [domain default]') % domaindata


def search_addresses(dbh, typelimit=None, lpattern=None, llike=False,
                     dpattern=None, dlike=False):
    """'Search' for addresses by *pattern* in the database.

    The search is limited by *typelimit*, a bitfield with values TYPE_ACCOUNT,
    TYPE_ALIAS, TYPE_RELOCATED, or a bitwise OR thereof. If no limit is
    specified, all types will be searched.

    *lpattern* may be a local part or a partial local part - starting and/or
    ending with a '%' sign.  When the *lpattern* starts or ends with a '%' sign
    *llike* has to be `True` to perform a wildcard search. To retrieve all
    available addresses use the arguments' default values.

    *dpattern* and *dlike* behave analogously for the domain part of an
    address, allowing for separate pattern matching: testuser%@example.%

    The return value of this function is a tuple. The first element is a list
    of domain IDs sorted alphabetically by the corresponding domain names. The
    second element is a dictionary indexed by domain ID, holding lists to
    associated addresses. Each address is itself actually a tuple of address,
    type, and boolean indicating whether the address stems from an alias
    domain.
    """
    if typelimit == None:
            typelimit = TYPE_ACCOUNT | TYPE_ALIAS | TYPE_RELOCATED
    queries = []
    if typelimit & TYPE_ACCOUNT:
        queries.append('SELECT gid, local_part, %d AS type FROM users'
                       % TYPE_ACCOUNT)
    if typelimit & TYPE_ALIAS:
        queries.append('SELECT DISTINCT gid, address as local_part, %d AS type '
                       'FROM alias' % TYPE_ALIAS)
    if typelimit & TYPE_RELOCATED:
        queries.append('SELECT gid, address as local_part, %d AS type '
                       'FROM relocated' % TYPE_RELOCATED)
    sql  = "SELECT gid, local_part || '@' || domainname AS address, "
    sql += 'type, NOT is_primary AS from_aliasdomain FROM ('
    sql += ' UNION '.join(queries)
    sql += ') a JOIN domain_name USING (gid)'
    nextkw = 'WHERE'
    sqlargs = []
    for like, field, pattern in ((dlike, 'domainname', dpattern),
                                 (llike, 'local_part', lpattern)):
        if like:
            match = 'LIKE'
        else:
            if not pattern: continue
            match = '='
        sql += ' %s %s %s %%s' % (nextkw, field, match)
        sqlargs.append(pattern)
        nextkw = 'AND'
    sql += ' ORDER BY domainname, local_part'
    dbc = dbh.cursor()
    dbc.execute(sql, sqlargs)
    result = dbc.fetchall()
    dbc.close()

    gids = []
    daddrs = {}
    for gid, address, addrtype, aliasdomain in result:
        if gid not in daddrs:
            gids.append(gid)
            daddrs[gid] = []
        daddrs[gid].append((address, addrtype, aliasdomain))
    return gids, daddrs

del _
