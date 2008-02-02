#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Virtual Mail Manager's Account class to manage e-mail accounts."""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

from Exceptions import VMMAccountException
from Domain import Domain
import constants.ERROR as ERR

class Account:
    """Class to manage e-mail accounts."""
    def __init__(self, dbh, basedir, address, password=None):
        self._dbh = dbh
        self._base = basedir
        self._base = None
        self._addr = address
        self._localpart = None
        self._name = None
        self._uid = 0
        self._gid = 0
        self._passwd = password
        self._home = None
        self._setAddr(address)
        self._exists()
        if self._isAlias():
            raise VMMAccountException(
            ('There is already an alias with address »%s«' % address,
                ERR.ALIAS_EXISTS))

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT uid FROM users WHERE gid=%s AND local_part=%s",
                self._gid, self._localpart)
        uid = dbc.fetchone()
        dbc.close()
        if uid is not None:
            self._uid = uid[0]
            return True
        else:
            return False

    def _isAlias(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT id FROM alias WHERE gid=%s AND address=%s",
                self._gid, self._localpart)
        aid = dbc.fetchone()
        dbc.close()
        if aid is not None:
            return True
        else:
            return False

    def _setAddr(self, address):
        self._localpart, d = address.split('@')
        dom = Domain(self._dbh, d, self._base)
        self._gid = dom.getID()
        self._base = dom.getDir()
        if self._gid == 0:
            raise VMMAccountException(("Domain »%s« doesn't exist." % d,
                ERR.NO_SUCH_DOMAIN))

    def _setID(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('users_uid')")
        self._uid = dbc.fetchone()[0]
        dbc.close()

    def _prepare(self):
        self._setID()
        self._home = "%i" % self._uid

    def _switchState(self, state):
        if not isinstance(state, bool):
            return False
        if self._uid < 1:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
        dbc = self._dbh.cursor()
        dbc.execute("""UPDATE users SET disabled=%s WHERE local_part=%s\
 AND gid=%s""", state, self._localpart, self._gid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def getUID(self):
        return self._uid

    def getGID(self):
        return self._gid

    def getDir(self, directory):
        if directory == 'domain':
            return '%s' % self._base
        elif directory == 'home':
            return '%s/%i' % (self._base, self._uid)

    def enable(self):
        self._switchState(False)

    def disable(self):
        self._switchState(True)

    def save(self, mail):
        if self._uid < 1:
            self._prepare()
            dbc = self._dbh.cursor()
            dbc.execute("""INSERT INTO users (local_part, passwd, uid, gid,\
 home, mail) VALUES (%s, %s, %s, %s, %s, %s)""", self._localpart,
                    self._passwd, self._uid, self._gid, self._home, mail)
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMAccountException(('Account already exists.',
                ERR.ACCOUNT_EXISTS))
       
    def modify(self, what, value):
        if self._uid == 0:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
        if what not in ['name', 'password']:
            return False
        dbc = self._dbh.cursor()
        if what == 'password':
            dbc.execute("UPDATE users SET passwd=%s WHERE local_part=%s AND\
 gid=%s", value, self._localpart, self._gid)
        else:
            dbc.execute("UPDATE users SET name=%s WHERE local_part=%s AND\
 gid=%s", value, self._localpart, self._gid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def getInfo(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT name, uid, gid, home, mail, disabled FROM users\
 WHERE local_part=%s AND gid=%s", self._localpart, self._gid)
        info = dbc.fetchone()
        dbc.close()
        if info is None:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
        else:
            keys = ['name', 'uid', 'gid', 'home', 'mail', 'disabled']
            info = dict(zip(keys, info))
            if bool(info['disabled']):
                info['disabled'] = 'Yes'
            else:
                info['disabled'] = 'No'
            info['address'] = self._addr
            info['home'] = '%s/%s' % (self._base, info['home'])
            return info

    def delete(self):
        if self._uid > 0:
            dbc = self._dbh.cursor()
            dbc.execute("DELETE FROM users WHERE gid=%s AND local_part=%s",
                    self._gid, self._localpart)
            if dbc.rowcount > 0:
                self._dbh.commit()
            dbc.close()
        else:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
