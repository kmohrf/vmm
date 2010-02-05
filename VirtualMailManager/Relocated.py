# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Virtual Mail Manager's Relocated class to manage relocated users."""

import VirtualMailManager.constants.ERROR as ERR
from VirtualMailManager.Domain import Domain
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.Exceptions import VMMRelocatedException as VMMRE
import VirtualMailManager as VMM

class Relocated(object):
    """Class to manage e-mail addresses of relocated users."""
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
            raise VMMRE(_(u"Address and destination are identical."),
                ERR.RELOCATED_ADDR_DEST_IDENTICAL)
        self._dbh = dbh
        self._gid = 0
        self._isNew = False
        self._setAddr()
        self._exists()
        if self._isNew and VMM.VirtualMailManager.accountExists(self._dbh,
                self._addr):
            raise VMMRE(_(u"There is already an account with address “%s”.") %\
                    self._addr, ERR.ACCOUNT_EXISTS)
        if self._isNew and VMM.VirtualMailManager.aliasExists(self._dbh,
                self._addr):
            raise VMMRE(
                    _(u"There is already an alias with the address “%s”.") %\
                    self._addr, ERR.ALIAS_EXISTS)

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT gid FROM relocated WHERE gid = %s AND address = %s",
                self._gid, self._addr._localpart)
        gid = dbc.fetchone()
        dbc.close()
        if gid is None:
            self._isNew = True

    def _setAddr(self):
        dom = Domain(self._dbh, self._addr._domainname)
        self._gid = dom.getID()
        if self._gid == 0:
            raise VMMRE(_(u"The domain “%s” doesn't exist.") %\
                    self._addr._domainname, ERR.NO_SUCH_DOMAIN)

    def save(self):
        if self._dest is None:
           raise VMMRE(
                   _(u"No destination address specified for relocated user."),
                   ERR.RELOCATED_MISSING_DEST)
        if self._isNew:
            dbc = self._dbh.cursor()
            dbc.execute("INSERT INTO relocated VALUES (%s, %s, %s)",
                    self._gid, self._addr._localpart, str(self._dest))
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMRE(
                    _(u"The relocated user “%s” already exists.") % self._addr,
                    ERR.RELOCATED_EXISTS)

    def getInfo(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT destination FROM relocated WHERE gid=%s\
 AND address=%s',
                self._gid, self._addr._localpart)
        destination = dbc.fetchone()
        dbc.close()
        if destination is not None:
            return destination[0]
        else:
            raise VMMRE(
                    _(u"The relocated user “%s” doesn't exist.") % self._addr,
                    ERR.NO_SUCH_RELOCATED)

    def delete(self):
        dbc = self._dbh.cursor()
        dbc.execute("DELETE FROM relocated WHERE gid = %s AND address = %s",
                self._gid, self._addr._localpart)
        rowcount = dbc.rowcount
        dbc.close()
        if rowcount > 0:
            self._dbh.commit()
        else:
            raise VMMRE(
                    _(u"The relocated user “%s” doesn't exist.") % self._addr,
                    ERR.NO_SUCH_RELOCATED)

