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
from Transport import Transport
from MailLocation import MailLocation
import constants.ERROR as ERR

class Account:
    """Class to manage e-mail accounts."""
    def __init__(self, dbh, address, password=None):
        self._dbh = dbh
        self._base = None
        self._addr = address
        self._localpart = None
        self._name = None
        self._uid = 0
        self._gid = 0
        self._mid = 0
        self._tid = 0
        self._passwd = password
        self._setAddr()
        self._exists()
        if self._isAlias():
            raise VMMAccountException(
            ('There is already an alias with address »%s«' % address,
                ERR.ALIAS_EXISTS))

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT uid, mid, tid FROM users \
WHERE gid=%s AND local_part=%s",
                self._gid, self._localpart)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self._uid, self._mid, self._tid = result
            return True
        else:
            return False

    def _isAlias(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT gid FROM alias WHERE gid=%s AND address=%s",
                self._gid, self._localpart)
        gid = dbc.fetchone()
        dbc.close()
        if gid is not None:
            return True
        else:
            return False

    def _setAddr(self):
        self._localpart, d = self._addr.split('@')
        dom = Domain(self._dbh, d)
        self._gid = dom.getID()
        if self._gid == 0:
            raise VMMAccountException(("Domain »%s« doesn't exist." % d,
                ERR.NO_SUCH_DOMAIN))
        self._base = dom.getDir()
        self._tid = dom.getTransportID()

    def _setID(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('users_uid')")
        self._uid = dbc.fetchone()[0]
        dbc.close()

    def _prepare(self, maillocation):
        self._setID()
        self._mid = MailLocation(self._dbh, maillocation=maillocation).getID()

    def _switchState(self, state, service):
        if not isinstance(state, bool):
            return False
        if not service in ['smtp', 'pop3', 'imap', 'managesieve', 'all', None]:
            raise VMMAccountException(("Unknown service »%s«" % service,
                ERR.UNKNOWN_SERVICE))
        if self._uid < 1:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
        dbc = self._dbh.cursor()
        if service in ['smtp', 'pop3', 'imap', 'managesieve']:
            dbc.execute(
                    "UPDATE users SET %s=%s WHERE local_part='%s' AND gid=%s"
                    % (service, state, self._localpart, self._gid))
        elif state:
            dbc.execute("UPDATE users SET smtp = TRUE, pop3 = TRUE,\
 imap = TRUE, managesieve = TRUE WHERE local_part = %s AND gid = %s",
                self._localpart, self._gid)
        else:
            dbc.execute("UPDATE users SET smtp = FALSE, pop3 = FALSE,\
 imap = FALSE, managesieve = FALSE WHERE local_part = %s AND gid = %s",
                self._localpart, self._gid)
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

    def enable(self, service=None):
        self._switchState(True, service)

    def disable(self, service=None):
        self._switchState(False, service)

    def save(self, maillocation, smtp, pop3, imap, managesieve):
        if self._uid < 1:
            self._prepare(maillocation)
            dbc = self._dbh.cursor()
            dbc.execute("""INSERT INTO users (local_part, passwd, uid, gid,\
 mid, tid, smtp, pop3, imap, managesieve)\
 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                self._localpart, self._passwd, self._uid, self._gid, self._mid,
                self._tid, smtp, pop3, imap, managesieve)
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMAccountException(('Account already exists.',
                ERR.ACCOUNT_EXISTS))
       
    def modify(self, what, value):
        if self._uid == 0:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
        if what not in ['name', 'password', 'transport']:
            return False
        dbc = self._dbh.cursor()
        if what == 'password':
            dbc.execute("UPDATE users SET passwd=%s WHERE local_part=%s AND\
 gid=%s", value, self._localpart, self._gid)
        elif what == 'transport':
            self._tid = Transport(self._dbh, transport=value).getID()
            dbc.execute("UPDATE users SET tid=%s WHERE local_part=%s AND\
 gid=%s", self._tid, self._localpart, self._gid)
        else:
            dbc.execute("UPDATE users SET name=%s WHERE local_part=%s AND\
 gid=%s", value, self._localpart, self._gid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def getInfo(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT name, uid, gid, mid, tid, smtp, pop3, imap, \
 managesieve FROM users WHERE local_part=%s AND gid=%s",
            self._localpart, self._gid)
        info = dbc.fetchone()
        dbc.close()
        if info is None:
            raise VMMAccountException(("Account doesn't exists",
                ERR.NO_SUCH_ACCOUNT))
        else:
            keys = ['name', 'uid', 'gid', 'maildir', 'transport', 'smtp',
                    'pop3', 'imap', 'managesieve']
            info = dict(zip(keys, info))
            for service in ['smtp', 'pop3', 'imap', 'managesieve']:
                if bool(info[service]):
                    info[service] = 'enabled'
                else:
                    info[service] = 'disabled'
            info['address'] = self._addr
            info['maildir'] = '%s/%s/%s' % (self._base, info['uid'],
                    MailLocation(self._dbh,
                        mid=info['maildir']).getMailLocation())
            info['transport'] = Transport(self._dbh,
                    tid=info['transport']).getTransport()
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


def getAccountByID(uid, dbh):
    try:
        uid = long(uid)
    except ValueError:
        raise VMMAccountException(('uid must be an int/long.',
            ERR.INVALID_AGUMENT))
    if uid < 1:
        raise VMMAccountException(('uid must be greater than 0.',
            ERR.INVALID_AGUMENT))
    dbc = dbh.cursor()
    dbc.execute("SELECT local_part||'@'||domains.domainname AS address, uid,\
 gid FROM users LEFT JOIN domains USING(gid) WHERE uid=%s", uid)
    info = dbc.fetchone()
    dbc.close()
    if info is None:
        raise VMMAccountException(("Account doesn't exists",
            ERR.NO_SUCH_ACCOUNT))
    keys = ['address', 'uid', 'gid']
    info = dict(zip(keys, info))
    return info

