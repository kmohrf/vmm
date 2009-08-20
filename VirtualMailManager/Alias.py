# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2009, VEB IT
# See COPYING for distribution information.

"""Virtual Mail Manager's Alias class to manage e-mail aliases."""

from constants.VERSION import *

from Exceptions import VMMAliasException as VMMAE
from Domain import Domain
from EmailAddress import EmailAddress
import constants.ERROR as ERR
import VirtualMailManager as VMM

class Alias(object):
    """Class to manage e-mail aliases."""
    __slots__ = ('_addr', '_dest', '_gid', '_isNew', '_dbh')
    def __init__(self, dbh, address, destination=None):
        if isinstance(address, EmailAddress):
            self._addr = address
        else:
            raise TypeError("Argument 'address' is not an EmailAddress")
        if destination is None:
            self._dest = None
        elif isinstance(destination, EmailAddress):
            self._dest = destination
        else:
            raise TypeError("Argument 'destination' is not an EmailAddress")
        if address == destination:
            raise VMMAE(_(u"Address and destination are identical."),
                ERR.ALIAS_ADDR_DEST_IDENTICAL)
        self._dbh = dbh
        self._gid = 0
        self._isNew = False
        self._setAddr()
        if not self._dest is None:
            self._exists()
        if self._isNew and VMM.VirtualMailManager.accountExists(self._dbh,
                self._addr):
            raise VMMAE(_(u"There is already an account with address »%s«.") %\
                    self._addr, ERR.ACCOUNT_EXISTS)
        if self._isNew and VMM.VirtualMailManager.relocatedExists(self._dbh,
                self._addr):
            raise VMMAE(
              _(u"There is already a relocated user with the address »%s«.") %\
                    self._addr, ERR.RELOCATED_EXISTS)

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT gid FROM alias WHERE gid=%s AND address=%s\
 AND destination=%s", self._gid, self._addr._localpart, str(self._dest))
        gid = dbc.fetchone()
        dbc.close()
        if gid is None:
            self._isNew = True

    def _setAddr(self):
        dom = Domain(self._dbh, self._addr._domainname)
        self._gid = dom.getID()
        if self._gid == 0:
            raise VMMAE(_(u"The domain »%s« doesn't exist yet.") %\
                    self._addr._domainname, ERR.NO_SUCH_DOMAIN)

    def _checkExpansion(self, limit):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT count(gid) FROM alias where gid=%s AND address=%s',
                self._gid, self._addr._localpart)
        curEx = dbc.fetchone()[0]
        dbc.close()
        if curEx == limit:
            errmsg = _(u"""Can't add new destination to alias »%(address)s«.
Currently this alias expands into %(count)i recipients.
One more destination will render this alias unusable.
Hint: Increase Postfix' virtual_alias_expansion_limit
""") % {'address': self._addr, 'count': curEx}
            raise VMMAE(errmsg, ERR.ALIAS_EXCEEDS_EXPANSION_LIMIT)

    def save(self, expansion_limit):
        if self._dest is None:
           raise VMMAE(_(u"No destination address for alias denoted."),
               ERR.ALIAS_MISSING_DEST)
        if self._isNew:
            self._checkExpansion(expansion_limit)
            dbc = self._dbh.cursor()
            dbc.execute("INSERT INTO alias (gid, address, destination) VALUES\
 (%s, %s, %s)", self._gid, self._addr._localpart, str(self._dest))
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMAE(
               _(u"The alias »%(a)s« with destination »%(d)s« already exists.")\
                       % {'a': self._addr, 'd': self._dest}, ERR.ALIAS_EXISTS)

    def getInfo(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT destination FROM alias WHERE gid=%s AND address=%s',
                self._gid, self._addr._localpart)
        destinations = dbc.fetchall()
        dbc.close()
        if len(destinations) > 0:
            targets = []
            for destination in destinations:
                targets.append(destination[0])
            return targets
        else:
            raise VMMAE(_(u"The alias »%s« doesn't exists.") % self._addr,
                    ERR.NO_SUCH_ALIAS)

    def delete(self):
        dbc = self._dbh.cursor()
        if self._dest is None:
            dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s",
                    self._gid, self._addr._localpart)
        else:
            dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s AND \
 destination=%s", self._gid, self._addr._localpart, str(self._dest))
        rowcount = dbc.rowcount
        dbc.close()
        if rowcount > 0:
            self._dbh.commit()
        else:
            if self._dest is None:
                msg = u"The alias »%s« doesn't exists." % self._addr
            else:
                msg = u"The alias »%(a)s« with destination »%(d)s« doesn't\
 exists." % {'a': self._addr, 'd': self._dest}
            raise VMMAE(_(msg), ERR.NO_SUCH_ALIAS)

