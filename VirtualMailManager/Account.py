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

from Exceptions import VMMAccountException as AccE
from Domain import Domain
from Transport import Transport
from MailLocation import MailLocation
from EmailAddress import EmailAddress
import VirtualMailManager as VMM
import constants.ERROR as ERR

class Account:
    """Class to manage e-mail accounts."""
    def __init__(self, dbh, address, password=None):
        self._dbh = dbh
        self._base = None
        if isinstance(address, EmailAddress):
            self._addr = address
        else:
            raise TypeError("Argument 'address' is not an EmailAddress")
        self._uid = 0
        self._gid = 0
        self._mid = 0
        self._tid = 0
        self._passwd = password
        self._setAddr()
        self._exists()
        if VMM.VirtualMailManager.aliasExists(self._dbh, self._addr):
            raise AccE(_(u"There is already an alias with the address »%s«.") %\
                    self._addr, ERR.ALIAS_EXISTS)
        if VMM.VirtualMailManager.relocatedExists(self._dbh, self._addr):
            raise AccE(
              _(u"There is already a relocated user with the address »%s«.") %\
                    self._addr, ERR.RELOCATED_EXISTS)

    def _exists(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT uid, mid, tid FROM users \
WHERE gid=%s AND local_part=%s",
                self._gid, self._addr._localpart)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self._uid, self._mid, self._tid = result
            return True
        else:
            return False

    def _setAddr(self):
        dom = Domain(self._dbh, self._addr._domainname)
        self._gid = dom.getID()
        if self._gid == 0:
            raise AccE(_(u"The domain »%s« doesn't exist yet.") %\
                    self._addr._domainname, ERR.NO_SUCH_DOMAIN)
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
            raise AccE(_(u"Unknown service »%s«.") % service,
                    ERR.UNKNOWN_SERVICE)
        if self._uid < 1:
            raise AccE(_(u"The account »%s« doesn't exists.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        dbc = self._dbh.cursor()
        if service in ['smtp', 'pop3', 'imap', 'managesieve']:
            dbc.execute(
                    "UPDATE users SET %s=%s WHERE local_part='%s' AND gid=%s"
                    % (service, state, self._addr._localpart, self._gid))
        elif state:
            dbc.execute("UPDATE users SET smtp = TRUE, pop3 = TRUE,\
 imap = TRUE, managesieve = TRUE WHERE local_part = %s AND gid = %s",
                self._addr._localpart, self._gid)
        else:
            dbc.execute("UPDATE users SET smtp = FALSE, pop3 = FALSE,\
 imap = FALSE, managesieve = FALSE WHERE local_part = %s AND gid = %s",
                self._addr._localpart, self._gid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def __aliaseCount(self):
        dbc = self._dbh.cursor()
        q = "SELECT COUNT(destination) FROM alias WHERE destination = '%s'"\
            %self._addr
        dbc.execute(q)
        a_count = dbc.fetchone()[0]
        dbc.close()
        return a_count

    def setPassword(self, password):
        self._passwd = password

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
                self._addr._localpart, self._passwd, self._uid, self._gid,
                self._mid, self._tid, smtp, pop3, imap, managesieve)
            self._dbh.commit()
            dbc.close()
        else:
            raise AccE(_(u'The account »%s« already exists.') % self._addr,
                    ERR.ACCOUNT_EXISTS)
       
    def modify(self, what, value):
        if self._uid == 0:
            raise AccE(_(u"The account »%s« doesn't exists.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        if what not in ['name', 'password', 'transport']:
            return False
        dbc = self._dbh.cursor()
        if what == 'password':
            dbc.execute("UPDATE users SET passwd=%s WHERE local_part=%s AND\
 gid=%s", value, self._addr._localpart, self._gid)
        elif what == 'transport':
            self._tid = Transport(self._dbh, transport=value).getID()
            dbc.execute("UPDATE users SET tid=%s WHERE local_part=%s AND\
 gid=%s", self._tid, self._addr._localpart, self._gid)
        else:
            dbc.execute("UPDATE users SET name=%s WHERE local_part=%s AND\
 gid=%s", value, self._addr._localpart, self._gid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def getInfo(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT name, uid, gid, mid, tid, smtp, pop3, imap, \
 managesieve FROM users WHERE local_part=%s AND gid=%s",
            self._addr._localpart, self._gid)
        info = dbc.fetchone()
        dbc.close()
        if info is None:
            raise AccE(_(u"The account »%s« doesn't exists.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        else:
            keys = ['name', 'uid', 'gid', 'maildir', 'transport', 'smtp',
                    'pop3', 'imap', 'managesieve']
            info = dict(zip(keys, info))
            for service in ['smtp', 'pop3', 'imap', 'managesieve']:
                if bool(info[service]):
                    info[service] = _('enabled')
                else:
                    info[service] = _('disabled')
            info['address'] = self._addr
            info['maildir'] = '%s/%s/%s' % (self._base, info['uid'],
                    MailLocation(self._dbh,
                        mid=info['maildir']).getMailLocation())
            info['transport'] = Transport(self._dbh,
                    tid=info['transport']).getTransport()
            return info

    def delete(self, delalias):
        if self._uid < 1:
            raise AccE(_(u"The account »%s« doesn't exists.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        dbc = self._dbh.cursor()
        if delalias == 'delalias':
            dbc.execute("DELETE FROM users WHERE gid=%s AND local_part=%s",
                    self._gid, self._addr._localpart)
            u_rc = dbc.rowcount
            # delete also all aliases where the destination address is the same
            # as for this account.
            dbc.execute("DELETE FROM alias WHERE destination = %s", self._addr)
            if u_rc > 0 or dbc.rowcount > 0:
                self._dbh.commit()
        else: # check first for aliases
            a_count = self.__aliaseCount()
            if a_count == 0:
                dbc.execute("DELETE FROM users WHERE gid=%s AND local_part=%s",
                        self._gid, self._addr._localpart)
                if dbc.rowcount > 0:
                    self._dbh.commit()
            else:
                dbc.close()
                raise AccE(
                  _(u"There are %(count)d aliases with the destination address\
 »%(address)s«.") %{'count': a_count, 'address': self._addr}, ERR.ALIAS_PRESENT)
        dbc.close()

def getAccountByID(uid, dbh):
    try:
        uid = long(uid)
    except ValueError:
        raise AccE(_(u'uid must be an int/long.'), ERR.INVALID_AGUMENT)
    if uid < 1:
        raise AccE(_(u'uid must be greater than 0.'), ERR.INVALID_AGUMENT)
    dbc = dbh.cursor()
    dbc.execute("SELECT local_part||'@'|| domain_name.domainname AS address,\
 uid, users.gid FROM users LEFT JOIN domain_name ON (domain_name.gid \
 = users.gid AND is_primary) WHERE uid = %s;", uid)
    info = dbc.fetchone()
    dbc.close()
    if info is None:
        raise AccE(_(u"There is no account with the UID »%d«.") % uid, 
                ERR.NO_SUCH_ACCOUNT)
    keys = ['address', 'uid', 'gid']
    info = dict(zip(keys, info))
    return info

