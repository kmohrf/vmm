# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.EmailAddress

    Virtual Mail Manager's EmailAddress class to handle e-mail addresses.
"""

import re

from VirtualMailManager import chk_domainname
from VirtualMailManager.constants.ERROR import \
     DOMAIN_NO_NAME, INVALID_ADDRESS, LOCALPART_INVALID, LOCALPART_TOO_LONG
from VirtualMailManager.Exceptions import VMMEmailAddressException as VMMEAE


RE_LOCALPART = """[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]"""


class EmailAddress(object):
    """Simple class for validated e-mail addresses."""
    __slots__ = ('localpart', 'domainname')

    def __init__(self, address):
        """Creates a new instance from the string/unicode ``address``."""
        if not isinstance(address, basestring):
            raise TypeError('address is not a str/unicode object: %r' %
                            address)
        self.localpart = None
        self.domainname = None
        self._chk_address(address)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.localpart == other.localpart and \
                    self.domainname == other.domainname
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.localpart != other.localpart or \
                    self.domainname != other.domainname
        return NotImplemented

    def __repr__(self):
        return "EmailAddress('%s@%s')" % (self.localpart, self.domainname)

    def __str__(self):
        return "%s@%s" % (self.localpart, self.domainname)

    def _chk_address(self, address):
        """Checks if the string ``address`` could be used for an e-mail
        address."""
        parts = address.split('@')
        p_len = len(parts)
        if p_len is 2:
            self.localpart = check_localpart(parts[0])
            if len(parts[1]) > 0:
                self.domainname = chk_domainname(parts[1])
            else:
                raise VMMEAE(_(u"Missing domain name after “%s@”.") %
                             self.localpart, DOMAIN_NO_NAME)
        elif p_len < 2:
            raise VMMEAE(_(u"Missing '@' sign in e-mail address “%s”.") %
                         address, INVALID_ADDRESS)
        elif p_len > 2:
            raise VMMEAE(_(u"Too many '@' signs in e-mail address “%s”.") %
                         address, INVALID_ADDRESS)


_ = lambda msg: msg


def check_localpart(localpart):
    """Validates the local-part of an e-mail address.

    Argument:
    localpart -- local-part of the e-mail address that should be validated
    """
    if len(localpart) < 1:
        raise VMMEAE(_(u'No local-part specified.'), LOCALPART_INVALID)
    if len(localpart) > 64:
        raise VMMEAE(_(u'The local-part “%s” is too long') % localpart,
                     LOCALPART_TOO_LONG)
    invalid_chars = set(re.findall(RE_LOCALPART, localpart))
    if invalid_chars:
        i_chrs = u''.join((u'“%s” ' % c for c in invalid_chars))
        raise VMMEAE(_(u"The local-part “%(l_part)s” contains invalid\
 characters: %(i_chrs)s") % {'l_part': localpart, 'i_chrs': i_chrs},
                     LOCALPART_INVALID)
    return localpart

del _
