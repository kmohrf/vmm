# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Virtual Mail Manager's EmailAddress class to handle e-mail addresses."""

import re

from VirtualMailManager import chk_domainname
from VirtualMailManager.constants.ERROR import \
     DOMAIN_NO_NAME, INVALID_ADDRESS, LOCALPART_INVALID, LOCALPART_TOO_LONG
from VirtualMailManager.Exceptions import VMMEmailAddressException as VMMEAE


RE_LOCALPART = """[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]"""


class EmailAddress(object):
    __slots__ = ('_localpart', '_domainname')

    def __init__(self, address):
        if not isinstance(address, basestring):
            raise TypeError('address is not a str/unicode object: %r' %
                            address)
        self._localpart = None
        self._domainname = None
        self.__chkAddress(address)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._localpart == other._localpart and \
                    self._domainname == other._domainname
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._localpart != other._localpart or \
                    self._domainname != other._domainname
        return NotImplemented

    def __repr__(self):
        return "EmailAddress('%s@%s')" % (self._localpart, self._domainname)

    def __str__(self):
        return "%s@%s" % (self._localpart, self._domainname)

    def __chkAddress(self, address):
        parts = address.split('@')
        p_len = len(parts)
        if p_len is 2:
            self._localpart = self.__chkLocalpart(parts[0])
            if len(parts[1]) > 0:
                self._domainname = chk_domainname(parts[1])
            else:
                raise VMMEAE(_(u"Missing domain name after “%s@”.") %
                             self._localpart, DOMAIN_NO_NAME)
        elif p_len < 2:
            raise VMMEAE(_(u"Missing '@' sign in e-mail address “%s”.") %
                         address, INVALID_ADDRESS)
        elif p_len > 2:
            raise VMMEAE(_(u"Too many '@' signs in e-mail address “%s”.") %
                         address, INVALID_ADDRESS)

    def __chkLocalpart(self, localpart):
        """Validates the local-part of an e-mail address.

        Arguments:
        localpart -- local-part of the e-mail address that should be validated
        """
        if len(localpart) < 1:
            raise VMMEAE(_(u'No local-part specified.'), LOCALPART_INVALID)
        if len(localpart) > 64:
            raise VMMEAE(_(u'The local-part “%s” is too long') % localpart,
                         LOCALPART_TOO_LONG)
        ic = set(re.findall(RE_LOCALPART, localpart))
        if len(ic):
            ichrs = u''.join((u'“%s” ' % c for c in ic))
            raise VMMEAE(_(u"The local-part “%(lpart)s” contains invalid\
 characters: %(ichrs)s") % {'lpart': localpart, 'ichrs': ichrs},
                         LOCALPART_INVALID)
        return localpart
