# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Virtual Mail Manager's Account class to manage e-mail accounts."""

import VirtualMailManager.constants.ERROR as ERR
from VirtualMailManager.Domain import Domain
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.Exceptions import VMMAccountException as AccE
from VirtualMailManager.MailLocation import MailLocation
from VirtualMailManager.Transport import Transport
import VirtualMailManager as VMM

class Account(object):
    """Class to manage e-mail accounts."""
    __slots__ = ('_addr','_base','_gid','_mid','_passwd','_tid','_uid','_dbh')
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
        if self._uid < 1 and VMM.VirtualMailManager.aliasExists(self._dbh,
                self._addr):
            # TP: Hm, what quotation marks should be used?
            # If you are unsure have a look at:
            # http://en.wikipedia.org/wiki/Quotation_mark,_non-English_usage
            raise AccE(_(u"There is already an alias with the address “%s”.") %\
                    self._addr, ERR.ALIAS_EXISTS)
        if self._uid < 1 and VMM.VirtualMailManager.relocatedExists(self._dbh,
                self._addr):
            raise AccE(
              _(u"There is already a relocated user with the address “%s”.") %\
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
            raise AccE(_(u"The domain “%s” doesn't exist.") %\
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

    def _switchState(self, state, dcvers, service):
        if not isinstance(state, bool):
            return False
        if not service in (None, 'all', 'imap', 'pop3', 'sieve', 'smtp'):
            raise AccE(_(u"Unknown service “%s”.") % service,
                    ERR.UNKNOWN_SERVICE)
        if self._uid < 1:
            raise AccE(_(u"The account “%s” doesn't exist.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        if dcvers > 11:
            sieve_col = 'sieve'
        else:
            sieve_col = 'managesieve'
        if service in ('smtp', 'pop3', 'imap'):
            sql = 'UPDATE users SET %s = %s WHERE uid = %d' % (service, state,
                    self._uid)
        elif service == 'sieve':
            sql = 'UPDATE users SET %s = %s WHERE uid = %d' % (sieve_col,
                    state, self._uid)
        else:
            sql = 'UPDATE users SET smtp = %(s)s, pop3 = %(s)s, imap = %(s)s,\
 %(col)s = %(s)s WHERE uid = %(uid)d' % {
                's': state, 'col': sieve_col, 'uid': self._uid}
        dbc = self._dbh.cursor()
        dbc.execute(sql)
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

    def enable(self, dcvers, service=None):
        self._switchState(True, dcvers, service)

    def disable(self, dcvers, service=None):
        self._switchState(False, dcvers, service)

    def save(self, maillocation, dcvers, smtp, pop3, imap, sieve):
        if self._uid < 1:
            if dcvers > 11:
                sieve_col = 'sieve'
            else:
                sieve_col = 'managesieve'
            self._prepare(maillocation)
            sql = "INSERT INTO users (local_part, passwd, uid, gid, mid, tid,\
 smtp, pop3, imap, %s) VALUES ('%s', '%s', %d, %d, %d, %d, %s, %s, %s, %s)" % (
                sieve_col, self._addr._localpart, self._passwd, self._uid,
                self._gid, self._mid, self._tid, smtp, pop3, imap, sieve)
            dbc = self._dbh.cursor()
            dbc.execute(sql)
            self._dbh.commit()
            dbc.close()
        else:
            raise AccE(_(u'The account “%s” already exists.') % self._addr,
                    ERR.ACCOUNT_EXISTS)

    def modify(self, what, value):
        if self._uid == 0:
            raise AccE(_(u"The account “%s” doesn't exist.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        if what not in ['name', 'password', 'transport']:
            return False
        dbc = self._dbh.cursor()
        if what == 'password':
            dbc.execute('UPDATE users SET passwd = %s WHERE uid = %s',
                    value, self._uid)
        elif what == 'transport':
            self._tid = Transport(self._dbh, transport=value).getID()
            dbc.execute('UPDATE users SET tid = %s WHERE uid = %s',
                    self._tid, self._uid)
        else:
            dbc.execute('UPDATE users SET name = %s WHERE uid = %s',
                    value, self._uid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def getInfo(self, dcvers):
        if dcvers > 11:
            sieve_col = 'sieve'
        else:
            sieve_col = 'managesieve'
        sql = 'SELECT name, uid, gid, mid, tid, smtp, pop3, imap, %s\
 FROM users WHERE uid = %d' % (sieve_col, self._uid)
        dbc = self._dbh.cursor()
        dbc.execute(sql)
        info = dbc.fetchone()
        dbc.close()
        if info is None:
            raise AccE(_(u"The account “%s” doesn't exist.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        else:
            keys = ['name', 'uid', 'gid', 'maildir', 'transport', 'smtp',
                    'pop3', 'imap', sieve_col]
            info = dict(zip(keys, info))
            for service in ('smtp', 'pop3', 'imap', sieve_col):
                if bool(info[service]):
                    # TP: A service (pop3/imap/…) is enabled/usable for a user
                    info[service] = _('enabled')
                else:
                    # TP: A service (pop3/imap) isn't enabled/usable for a user
                    info[service] = _('disabled')
            info['address'] = self._addr
            info['maildir'] = '%s/%s/%s' % (self._base, info['uid'],
                    MailLocation(self._dbh,
                        mid=info['maildir']).getMailLocation())
            info['transport'] = Transport(self._dbh,
                    tid=info['transport']).getTransport()
            return info

    def getAliases(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT address ||'@'|| domainname FROM alias, domain_name\
 WHERE destination = %s AND domain_name.gid = alias.gid\
 AND domain_name.is_primary ORDER BY address", str(self._addr))
        addresses = dbc.fetchall()
        dbc.close()
        aliases = []
        if len(addresses) > 0:
            aliases = [alias[0] for alias in addresses]
        return aliases

    def delete(self, delalias):
        if self._uid < 1:
            raise AccE(_(u"The account “%s” doesn't exist.") % self._addr,
                    ERR.NO_SUCH_ACCOUNT)
        dbc = self._dbh.cursor()
        if delalias == 'delalias':
            dbc.execute('DELETE FROM users WHERE uid= %s', self._uid)
            u_rc = dbc.rowcount
            # delete also all aliases where the destination address is the same
            # as for this account.
            dbc.execute("DELETE FROM alias WHERE destination = %s",
                    str(self._addr))
            if u_rc > 0 or dbc.rowcount > 0:
                self._dbh.commit()
        else: # check first for aliases
            a_count = self.__aliaseCount()
            if a_count == 0:
                dbc.execute('DELETE FROM users WHERE uid = %s', self._uid)
                if dbc.rowcount > 0:
                    self._dbh.commit()
            else:
                dbc.close()
                raise AccE(
                  _(u"There are %(count)d aliases with the destination address\
 “%(address)s”.") %{'count': a_count, 'address': self._addr}, ERR.ALIAS_PRESENT)
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
        raise AccE(_(u"There is no account with the UID “%d”.") % uid,
                ERR.NO_SUCH_ACCOUNT)
    keys = ['address', 'uid', 'gid']
    info = dict(zip(keys, info))
    return info

