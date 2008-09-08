# -*- coding: UTF-8 -*-
# Copyright 2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Virtual Mail Manager's AliasDomain class to manage alias domains."""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

from Exceptions import VMMAliasDomainException as VADE
import constants.ERROR as ERR
import VirtualMailManager as VMM

class AliasDomain:
    """Class to manage e-mail alias domains."""
    def __init__(self, dbh, domainname, targetDomain=None):
        self._dbh = dbh
        self.__name = VMM.VirtualMailManager.chkDomainname(domainname)
        self.__gid = 0
        self._domain = targetDomain
        self._exists()

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT gid, is_primary FROM domain_name WHERE domainname\
 = %s', self.__name)
        alias = dbc.fetchone()
        dbc.close()
        if alias is not None:
            self.__gid, primary = alias
            if primary:
                raise VADE(_(u"The domain »%s« is a primary domain.") %
                        self.__name, ERR.ALIASDOMAIN_ISDOMAIN)

    def save(self):
        if self.__gid > 0:
            raise VADE(_(u'The alias domain »%s« already exists.') %self.__name,
                    ERR.ALIASDOMAIN_EXISTS)
        if self._domain is None:
            raise VADE(_(u'No destination domain for alias domain denoted.'),
                    ERR.ALIASDOMAIN_NO_DOMDEST)
        if self._domain._id < 1:
            raise VADE (_(u"The target domain »%s« doesn't exist yet.") %
                    self._domain._name, ERR.NO_SUCH_DOMAIN)
        dbc = self._dbh.cursor()
        dbc.execute('INSERT INTO domain_name (domainname, gid, is_primary)\
 VALUES (%s, %s, FALSE)', self.__name, self._domain._id)
        self._dbh.commit()
        dbc.close()

    def info(self):
        if self.__gid > 0:
            dbc = self._dbh.cursor()
            dbc.execute('SELECT domainname FROM domain_name WHERE gid = %s\
 AND is_primary', self.__gid)
            domain = dbc.fetchone()
            dbc.close()
            if domain is not None:
                return {'alias': self.__name, 'domain': domain[0]}
            else:# an almost unlikely case, isn't it?
                raise VADE(
                    _(u'There is no primary domain for the alias domain »%s«.')\
                            % self.__name, ERR.NO_SUCH_DOMAIN)
        else:
            raise VADE(_(u"The alias domain »%s« doesn't exist yet.") %
                    self.__name, ERR.NO_SUCH_ALIASDOMAIN)

    def switch(self):
        if self._domain is None:
            raise VADE(_(u'No destination domain for alias domain denoted.'),
                    ERR.ALIASDOMAIN_NO_DOMDEST)
        if self._domain._id < 1:
            raise VADE (_(u"The target domain »%s« doesn't exist yet.") %
                    self._domain._name, ERR.NO_SUCH_DOMAIN)
        if self.__gid < 1:
            raise VADE(_(u"The alias domain »%s« doesn't exist yet.") %
                    self.__name, ERR.NO_SUCH_ALIASDOMAIN)
        if self.__gid == self._domain._id:
            raise VADE(_(u"The alias domain »%(alias)s« is already assigned to\
 the domain »%(domain)s«.") %
                    {'alias': self.__name, 'domain': self._domain._name},
                    ERR.ALIASDOMAIN_EXISTS)
        dbc = self._dbh.cursor()
        dbc.execute('UPDATE domain_name SET gid = %s WHERE gid = %s\
 AND domainname = %s AND NOT is_primary',
                self._domain._id, self.__gid, self.__name)
        self._dbh.commit()
        dbc.close()

    def delete(self):
        if self.__gid > 0:
            dbc = self._dbh.cursor()
            dbc.execute('DELETE FROM domain_name WHERE domainname = %s \
 AND NOT is_primary', self.__name)
            if dbc.rowcount > 0:
                self._dbh.commit()
        else:
            raise VADE(
                  _(u"The alias domain »%s« doesn't exist yet.") % self.__name,
                  ERR.NO_SUCH_ALIASDOMAIN)

