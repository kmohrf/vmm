# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2011, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.domain
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's Domain class to manage e-mail domains.
"""

import os
import re
from random import choice

from VirtualMailManager.constants import \
     ACCOUNT_AND_ALIAS_PRESENT, DOMAIN_ALIAS_EXISTS, DOMAIN_EXISTS, \
     DOMAIN_INVALID, DOMAIN_TOO_LONG, NO_SUCH_DOMAIN, VMM_ERROR
from VirtualMailManager.errors import VMMError, DomainError as DomErr
from VirtualMailManager.pycompat import all, any
from VirtualMailManager.quotalimit import QuotaLimit
from VirtualMailManager.transport import Transport


MAILDIR_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'
RE_DOMAIN = re.compile(r"^(?:[a-z0-9-]{1,63}\.){1,}[a-z]{2,6}$")
_ = lambda msg: msg
cfg_dget = lambda option: None


class Domain(object):
    """Class to manage e-mail domains."""
    __slots__ = ('_directory', '_gid', '_name', '_qlimit', '_transport',
                 '_dbh', '_new')

    def __init__(self, dbh, domainname):
        """Creates a new Domain instance.

        Loads all relevant data from the database, if the domain could be
        found.  To create a new domain call the methods set_directory() and
        set_transport() before save().

        A DomainError will be thrown when the *domainname* is the name of
        an alias domain.

        Arguments:

        `dbh` : pyPgSQL.PgSQL.Connection
          a database connection for the database access
        `domainname` : basestring
          The name of the domain
        """
        self._name = check_domainname(domainname)
        self._dbh = dbh
        self._gid = 0
        self._qlimit = None
        self._transport = None
        self._directory = None
        self._new = True
        self._load()

    def _load(self):
        """Load information from the database and checks if the domain name
        is the primary one.

        Raises a DomainError if Domain._name isn't the primary name of the
        domain.
        """
        dbc = self._dbh.cursor()
        dbc.execute('SELECT dd.gid, qid, tid, domaindir, is_primary FROM '
                    'domain_data dd, domain_name dn WHERE domainname = %s AND '
                    'dn.gid = dd.gid', (self._name,))
        result = dbc.fetchone()
        dbc.close()
        if result:
            if not result[4]:
                raise DomErr(_(u"The domain '%s' is an alias domain.") %
                             self._name, DOMAIN_ALIAS_EXISTS)
            self._gid, self._directory = result[0], result[3]
            self._qlimit = QuotaLimit(self._dbh, qid=result[1])
            self._transport = Transport(self._dbh, tid=result[2])
            self._new = False

    def _set_gid(self):
        """Sets the ID of the domain - if not set yet."""
        assert self._gid == 0
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('domain_gid')")
        self._gid = dbc.fetchone()[0]
        dbc.close()

    def _check_for_addresses(self):
        """Checks dependencies for deletion. Raises a DomainError if there
        are accounts, aliases and/or relocated users.
        """
        dbc = self._dbh.cursor()
        dbc.execute('SELECT count(gid) FROM users WHERE gid = %(gid)u '
                    'UNION SELECT count(gid) FROM alias WHERE gid = %(gid)u '
                    'UNION SELECT count(gid) FROM relocated WHERE gid = '
                    '%(gid)u' % {'gid': self._gid})
        result = dbc.fetchall()
        dbc.close()
        result = [count[0] for count in result]
        if any(result):
            keys = ('account_count', 'alias_count', 'relocated_count')
            raise DomErr(_(u'There are %(account_count)u accounts, '
                           u'%(alias_count)u aliases and %(relocated_count)u '
                           u'relocated users.') % dict(zip(keys, result)),
                         ACCOUNT_AND_ALIAS_PRESENT)

    def _chk_state(self):
        """Throws a DomainError if the Domain is new - not saved in the
        database."""
        if self._new:
            raise DomErr(_(u"The domain '%s' doesn't exist.") % self._name,
                         NO_SUCH_DOMAIN)

    def _update_tables(self, column, value, force=False):
        """Update various columns in the domain_data table. When *force* is
        `True` also the corresponding column in the users table will be
        updated.

        Arguments:

        `column` : basestring
          Name of the table column. Currently: qid and tid
        `value` : long
          The referenced key
        `force` : bool
          enforce the new setting also for existing users. Default: `False`
        """
        if column not in ('qid', 'tid'):
            raise ValueError('Unknown column: %r' % column)
        dbc = self._dbh.cursor()
        dbc.execute('UPDATE domain_data SET %s = %%s WHERE gid = %%s' % column,
                    (value, self._gid))
        if dbc.rowcount > 0:
            self._dbh.commit()
        if force:
            dbc.execute('UPDATE users SET %s = %%s WHERE gid = %%s' % column,
                        (value, self._gid))
            if dbc.rowcount > 0:
                self._dbh.commit()
        dbc.close()

    @property
    def gid(self):
        """The GID of the Domain."""
        return self._gid

    @property
    def name(self):
        """The Domain's name."""
        return self._name

    @property
    def directory(self):
        """The Domain's directory."""
        return self._directory

    @property
    def quotalimit(self):
        """The Domain's quota limit."""
        return self._qlimit

    @property
    def transport(self):
        """The Domain's transport."""
        return self._transport

    def set_directory(self, basedir):
        """Set the path value of the Domain's directory, inside *basedir*.

        Argument:

        `basedir` : basestring
          The base directory of all domains
        """
        if not self._new:
            raise DomErr(_(u"The domain '%s' already exists.") % self._name,
                         DOMAIN_EXISTS)
        assert self._directory is None
        self._set_gid()
        self._directory = os.path.join(basedir, choice(MAILDIR_CHARS),
                                       str(self._gid))

    def set_quotalimit(self, quotalimit):
        """Set the quota limit for the new Domain.

        Argument:

        `quotalimit` : VirtualMailManager.quotalimit.QuotaLimit
          The quota limit of the new Domain.
        """
        if not self._new:
            raise DomErr(_(u"The domain '%s' already exists.") % self._name,
                         DOMAIN_EXISTS)
        assert isinstance(quotalimit, QuotaLimit)
        self._qlimit = quotalimit

    def set_transport(self, transport):
        """Set the transport for the new Domain.

        Argument:

        `transport` : VirtualMailManager.Transport
          The transport of the new Domain
        """
        if not self._new:
            raise DomErr(_(u"The domain '%s' already exists.") % self._name,
                         DOMAIN_EXISTS)
        assert isinstance(transport, Transport)
        self._transport = transport

    def save(self):
        """Stores the new domain in the database."""
        if not self._new:
            raise DomErr(_(u"The domain '%s' already exists.") % self._name,
                         DOMAIN_EXISTS)
        assert all((self._directory, self._qlimit, self._transport))
        dbc = self._dbh.cursor()
        dbc.execute('INSERT INTO domain_data (gid, qid, tid, domaindir) '
                    'VALUES (%s, %s, %s, %s)', (self._gid, self._qlimit.qid,
                    self._transport.tid, self._directory))
        dbc.execute('INSERT INTO domain_name (domainname, gid, is_primary) '
                    'VALUES (%s, %s, TRUE)', (self._name, self._gid))
        self._dbh.commit()
        dbc.close()
        self._new = False

    def delete(self, force=False):
        """Deletes the domain.

        Arguments:

        `force` : bool
          force the deletion of all available accounts, aliases and
          relocated users.  When *force* is `False` and there are accounts,
          aliases and/or relocated users a DomainError will be raised.
          Default `False`
        """
        if not isinstance(force, bool):
            raise TypeError('force must be a bool')
        self._chk_state()
        if not force:
            self._check_for_addresses()
        dbc = self._dbh.cursor()
        for tbl in ('alias', 'users', 'relocated', 'domain_name',
                    'domain_data'):
            dbc.execute("DELETE FROM %s WHERE gid = %u" % (tbl, self._gid))
        self._dbh.commit()
        dbc.close()
        self._gid = 0
        self._directory = self._qlimit = self._transport = None
        self._new = True

    def update_quotalimit(self, quotalimit, force=False):
        """Update the quota limit of the Domain.

        If *force* is `True` the new *quotalimit* will be applied to
        all existing accounts of the domain. Otherwise the *quotalimit*
        will be only applied to accounts created from now on.

        Arguments:

        `quotalimit` : VirtualMailManager.quotalimit.QuotaLimit
          the new quota limit of the domain.
        `force` : bool
          enforce new quota limit for all accounts, default `False`
        """
        if cfg_dget('misc.dovecot_version') < 0x10102f00:
            raise VMMError(_(u'PostgreSQL-based dictionary quota requires '
                             u'Dovecot >= v1.1.2'), VMM_ERROR)
        self._chk_state()
        assert isinstance(quotalimit, QuotaLimit)
        if not force and quotalimit == self._qlimit:
            return
        self._update_tables('qid', quotalimit.qid, force)
        self._qlimit = quotalimit

    def update_transport(self, transport, force=False):
        """Sets a new transport for the Domain.

        If *force* is `True` the new *transport* will be assigned to all
        existing accounts.  Otherwise the *transport* will be only used for
        accounts created from now on.

        Arguments:

        `transport` : VirtualMailManager.Transport
          the new transport
        `force` : bool
          enforce new transport setting for all accounts, default `False`
        """
        self._chk_state()
        assert isinstance(transport, Transport)
        if not force and transport == self._transport:
            return
        self._update_tables('tid', transport.tid, force)
        self._transport = transport

    def get_info(self):
        """Returns a dictionary with information about the domain."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute('SELECT aliasdomains, accounts, aliases, relocated '
                    'FROM vmm_domain_info WHERE gid = %s', (self._gid,))
        info = dbc.fetchone()
        dbc.close()
        keys = ('aliasdomains', 'accounts', 'aliases', 'relocated')
        info = dict(zip(keys, info))
        info['gid'] = self._gid
        info['domainname'] = self._name
        info['transport'] = self._transport.transport
        info['domaindir'] = self._directory
        info['bytes'] = self._qlimit.bytes
        info['messages'] = self._qlimit.messages
        return info

    def get_accounts(self):
        """Returns a list with all accounts of the domain."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute('SELECT local_part from users where gid = %s ORDER BY '
                    'local_part', (self._gid,))
        users = dbc.fetchall()
        dbc.close()
        accounts = []
        if users:
            addr = u'@'.join
            _dom = self._name
            accounts = [addr((account[0], _dom)) for account in users]
        return accounts

    def get_aliases(self):
        """Returns a list with all aliases e-mail addresses of the domain."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute('SELECT DISTINCT address FROM alias WHERE gid = %s ORDER '
                    'BY address', (self._gid,))
        addresses = dbc.fetchall()
        dbc.close()
        aliases = []
        if addresses:
            addr = u'@'.join
            _dom = self._name
            aliases = [addr((alias[0], _dom)) for alias in addresses]
        return aliases

    def get_relocated(self):
        """Returns a list with all addresses of relocated users."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute('SELECT address FROM relocated WHERE gid = %s ORDER BY '
                    'address', (self._gid,))
        addresses = dbc.fetchall()
        dbc.close()
        relocated = []
        if addresses:
            addr = u'@'.join
            _dom = self._name
            relocated = [addr((address[0], _dom)) for address in addresses]
        return relocated

    def get_aliase_names(self):
        """Returns a list with all alias domain names of the domain."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute('SELECT domainname FROM domain_name WHERE gid = %s AND '
                    'NOT is_primary ORDER BY domainname', (self._gid,))
        anames = dbc.fetchall()
        dbc.close()
        aliasdomains = []
        if anames:
            aliasdomains = [aname[0] for aname in anames]
        return aliasdomains


def check_domainname(domainname):
    """Returns the validated domain name `domainname`.

    Throws an `DomainError`, if the domain name is too long or doesn't
    look like a valid domain name (label.label.label).

    """
    if not RE_DOMAIN.match(domainname):
        domainname = domainname.encode('idna')
    if len(domainname) > 255:
        raise DomErr(_(u'The domain name is too long'), DOMAIN_TOO_LONG)
    if not RE_DOMAIN.match(domainname):
        raise DomErr(_(u"The domain name '%s' is invalid") % domainname,
                     DOMAIN_INVALID)
    return domainname


def get_gid(dbh, domainname):
    """Returns the group id of the domain *domainname*.

    If the domain couldn't be found in the database 0 will be returned.
    """
    domainname = check_domainname(domainname)
    dbc = dbh.cursor()
    dbc.execute('SELECT gid FROM domain_name WHERE domainname = %s',
                (domainname,))
    gid = dbc.fetchone()
    dbc.close()
    if gid:
        return gid[0]
    return 0


def search(dbh, pattern=None, like=False):
    """'Search' for domains by *pattern* in the database.

    *pattern* may be a domain name or a partial domain name - starting
    and/or ending with a '%' sign.  When the *pattern* starts or ends with
    a '%' sign *like* has to be `True` to perform a wildcard search.
    To retrieve all available domains use the arguments' default values.

    This function returns a tuple with a list and a dict: (order, domains).
    The order list contains the domains' gid, alphabetical sorted by the
    primary domain name.  The domains dict's keys are the gids of the
    domains. The value of item is a list.  The first list element contains
    the primary domain name or `None`.  The elements [1:] contains the
    names of alias domains.

    Arguments:

    `pattern` : basestring
      a (partial) domain name (starting and/or ending with a "%" sign)
    `like` : bool
      should be `True` when *pattern* starts/ends with a "%" sign
    """
    if pattern and not like:
        pattern = check_domainname(pattern)
    sql = 'SELECT gid, domainname, is_primary FROM domain_name'
    if pattern:
        if like:
            sql += " WHERE domainname LIKE '%s'" % pattern
        else:
            sql += " WHERE domainname = '%s'" % pattern
    sql += ' ORDER BY is_primary DESC, domainname'
    dbc = dbh.cursor()
    dbc.execute(sql)
    result = dbc.fetchall()
    dbc.close()

    gids = [domain[0] for domain in result if domain[2]]
    domains = {}
    for gid, domain, is_primary in result:
        if is_primary:
            if not gid in domains:
                domains[gid] = [domain]
            else:
                domains[gid].insert(0, domain)
        else:
            if gid in gids:
                if gid in domains:
                    domains[gid].append(domain)
                else:
                    domains[gid] = [domain]
            else:
                gids.append(gid)
                domains[gid] = [None, domain]
    return gids, domains

del _, cfg_dget
