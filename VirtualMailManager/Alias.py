#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Virtual Mail Manager's Alias class to manage e-mail aliases."""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

import gettext

from Exceptions import VMMAliasException
from Domain import Domain
import constants.ERROR as ERR

gettext.bindtextdomain('vmm', '/usr/local/share/locale')
gettext.textdomain('vmm')
_ = gettext.gettext

class Alias:
    """Class to manage e-mail accounts."""
    def __init__(self, dbh, address, destination=None):
        if address == destination:
            raise VMMAliasException((
                _('Address and destination are identical.'),
                ERR.ALIAS_ADDR_DEST_IDENTICAL))
        self._dbh = dbh
        self._addr = address
        self._dest = destination
        self._localpart = None
        self._gid = 0
        self._isNew = False
        self._setAddr()
        if not self._dest is None:
            self._exists()
        if self._isAccount():
            raise VMMAliasException(
            (_(u'There is already an account with address »%s«') % self._addr,
                ERR.ACCOUNT_EXISTS))

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT gid FROM alias WHERE gid=%s AND address=%s\
 AND destination=%s", self._gid, self._localpart, self._dest)
        gid = dbc.fetchone()
        dbc.close()
        if gid is None:
            self._isNew = True
        else:
            self._isNew = False

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
        
    def _setAddr(self):
        self._localpart, d = self._addr.split('@')
        dom = Domain(self._dbh, d)
        self._gid = dom.getID()
        if self._gid == 0:
            raise VMMAliasException((_(u"Domain »%s« doesn't exist.") % d,
                ERR.NO_SUCH_DOMAIN))

    def save(self):
        if self._dest is None:
           raise VMMAliasException((
               _('No destination address for alias denoted.'),
               ERR.ALIAS_MISSING_DEST))
        if self._isNew:
            dbc = self._dbh.cursor()
            dbc.execute("INSERT INTO alias (gid, address, destination) VALUES\
 (%s, %s, %s)", self._gid, self._localpart, self._dest)
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMAliasException((_("Alias already exists."),
                ERR.ALIAS_EXISTS))

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
            raise VMMAliasException((_("Alias doesn't exists"),
                ERR.NO_SUCH_ALIAS))

    def delete(self):
        dbc = self._dbh.cursor()
        if self._dest is None:
            dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s",
                    self._gid, self._localpart)
        else:
            dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s AND \
 destination=%s", self._gid, self._localpart, self._dest)
        rowcount = dbc.rowcount
        dbc.close()
        if rowcount > 0:
            self._dbh.commit()
        else:
            raise VMMAliasException((_("Alias doesn't exists"),
                ERR.NO_SUCH_ALIAS))

