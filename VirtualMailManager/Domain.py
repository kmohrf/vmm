# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Virtual Mail Manager's Domain class to manage e-mail domains."""

from random import choice

from __main__ import ERR
from Exceptions import VMMDomainException as VMMDE
import VirtualMailManager as VMM
from Transport import Transport

MAILDIR_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'

class Domain(object):
    """Class to manage e-mail domains."""
    __slots__ = ('_basedir','_domaindir','_id','_name','_transport','_dbh')
    def __init__(self, dbh, domainname, basedir=None, transport=None):
        """Creates a new Domain instance.

        Keyword arguments:
        dbh -- a pyPgSQL.PgSQL.connection
        domainname -- name of the domain (str)
        transport -- default vmm.cfg/misc/transport  (str)
        """
        self._dbh = dbh
        self._name = VMM.VirtualMailManager.chkDomainname(domainname)
        self._basedir = basedir
        if transport is not None:
            self._transport = Transport(self._dbh, transport=transport)
        else:
            self._transport = transport
        self._id = 0
        self._domaindir = None
        if not self._exists() and self._isAlias():
            raise VMMDE(_(u"The domain “%s” is an alias domain.") %self._name,
                    ERR.DOMAIN_ALIAS_EXISTS)

    def _exists(self):
        """Checks if the domain already exists.

        If the domain exists _id will be set and returns True, otherwise False
        will be returned.
        """
        dbc = self._dbh.cursor()
        dbc.execute("SELECT gid, tid, domaindir FROM domain_data WHERE gid =\
 (SELECT gid FROM domain_name WHERE domainname = %s AND is_primary)",
                self._name)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self._id, self._domaindir = result[0], result[2]
            self._transport = Transport(self._dbh, tid=result[1])
            return True
        else:
            return False

    def _isAlias(self):
        """Checks if self._name is known for an alias domain."""
        dbc = self._dbh.cursor()
        dbc.execute('SELECT is_primary FROM domain_name WHERE domainname = %s',
                self._name)
        result = dbc.fetchone()
        dbc.close()
        if result is not None and not result[0]:
            return True
        else:
            return False

    def _setID(self):
        """Sets the ID of the domain."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('domain_gid')")
        self._id = dbc.fetchone()[0]
        dbc.close()

    def _prepare(self):
        self._setID()
        self._domaindir = "%s/%s/%i" % (self._basedir, choice(MAILDIR_CHARS),
                self._id)

    def _has(self, what):
        """Checks if aliases or accounts are assigned to the domain.

        If there are assigned accounts or aliases True will be returned,
        otherwise False will be returned.

        Keyword arguments:
        what -- 'alias' or 'users' (strings)
        """
        if what not in ['alias', 'users']:
            return False
        dbc = self._dbh.cursor()
        if what == 'users':
            dbc.execute("SELECT count(gid) FROM users WHERE gid=%s", self._id)
        else:
            dbc.execute("SELECT count(gid) FROM alias WHERE gid=%s", self._id)
        count = dbc.fetchone()
        dbc.close()
        if count[0] > 0:
            return True
        else:
            return False

    def _chkDelete(self, delUser, delAlias):
        """Checks dependencies for deletion.

        Keyword arguments:
        delUser -- ignore available accounts (bool)
        delAlias -- ignore available aliases (bool)
        """
        if not delUser:
            hasUser = self._has('users')
        else:
            hasUser = False
        if not delAlias:
            hasAlias = self._has('alias')
        else:
            hasAlias = False
        if hasUser and hasAlias:
            raise VMMDE(_(u'There are accounts and aliases.'),
                ERR.ACCOUNT_AND_ALIAS_PRESENT)
        elif hasUser:
            raise VMMDE(_(u'There are accounts.'),
                ERR.ACCOUNT_PRESENT)
        elif hasAlias:
            raise VMMDE(_(u'There are aliases.'),
                ERR.ALIAS_PRESENT)

    def save(self):
        """Stores the new domain in the database."""
        if self._id < 1:
            self._prepare()
            dbc = self._dbh.cursor()
            dbc.execute("INSERT INTO domain_data (gid, tid, domaindir)\
 VALUES (%s, %s, %s)", self._id, self._transport.getID(), self._domaindir)
            dbc.execute("INSERT INTO domain_name (domainname, gid, is_primary)\
 VALUES (%s, %s, %s)", self._name, self._id, True)
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMDE(_(u'The domain “%s” already exists.') % self._name,
                ERR.DOMAIN_EXISTS)

    def delete(self, delUser=False, delAlias=False):
        """Deletes the domain.

        Keyword arguments:
        delUser -- force deletion of available accounts (bool)
        delAlias -- force deletion of available aliases (bool)
        """
        if self._id > 0:
            self._chkDelete(delUser, delAlias)
            dbc = self._dbh.cursor()
            for t in ('alias','users','relocated','domain_name','domain_data'):
                dbc.execute("DELETE FROM %s WHERE gid = %d" % (t, self._id))
            self._dbh.commit()
            dbc.close()
        else:
            raise VMMDE(_(u"The domain “%s” doesn't exist.") % self._name,
                ERR.NO_SUCH_DOMAIN)

    def updateTransport(self, transport, force=False):
        """Sets a new transport for the domain.

        Keyword arguments:
        transport -- the new transport (str)
        force -- True/False force new transport for all accounts (bool)
        """
        if self._id > 0:
            if transport == self._transport.getTransport():
                return
            trsp = Transport(self._dbh, transport=transport)
            dbc = self._dbh.cursor()
            dbc.execute("UPDATE domain_data SET tid = %s WHERE gid = %s",
                    trsp.getID(), self._id)
            if dbc.rowcount > 0:
                self._dbh.commit()
            if force:
                dbc.execute("UPDATE users SET tid = %s WHERE gid = %s",
                        trsp.getID(), self._id)
                if dbc.rowcount > 0:
                    self._dbh.commit()
            dbc.close()
        else:
            raise VMMDE(_(u"The domain “%s” doesn't exist.") % self._name,
                ERR.NO_SUCH_DOMAIN)

    def getID(self):
        """Returns the ID of the domain."""
        return self._id

    def getDir(self):
        """Returns the directory of the domain."""
        return self._domaindir

    def getTransport(self):
        """Returns domain's transport."""
        return self._transport.getTransport()

    def getTransportID(self):
        """Returns the ID from the domain's transport."""
        return self._transport.getID()

    def getInfo(self):
        """Returns a dictionary with information about the domain."""
        sql = """\
SELECT gid, domainname, transport, domaindir, aliasdomains, accounts,
       aliases, relocated
  FROM vmm_domain_info
 WHERE gid = %i""" % self._id
        dbc = self._dbh.cursor()
        dbc.execute(sql)
        info = dbc.fetchone()
        dbc.close()
        if info is None:
            raise VMMDE(_(u"The domain “%s” doesn't exist.") % self._name,
                    ERR.NO_SUCH_DOMAIN)
        else:
            keys = ['gid', 'domainname', 'transport', 'domaindir',
                    'aliasdomains', 'accounts', 'aliases', 'relocated']
            return dict(zip(keys, info))

    def getAccounts(self):
        """Returns a list with all accounts from the domain."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT local_part from users where gid = %s ORDER BY\
 local_part", self._id)
        users = dbc.fetchall()
        dbc.close()
        accounts = []
        if len(users) > 0:
            addr = u'@'.join
            _dom = self._name
            accounts = [addr((account[0], _dom)) for account in users]
        return accounts

    def getAliases(self):
        """Returns a list with all aliases from the domain."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT DISTINCT address FROM alias WHERE gid = %s\
 ORDER BY address",  self._id)
        addresses = dbc.fetchall()
        dbc.close()
        aliases = []
        if len(addresses) > 0:
            addr = u'@'.join
            _dom = self._name
            aliases = [addr((alias[0], _dom)) for alias in addresses]
        return aliases

    def getRelocated(self):
        """Returns a list with all addresses from relocated users."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT address FROM relocated WHERE gid = %s\
 ORDER BY address", self._id)
        addresses = dbc.fetchall()
        dbc.close()
        relocated = []
        if len(addresses) > 0:
            addr = u'@'.join
            _dom = self._name
            relocated = [addr((address[0], _dom)) for address in addresses]
        return relocated

    def getAliaseNames(self):
        """Returns a list with all alias names from the domain."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT domainname FROM domain_name WHERE gid = %s\
 AND NOT is_primary ORDER BY domainname", self._id)
        anames = dbc.fetchall()
        dbc.close()
        aliasdomains = []
        if len(anames) > 0:
            aliasdomains = [aname[0] for aname in anames]
        return aliasdomains

def search(dbh, pattern=None, like=False):
    if pattern is not None and like is False:
        pattern = VMM.VirtualMailManager.chkDomainname(pattern)
    sql = 'SELECT gid, domainname, is_primary FROM domain_name'
    if pattern is None:
        pass
    elif like:
        sql += " WHERE domainname LIKE '%s'" % pattern
    else:
        sql += " WHERE domainname = '%s'" % pattern
    sql += ' ORDER BY is_primary DESC, domainname'
    dbc = dbh.cursor()
    dbc.execute(sql)
    doms = dbc.fetchall()
    dbc.close()

    domdict = {}
    order = [dom[0] for dom in doms if dom[2]]
    if len(order) == 0:
        for dom in doms:
            if dom[0] not in order:
                order.append(dom[0])
    for gid, dom, is_primary in doms:
        if is_primary:
            domdict[gid] = [dom]
        else:
            try:
                domdict[gid].append(dom)
            except KeyError:
                domdict[gid] = [None, dom]
    del doms
    return order, domdict

