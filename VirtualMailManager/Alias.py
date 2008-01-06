#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# opyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Virtual Mail Manager's Alias class to manage email aliases."""

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

from Exceptions import VMMAliasException
from Domain import Domain
import constants.ERROR as ERR

class Alias:
    """Class to manage email accounts."""
    def __init__(self, dbh, address, basedir, destination=None):
        if address == destination:
            raise VMMAliasException(('Address and destination are identical.',
                ERR.ALIAS_ADDR_DEST_IDENTICAL))
        self._dbh = dbh
        self._addr = address
        self._dest = destination
        self._localpart = None
        self._gid = 0
        self._aid = 0
        self._setAddr(basedir)
        if not self._dest is None:
            self._exists()
        if self._isAccount():
            raise VMMAliasException(
            ('There is already an account with address «%s»' % self._addr,
                ERR.ACCOUNT_EXISTS))

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT id FROM alias WHERE gid=%s AND address=%s\
 AND destination=%s", self._gid, self._localpart, self._dest)
        aid = dbc.fetchone()
        dbc.close()
        if aid is not None:
            self._aid = aid[0]
            return True
        else:
            return False

    def _isAccount(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT uid FROM users WHERE gid=%s AND local_part=%s",
                self._gid, self._localpart)
        uid = dbc.fetchone()
        dbc.close()
        if uid is not None:
            return True
        else:
            return False
        
    def _setAddr(self, basedir):
        self._localpart, d = self._addr.split('@')
        dom = Domain(self._dbh, d, basedir)
        self._gid = dom.getID()
        if self._gid == 0:
            raise VMMAliasException(("Domain «%s» doesn't exist." % d,
                ERR.NO_SUCH_DOMAIN))

    def save(self):
        if self._dest is None:
           raise VMMAliasException(('No destination address for alias denoted.',
               ERR.ALIAS_MISSING_DEST))
        if self._aid < 1:
            dbc = self._dbh.cursor()
            dbc.execute("INSERT INTO alias (gid, address, destination) VALUES\
 (%s, %s, %s)", self._gid, self._localpart, self._dest)
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMAliasException(("Alias already exists.", ERR.ALIAS_EXISTS))

    def getInfo(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT destination FROM alias WHERE gid=%s AND address=%s',
                self._gid, self._localpart)
        destinations = dbc.fetchall()
        dbc.close()
        if len(destinations) > 0:
            targets = []
            for destination in destinations:
                targets.append(destination[0])
            return targets
        else:
            raise VMMAliasException(("Alias doesn't exists", ERR.NO_SUCH_ALIAS))

    def delete(self):
        dbc = self._dbh.cursor()
        dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s",
                self._gid, self._localpart)
        rowcount = dbc.rowcount
        dbc.close()
        if rowcount > 0:
            self._dbh.commit()
        else:
            raise VMMAliasException(("Alias doesn't exists", ERR.NO_SUCH_ALIAS))

