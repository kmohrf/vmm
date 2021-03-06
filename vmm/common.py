# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.common
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Some common functions
"""

import locale
import os
import re
import stat
from gettext import gettext as _

from vmm import ENCODING
from vmm.constants import (
    INVALID_MAIL_LOCATION,
    NOT_EXECUTABLE,
    NO_SUCH_BINARY,
    TYPE_ACCOUNT,
    TYPE_ALIAS,
    TYPE_RELOCATED,
)
from vmm.errors import VMMError

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(?:(\d+)|(alpha|beta|rc)(\d+))$")

_version_level = dict(alpha=0xA, beta=0xB, rc=0xC)
_version_cache = {}


def expand_path(path):
    """Expands paths, starting with ``.`` or ``~``, to an absolute path."""
    if path.startswith("."):
        return os.path.abspath(path)
    if path.startswith("~"):
        return os.path.expanduser(path)
    return path


def get_unicode(string):
    """Converts `string` to `unicode`, if necessary."""
    if isinstance(string, str):
        return string
    return str(string, ENCODING, "replace")


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
        raise VMMError(_("No such file: '%s'") % get_unicode(binary), NO_SUCH_BINARY)
    if not os.access(binary, os.X_OK):
        raise VMMError(
            _("File is not executable: '%s'") % get_unicode(binary), NOT_EXECUTABLE
        )
    return binary


def human_size(size):
    """Converts the `size` in bytes in human readable format."""
    if not isinstance(size, int):
        try:
            size = int(size)
        except ValueError:
            raise TypeError("'size' must be a positive integer.")
    if size < 0:
        raise ValueError("'size' must be a positive integer.")
    if size < 1024:
        return str(size)
    # TP: abbreviations of gibibyte, tebibyte kibibyte and mebibyte
    prefix_multiply = (
        (_("TiB"), 1 << 40),
        (_("GiB"), 1 << 30),
        (_("MiB"), 1 << 20),
        (_("KiB"), 1 << 10),
    )
    for prefix, multiply in prefix_multiply:
        if size >= multiply:
            # TP: e.g.: '%(size)s %(prefix)s' -> '118.30 MiB'
            return _("%(size)s %(prefix)s") % {
                "size": locale.format_string("%.2f", float(size) / multiply, True),
                "prefix": prefix,
            }


def size_in_bytes(size):
    """Converts the string `size` to an integer (size in bytes).

    The string `size` can be suffixed with *b* (bytes), *k* (kilobytes),
    *M* (megabytes) or *G* (gigabytes).
    """
    if not isinstance(size, str) or not size:
        raise TypeError("size must be a non empty string.")
    if size[-1].upper() in ("B", "K", "M", "G"):
        try:
            num = int(size[:-1])
        except ValueError:
            raise ValueError("Not a valid integer value: %r" % size[:-1])
        unit = size[-1].upper()
        if unit == "B":
            return num
        elif unit == "K":
            return num << 10
        elif unit == "M":
            return num << 20
        else:
            return num << 30
    else:
        try:
            num = int(size)
        except ValueError:
            raise ValueError("Not a valid size value: %r" % size)
        return num


def validate_transport(transport, maillocation):
    """Checks if the `transport` is usable for the given `maillocation`.

    Throws a `VMMError` if the chosen `transport` is unable to write
    messages in the `maillocation`'s mailbox format.

    Arguments:

    `transport` : vmm.transport.Transport
      a Transport object
    `maillocation` : vmm.maillocation.MailLocation
      a MailLocation object
    """
    if transport.transport in ("virtual", "virtual:") and not maillocation.postfix:
        raise VMMError(
            _("Invalid transport '%(transport)s' for mailbox " "format '%(mbfmt)s'.")
            % {"transport": transport.transport, "mbfmt": maillocation.mbformat},
            INVALID_MAIL_LOCATION,
        )


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
        raise ValueError("Invalid version string: %r" % version_string)
    major, minor, patch, level, serial = version_mo.groups()
    major = int(major)
    minor = int(minor)
    if patch:
        patch = int(patch)
    if serial:
        serial = int(serial)

    if (
        major > 0xFF
        or minor > 0xFF
        or patch
        and patch > 0xFF
        or serial
        and serial > 0xFF
    ):
        raise ValueError("Invalid version string: %r" % version_string)

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
    Raises a `TypeError` if *version* is not an integer.
    Raises a `ValueError` if *version* is an incorrect int version.
    """
    global _version_cache
    if version in _version_cache:
        return _version_cache[version]
    if not isinstance(version, int):
        raise TypeError("Argument is not a integer: %r", version)
    major = (version >> 28) & 0xFF
    minor = (version >> 20) & 0xFF
    patch = (version >> 12) & 0xFF
    level = (version >> 8) & 0x0F
    serial = version & 0xFF

    levels = dict(list(zip(list(_version_level.values()), list(_version_level.keys()))))
    if level == 0xF and not serial:
        version_string = "%u.%u.%u" % (major, minor, patch)
    elif level in levels and not patch:
        version_string = "%u.%u.%s%u" % (major, minor, levels[level], serial)
    else:
        raise ValueError("Invalid version: %r" % hex(version))

    _version_cache[version] = version_string
    return version_string


def format_domain_default(domaindata):
    """Format info output when the value displayed is the domain default."""
    # TP: [domain default] indicates that a user's setting is the same as
    # configured in the user's domain.
    # e.g.: [  0.84%] 42/5,000 [domain default]
    return _("%s [domain default]") % domaindata


def _build_search_addresses_query(typelimit, lpattern, llike, dpattern, dlike):
    if typelimit is None:
        typelimit = TYPE_ACCOUNT | TYPE_ALIAS | TYPE_RELOCATED
    selected_types = []
    if typelimit & TYPE_ACCOUNT:
        # fmt: off
        selected_types.append(
            "SELECT gid, local_part, %d AS type "
            "FROM users" % TYPE_ACCOUNT
        )
        # fmt: on
    if typelimit & TYPE_ALIAS:
        # fmt: off
        selected_types.append(
            "SELECT DISTINCT gid, address AS local_part, %d AS type "
            "FROM alias" % TYPE_ALIAS
        )
        # fmt: on
    if typelimit & TYPE_RELOCATED:
        # fmt: off
        selected_types.append(
            "SELECT gid, address AS local_part, %d AS type "
            "FROM relocated" % TYPE_RELOCATED
        )
        # fmt: on
    type_query = " UNION ".join(selected_types)

    where = []
    sqlargs = []
    for like, field, pattern in (
        (dlike, "domainname", dpattern),
        (llike, "local_part", lpattern),
    ):
        if not like and not pattern:
            continue
        match = "LIKE" if like else "="
        where.append(f"{field} {match} %s")
        sqlargs.append(pattern)
    where_query = f"WHERE ({' AND '.join(where)})" if where else ""

    # fmt: off
    sql = (
        f"SELECT "
        f"   gid, "
        f"   local_part || '@' || domainname AS address, "
        f"   type, "
        f"   NOT is_primary AS from_aliasdomain "
        f"FROM ({type_query}) a "
        f"JOIN domain_name USING (gid) "
        f"{where_query} "
        f"ORDER BY domainname, local_part"
    )
    # fmt: on
    return sql, sqlargs


def search_addresses(
    dbh, typelimit=None, lpattern=None, llike=False, dpattern=None, dlike=False
):
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
    dbc = dbh.cursor()
    sql, sqlargs = _build_search_addresses_query(
        typelimit, lpattern, llike, dpattern, dlike
    )
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
