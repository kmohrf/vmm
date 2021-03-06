# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.emailaddress
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's EmailAddress class to handle e-mail addresses.
"""
import re
from gettext import gettext as _

from vmm.domain import check_domainname, get_gid
from vmm.constants import (
    DOMAIN_NO_NAME,
    INVALID_ADDRESS,
    LOCALPART_INVALID,
    LOCALPART_TOO_LONG,
    DOMAIN_INVALID,
)
from vmm.errors import DomainError, EmailAddressError as EAErr


RE_LOCALPART = re.compile(r"[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]", re.ASCII)


class EmailAddress:
    """Simple class for validated e-mail addresses."""

    __slots__ = ("_localpart", "_domainname")

    def __init__(self, address, _validate=True):
        """Creates a new instance from the string/unicode ``address``."""
        assert isinstance(address, str)
        self._localpart = None
        self._domainname = None
        if _validate:
            self._chk_address(address)

    @property
    def localpart(self):
        """The local-part of the address *local-part@domain*"""
        return self._localpart

    @property
    def domainname(self):
        """The domain part of the address *local-part@domain*"""
        return self._domainname

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self._localpart == other._localpart
                and self._domainname == other._domainname
            )
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return (
                self._localpart != other._localpart
                or self._domainname != other._domainname
            )
        return NotImplemented

    def __hash__(self):
        return hash((self._localpart.lower(), self._domainname.lower()))

    def __repr__(self):
        return "EmailAddress('%s@%s')" % (self._localpart, self._domainname)

    def __str__(self):
        return "%s@%s" % (self._localpart, self._domainname)

    def _chk_address(self, address):
        """Checks if the string ``address`` could be used for an e-mail
        address.  If so, it will assign the corresponding values to the
        attributes `_localpart` and `_domainname`."""
        parts = address.split("@")
        p_len = len(parts)
        if p_len < 2:
            raise EAErr(
                _("Missing the '@' sign in address: '%s'") % address, INVALID_ADDRESS
            )
        elif p_len > 2:
            raise EAErr(
                _("Too many '@' signs in address: '%s'") % address, INVALID_ADDRESS
            )
        if not parts[0]:
            raise EAErr(
                _("Missing local-part in address: '%s'") % address, LOCALPART_INVALID
            )
        if not parts[1]:
            raise EAErr(
                _("Missing domain name in address: '%s'") % address, DOMAIN_NO_NAME
            )
        self._localpart = check_localpart(parts[0])
        self._domainname = check_domainname(parts[1])


class DestinationEmailAddress(EmailAddress):
    """Provides additionally the domains group ID - when the domain is known
    in the database."""

    __slots__ = ("_gid", "_localhost")

    def __init__(self, address, dbh, _validate=False):
        """Creates a new DestinationEmailAddress instance

        Arguments:

        `address`: string/unicode
          a e-mail address like user@example.com
        `dbh`: psycopg2._psycopg.connection
          a database connection for the database access
        """
        super(DestinationEmailAddress, self).__init__(address, _validate)
        self._localhost = False
        if not _validate:
            try:
                self._chk_address(address)
            except DomainError as err:
                if err.code is DOMAIN_INVALID and address.split("@")[1] == "localhost":
                    self._localhost = True
                    self._domainname = "localhost"
                else:
                    raise
        self._gid = 0
        if not self._localhost:
            self._find_domain(dbh)
        else:
            self._localpart = self._localpart.lower()

    def _find_domain(self, dbh):
        """Checks if the domain is known"""
        self._gid = get_gid(dbh, self._domainname)
        if self._gid:
            self._localpart = self._localpart.lower()

    @property
    def at_localhost(self):
        """True when the address is something@localhost."""
        return self._localhost

    @property
    def gid(self):
        """The domains group ID. 0 if the domain is not known."""
        return self._gid


def check_localpart(localpart):
    """Returns the validated local-part `localpart`.

    Throws a `EmailAddressError` if the local-part is too long or contains
    invalid characters.
    """
    if len(localpart) > 64:
        raise EAErr(
            _("The local-part '%s' is too long.") % localpart, LOCALPART_TOO_LONG
        )
    invalid_chars = set(RE_LOCALPART.findall(localpart))
    if invalid_chars:
        i_chars = "".join(('"%s" ' % c for c in invalid_chars))
        raise EAErr(
            _("The local-part '%(l_part)s' contains invalid " "characters: %(i_chars)s")
            % {"l_part": localpart, "i_chars": i_chars},
            LOCALPART_INVALID,
        )
    return localpart
