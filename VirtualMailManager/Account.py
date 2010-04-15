# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.Account

    Virtual Mail Manager's Account class to manage e-mail accounts.
"""

from VirtualMailManager.Domain import Domain
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.Transport import Transport
from VirtualMailManager.constants.ERROR import \
     ACCOUNT_EXISTS, ACCOUNT_MISSING_PASSWORD, ALIAS_EXISTS, ALIAS_PRESENT, \
     INVALID_AGUMENT, NO_SUCH_ACCOUNT, NO_SUCH_DOMAIN, RELOCATED_EXISTS, \
     UNKNOWN_MAILLOCATION_NAME, UNKNOWN_SERVICE
from VirtualMailManager.errors import AccountError as AErr
from VirtualMailManager.maillocation import MailLocation, known_format
from VirtualMailManager.pycompat import all


_ = lambda msg: msg


class Account(object):
    """Class to manage e-mail accounts."""
    __slots__ = ('_addr', '_domain', '_mid', '_new', '_passwd', '_tid', '_uid',
                 '_dbh')

    def __init__(self, dbh, address):
        """Creates a new Account instance.

        When an account with the given *address* could be found in the
        database all relevant data will be loaded.

        Arguments:

        `dbh` : pyPgSQL.PgSQL.Connection
          A database connection for the database access.
        `address` : basestring
          The e-mail address of the (new) Account.
        """
        if not isinstance(address, EmailAddress):
            raise TypeError("Argument 'address' is not an EmailAddress")
        self._addr = address
        self._dbh = dbh
        self._domain = Domain(self._dbh, self._addr.domainname)
        if not self._domain.gid:
            raise AErr(_(u"The domain '%s' doesn't exist.") %
                       self._addr.domainname, NO_SUCH_DOMAIN)
        self._uid = 0
        self._mid = 0
        self._tid = 0
        self._passwd = None
        self._new = True
        self._load()

    def _load(self):
        """Load 'uid', 'mid' and 'tid' from the database and set _new to
        `False` - if the user could be found. """
        dbc = self._dbh.cursor()
        dbc.execute(
            "SELECT uid, mid, tid FROM users WHERE gid=%s AND local_part=%s",
                    self._domain.gid, self._addr.localpart)
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._uid, self._mid, self._tid = result
            self._new = False

    def _set_uid(self):
        """Set the unique ID for the new Account."""
        assert self._uid == 0
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('users_uid')")
        self._uid = dbc.fetchone()[0]
        dbc.close()

    def _prepare(self, maillocation):
        """Check and set different attributes - before we store the
        information in the database."""
        if not known_format(maillocation):
            raise AErr(_(u'Unknown mail_location mailbox format: %r') %
                       maillocation, UNKNOWN_MAILLOCATION_NAME)
        self._mid = MailLocation(format=maillocation).mid
        if not self._tid:
            self._tid = self._domain.tid
        self._set_uid()

    def _switch_state(self, state, dcvers, service):
        """Switch the state of the Account's services on or off. See
        Account.enable()/Account.disable() for more information."""
        self._chk_state()
        if service not in (None, 'all', 'imap', 'pop3', 'sieve', 'smtp'):
            raise AErr(_(u"Unknown service: '%s'.") % service, UNKNOWN_SERVICE)
        if dcvers > 11:
            sieve_col = 'sieve'
        else:
            sieve_col = 'managesieve'
        if service in ('smtp', 'pop3', 'imap'):
            sql = 'UPDATE users SET %s = %s WHERE uid = %d' % (service, state,
                                                               self._uid)
        elif service == 'sieve':
            sql = 'UPDATE users SET %s = %s WHERE uid = %d' % (sieve_col,
                                                               state,
                                                               self._uid)
        else:
            sql = 'UPDATE users SET smtp = %(s)s, pop3 = %(s)s, imap = %(s)s,\
 %(col)s = %(s)s WHERE uid = %(uid)d' % \
                {'s': state, 'col': sieve_col, 'uid': self._uid}
        dbc = self._dbh.cursor()
        dbc.execute(sql)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def _count_aliases(self):
        """Count all alias addresses where the destination address is the
        address of the Account."""
        dbc = self._dbh.cursor()
        sql = "SELECT COUNT(destination) FROM alias WHERE destination = '%s'"\
                % self._addr
        dbc.execute(sql)
        a_count = dbc.fetchone()[0]
        dbc.close()
        return a_count

    def _chk_state(self):
        """Raise an AccountError if the Account is new - not yet saved in the
        database."""
        if self._new:
            raise AErr(_(u"The account '%s' doesn't exist.") % self._addr,
                       NO_SUCH_ACCOUNT)

    @property
    def domain_directory(self):
        """The directory of the domain the Account belongs to."""
        return self._domain.directory

    @property
    def gid(self):
        """The Account's group ID."""
        return self._domain.gid

    @property
    def home(self):
        """The Account's home directory."""
        return '%s/%s' % (self._domain.directory, self._uid)

    @property
    def uid(self):
        """The Account's unique ID."""
        return self._uid

    def set_password(self, password):
        """Set a password for the new Account.

        If you want to update the password of an existing Account use
        Account.modify().

        Argument:

        `password` : basestring
          The hashed password for the new Account."""
        self._passwd = password

    def set_transport(self, transport):
        """Set the transport for the new Account.

        If you want to update the transport of an existing Account use
        Account.modify().

        Argument:

        `transport` : basestring
          The string representation of the transport, e.g.: 'dovecot:'
        """
        self._tid = Transport(self._dbh, transport=transport).tid

    def enable(self, dcvers, service=None):
        """Enable a/all service/s for the Account.

        Possible values for the *service* are: 'imap', 'pop3', 'sieve' and
        'smtp'. When all services should be enabled, use 'all' or the
        default value `None`.

        Arguments:

        `dcvers` : int
          The concatenated major and minor version number from
          `dovecot --version`.
        `service` : basestring
          The name of a service ('imap', 'pop3', 'smtp', 'sieve'), 'all'
          or `None`.
        """
        self._switch_state(True, dcvers, service)

    def disable(self, dcvers, service=None):
        """Disable a/all service/s for the Account.

        For more information see: Account.enable()."""
        self._switch_state(False, dcvers, service)

    def save(self, maillocation, dcvers, smtp, pop3, imap, sieve):
        """Save the new Account in the database.

        Arguments:

        `maillocation` : basestring
          The mailbox format of the mail_location: 'maildir', 'mbox',
          'dbox' or 'mdbox'.
        `dcvers` : int
          The concatenated major and minor version number from
          `dovecot --version`.
        `smtp, pop3, imap, sieve` : bool
          Indicates if the user of the Account should be able to use this
          services.
        """
        if not self._new:
            raise AErr(_(u"The account '%s' already exists.") % self._addr,
                       ACCOUNT_EXISTS)
        if not self._passwd:
            raise AErr(_(u"No password set for '%s'.") % self._addr,
                       ACCOUNT_MISSING_PASSWORD)
        assert all(isinstance(service, bool) for service in (smtp, pop3, imap,
                                                             sieve))
        if dcvers > 11:
            sieve_col = 'sieve'
        else:
            sieve_col = 'managesieve'
        self._prepare(maillocation)
        sql = "INSERT INTO users (local_part, passwd, uid, gid, mid, tid,\
 smtp, pop3, imap, %s) VALUES ('%s', '%s', %d, %d, %d, %d, %s, %s, %s, %s)" % (
            sieve_col, self._addr.localpart, self._passwd, self._uid,
            self._domain.gid, self._mid, self._tid, smtp, pop3, imap, sieve)
        dbc = self._dbh.cursor()
        dbc.execute(sql)
        self._dbh.commit()
        dbc.close()
        self._new = False

    def modify(self, field, value):
        """Update the Account's *field* to the new *value*.

        Possible values for *filed* are: 'name', 'password' and
        'transport'.  *value* is the *field*'s new value.

        Arguments:

        `field` : basestring
          The attribute name: 'name', 'password' or 'transport'
        `value` : basestring
          The new value of the attribute. The password is expected as a
          hashed password string.
        """
        if field not in ('name', 'password', 'transport'):
            raise AErr(_(u"Unknown field: '%s'") % field, INVALID_AGUMENT)
        self._chk_state()
        dbc = self._dbh.cursor()
        if field == 'password':
            dbc.execute('UPDATE users SET passwd = %s WHERE uid = %s',
                        value, self._uid)
        elif field == 'transport':
            self._tid = Transport(self._dbh, transport=value).tid
            dbc.execute('UPDATE users SET tid = %s WHERE uid = %s',
                        self._tid, self._uid)
        else:
            dbc.execute('UPDATE users SET name = %s WHERE uid = %s',
                        value, self._uid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def get_info(self, dcvers):
        """Returns a dict with some information about the Account.

        The keys of the dict are: 'address', 'gid', 'home', 'imap'
        'mail_location', 'name', 'pop3', 'sieve', 'smtp', transport' and
        'uid'.

        Argument:

        `dcvers` : int
          The concatenated major and minor version number from
          `dovecot --version`.
        """
        self._chk_state()
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
        if info:
            keys = ('name', 'uid', 'gid', 'mid', 'transport', 'smtp',
                    'pop3', 'imap', sieve_col)
            info = dict(zip(keys, info))
            for service in ('smtp', 'pop3', 'imap', sieve_col):
                if info[service]:
                    # TP: A service (pop3/imap) is enabled/usable for a user
                    info[service] = _('enabled')
                else:
                    # TP: A service (pop3/imap) isn't enabled/usable for a user
                    info[service] = _('disabled')
            info['address'] = self._addr
            info['home'] = '%s/%s' % (self._domain.directory, info['uid'])
            info['mail_location'] = MailLocation(mid=info['mid']).mail_location
            info['transport'] = Transport(self._dbh,
                                          tid=info['transport']).transport
            del info['mid']
            return info
        # nearly impossible‽
        raise AErr(_(u"Couldn't fetch information for account: '%s'") \
                   % self._addr, NO_SUCH_ACCOUNT)

    def get_aliases(self):
        """Return a list with all alias e-mail addresses, whose destination
        is the address of the Account."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute("SELECT address ||'@'|| domainname FROM alias, domain_name\
 WHERE destination = %s AND domain_name.gid = alias.gid\
 AND domain_name.is_primary ORDER BY address", str(self._addr))
        addresses = dbc.fetchall()
        dbc.close()
        aliases = []
        if addresses:
            aliases = [alias[0] for alias in addresses]
        return aliases

    def delete(self, delalias):
        """Delete the Account from the database.

        Argument:

        `delalias` : basestring
          if the values of delalias is 'delalias', all aliases, which
          points to the Account, will be also deleted."""
        self._chk_state()
        dbc = self._dbh.cursor()
        if delalias == 'delalias':
            dbc.execute('DELETE FROM users WHERE uid= %s', self._uid)
            # delete also all aliases where the destination address is the same
            # as for this account.
            dbc.execute("DELETE FROM alias WHERE destination = %s",
                        str(self._addr))
            self._dbh.commit()
        else:  # check first for aliases
            a_count = self._count_aliases()
            if a_count == 0:
                dbc.execute('DELETE FROM users WHERE uid = %s', self._uid)
                self._dbh.commit()
            else:
                dbc.close()
                raise AErr(_(u"There are %(count)d aliases with the \
destination address '%(address)s'.") % \
                           {'count': a_count, 'address': self._addr},
                           ALIAS_PRESENT)
        dbc.close()


def getAccountByID(uid, dbh):
    """Search an Account by its UID.

    Argument:

    `uid` : long
      The Account unique ID.
    `dbh` : pyPgSQL.PgSQL.Connection
      a database connection for the database access.
    """
    try:
        uid = long(uid)
    except ValueError:
        raise AErr(_(u'UID must be an int/long.'), INVALID_AGUMENT)
    if uid < 1:
        raise AErr(_(u'UID must be greater than 0.'), INVALID_AGUMENT)
    dbc = dbh.cursor()
    dbc.execute("SELECT local_part||'@'|| domain_name.domainname AS address,\
 uid, users.gid FROM users LEFT JOIN domain_name ON (domain_name.gid \
 = users.gid AND is_primary) WHERE uid = %s;", uid)
    info = dbc.fetchone()
    dbc.close()
    if not info:
        raise AErr(_(u"There is no account with the UID '%d'.") % uid,
                   NO_SUCH_ACCOUNT)
    info = dict(zip(('address', 'uid', 'gid'), info))
    return info


del _
