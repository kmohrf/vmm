# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.EmailAddress

    Virtual Mail Manager's EmailAddress class to handle e-mail addresses.
"""
import re

from VirtualMailManager.Domain import check_domainname
from VirtualMailManager.constants.ERROR import \
     DOMAIN_NO_NAME, INVALID_ADDRESS, LOCALPART_INVALID, LOCALPART_TOO_LONG
from VirtualMailManager.errors import EmailAddressError as EAErr


RE_LOCALPART = re.compile(r"[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]")
_ = lambda msg: msg


class EmailAddress(object):
    """Simple class for validated e-mail addresses."""
    __slots__ = ('_localpart', '_domainname')

    def __init__(self, address):
        """Creates a new instance from the string/unicode ``address``."""
        assert isinstance(address, basestring)
        self._localpart = None
        self._domainname = None
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
            return self._localpart == other.localpart and \
                    self._domainname == other.domainname
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._localpart != other.localpart or \
                    self._domainname != other.domainname
        return NotImplemented

    def __hash__(self):
        return hash((self._localpart.lower(), self._domainname.lower()))

    def __repr__(self):
        return "EmailAddress('%s@%s')" % (self._localpart, self._domainname)

    def __str__(self):
        return '%s@%s' % (self._localpart, self._domainname)

    def _chk_address(self, address):
        """Checks if the string ``address`` could be used for an e-mail
        address.  If so, it will assign the corresponding values to the
        attributes `_localpart` and `_domainname`."""
        parts = address.split('@')
        p_len = len(parts)
        if p_len < 2:
            raise EAErr(_(u"Missing the '@' sign in address %r") % address,
                        INVALID_ADDRESS)
        elif p_len > 2:
            raise EAErr(_(u"Too many '@' signs in address %r") % address,
                        INVALID_ADDRESS)
        if not parts[0]:
            raise EAErr(_(u'Missing local-part in address %r') % address,
                        LOCALPART_INVALID)
        if not parts[1]:
            raise EAErr(_(u'Missing domain name in address %r') % address,
                        DOMAIN_NO_NAME)
        self._localpart = check_localpart(parts[0])
        self._domainname = check_domainname(parts[1])


def check_localpart(localpart):
    """Returns the validated local-part `localpart`.

    Throws a `EmailAddressError` if the local-part is too long or contains
    invalid characters.
    """
    if len(localpart) > 64:
        raise EAErr(_(u"The local-part '%s' is too long") % localpart,
                    LOCALPART_TOO_LONG)
    invalid_chars = set(RE_LOCALPART.findall(localpart))
    if invalid_chars:
        i_chars = u''.join((u'"%s" ' % c for c in invalid_chars))
        raise EAErr(_(u"The local-part '%(l_part)s' contains invalid \
characters: %(i_chars)s") %
                    {'l_part': localpart, 'i_chars': i_chars},
                    LOCALPART_INVALID)
    return localpart


del _
