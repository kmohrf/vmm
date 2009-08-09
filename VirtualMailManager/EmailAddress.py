# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2009, VEB IT
# See COPYING for distribution information.

"""Virtual Mail Manager's EmailAddress class to handle e-mail addresses."""

from constants.VERSION import *

import re

from Exceptions import VMMEmailAddressException as VMMEAE
import VirtualMailManager as VMM
import constants.ERROR as ERR

RE_LOCALPART = """[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]"""

class EmailAddress(object):
    def __init__(self, address):
        self._localpart = None
        self._domainname = None
        self.__chkAddress(address)
    
    def __eq__(self, other):
        if hasattr(other, '_localpart') and hasattr(other, '_domainname'):
            return self._localpart == other._localpart\
                    and self._domainname == other._domainname
        else:
            return NotImplemented

    def __ne__(self, other):
        if hasattr(other, '_localpart') and hasattr(other, '_domainname'):
            return not self._localpart == other._localpart\
                    and self._domainname == other._domainname
        else:
            return NotImplemented

    def __repr__(self):
        return "EmailAddress('%s@%s')" % (self._localpart, self._domainname)

    def __str__(self):
        return "%s@%s" % (self._localpart, self._domainname)

    def __chkAddress(self, address):
        try:
            localpart, domain = address.split('@')
        except ValueError:
            raise VMMEAE(_(u"Missing '@' sign in e-mail address »%s«.") %
                address, ERR.INVALID_ADDRESS)
        except AttributeError:
            raise VMMEAE(_(u"»%s« looks not like an e-mail address.") %
                address, ERR.INVALID_ADDRESS)
        if len(domain) > 0:
            domain = VMM.VirtualMailManager.chkDomainname(domain)
        else:
            raise VMMEAE(_(u"Missing domain name after »%s@«.") %
                    localpart, ERR.DOMAIN_NO_NAME)
        localpart = self.__chkLocalpart(localpart)
        self._localpart, self._domainname = localpart, domain

    def __chkLocalpart(self, localpart):
        """Validates the local part of an e-mail address.
        
        Keyword arguments:
        localpart -- of the e-mail address that should be validated (str)
        """
        if len(localpart) < 1:
            raise VMMEAE(_(u'No localpart specified.'),
                ERR.LOCALPART_INVALID)
        if len(localpart) > 64:
            raise VMMEAE(_(u'The local part »%s« is too long') %
                localpart, ERR.LOCALPART_TOO_LONG)
        ic = set(re.findall(RE_LOCALPART, localpart))
        if len(ic):
            ichrs = ''
            for c in ic:
                ichrs += u"»%s« " % c
            raise VMMEAE(_(u"The local part »%(lpart)s« contains invalid\
 characters: %(ichrs)s") % {'lpart': localpart, 'ichrs': ichrs},
                ERR.LOCALPART_INVALID)
        return localpart

