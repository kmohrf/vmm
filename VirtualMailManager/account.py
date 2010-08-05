# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.account
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's Account class to manage e-mail accounts.
"""

from VirtualMailManager.domain import Domain
from VirtualMailManager.emailaddress import EmailAddress
from VirtualMailManager.transport import Transport
from VirtualMailManager.common import version_str
from VirtualMailManager.constants import \
     ACCOUNT_EXISTS, ACCOUNT_MISSING_PASSWORD, ALIAS_PRESENT, \
     INVALID_ARGUMENT, INVALID_MAIL_LOCATION, NO_SUCH_ACCOUNT, \
     NO_SUCH_DOMAIN, UNKNOWN_SERVICE
from VirtualMailManager.errors import AccountError as AErr
from VirtualMailManager.maillocation import MailLocation
from VirtualMailManager.password import pwhash

__all__ = ('SERVICES', 'Account', 'get_account_by_uid')

SERVICES = ('imap', 'pop3', 'smtp', 'sieve')

_ = lambda msg: msg
cfg_dget = lambda option: None


class Account(object):
    """Class to manage e-mail accounts."""
    __slots__ = ('_addr', '_dbh', '_domain', '_mail', '_new', '_passwd',
                 '_transport', '_uid')

    def __init__(self, dbh, address):
        """Creates a new Account instance.

        When an account with the given *address* could be found in the
        database all relevant data will be loaded.

        Arguments:

        `dbh` : pyPgSQL.PgSQL.Connection
          A database connection for the database access.
        `address` : VirtualMailManager.EmailAddress.EmailAddress
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
        self._mail = None
        self._transport = self._domain.transport
        self._passwd = None
        self._new = True
        self._load()

    def __nonzero__(self):
        """Returns `True` if the Account is known, `False` if it's new."""
        return not self._new

    def _load(self):
        """Load 'uid', 'mid' and 'tid' from the database and set _new to
        `False` - if the user could be found. """
        dbc = self._dbh.cursor()
        dbc.execute('SELECT uid, mid, tid FROM users WHERE gid = %s AND '
                    'local_part = %s', self._domain.gid, self._addr.localpart)
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._uid, _mid, _tid = result
            if _tid != self._transport.tid:
                self._transport = Transport(self._dbh, tid=_tid)
            self._mail = MailLocation(self._dbh, mid=_mid)
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
        information in the database.
        """
        if maillocation.dovecot_version > cfg_dget('misc.dovecot_version'):
            raise AErr(_(u"The mailbox format '%(mbfmt)s' requires Dovecot "
                         u">= v%(version)s") % {'mbfmt': maillocation.mbformat,
                       'version': version_str(maillocation.dovecot_version)},
                       INVALID_MAIL_LOCATION)
        if not maillocation.postfix and \
          self._transport.transport.lower() in ('virtual:', 'virtual'):
            raise AErr(_(u"Invalid transport '%(transport)s' for mailbox "
                         u"format '%(mbfmt)s'") %
                       {'transport': self._transport,
                        'mbfmt': maillocation.mbformat}, INVALID_MAIL_LOCATION)
        self._mail = maillocation
        self._set_uid()

    def _update_services(self, activate, *services):
        """Activate or deactivate the Account's services.

        Arguments:

        `activate`: bool
          When `True` the Account's user will be able to login to the
          services, otherwise the login will fail.
        `*services`
          No or one or more of the services: imap, pop3, smtp and sieve
        """
        self._chk_state()
        if services:
            services = set(services)
            for service in services:
                if service not in SERVICES:
                    raise AErr(_(u"Unknown service: '%s'.") % service,
                               UNKNOWN_SERVICE)
        else:
            services = SERVICES
        state = ('FALSE', 'TRUE')[activate]
        sql = 'UPDATE users SET %s WHERE uid = %u' % (
                    (' = %(s)s, '.join(services) + ' = %(s)s') % {'s': state},
                    self._uid)
        if 'sieve' in services and \
           cfg_dget('misc.dovecot_version') < 0x10200b02:
            sql = sql.replace('sieve', 'managesieve')
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
    def address(self):
        """The Account's EmailAddress instance."""
        return self._addr

    @property
    def domain(self):
        """The Domain to which the Account belongs to."""
        if self._domain:
            return self._domain
        return None

    @property
    def gid(self):
        """The Account's group ID."""
        if self._domain:
            return self._domain.gid
        return None

    @property
    def home(self):
        """The Account's home directory."""
        if not self._new:
            return '%s/%s' % (self._domain.directory, self._uid)
        return None

    @property
    def mail_location(self):
        """The Account's MailLocation."""
        return self._mail

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
          The password for the new Account.
        """
        if not isinstance(password, basestring) or not password:
            raise AErr(_(u"Couldn't accept password: '%s'") % password,
                       ACCOUNT_MISSING_PASSWORD)
        self._passwd = password

    def set_transport(self, transport):
        """Set the transport for the new Account.

        If you want to update the transport of an existing Account use
        Account.modify().

        Argument:

        `transport` : basestring
          The string representation of the transport, e.g.: 'dovecot:'
        """
        self._transport = Transport(self._dbh, transport=transport)

    def enable(self, *services):
        """Enable all or the given service/s for the Account.

        Possible *services* are: 'imap', 'pop3', 'sieve' and 'smtp'.
        When all services should be enabled, give no service name.

        Arguments:

        `*services` : basestring
          No or one or more of the services 'imap', 'pop3', 'smtp', and
          'sieve'.
        """
        self._update_services(True, *services)

    def disable(self, *services):
        """Disable all or the given service/s for the Account.

        For more information see: Account.enable()."""
        self._update_services(False, *services)

    def save(self):
        """Save the new Account in the database."""
        if not self._new:
            raise AErr(_(u"The account '%s' already exists.") % self._addr,
                       ACCOUNT_EXISTS)
        if not self._passwd:
            raise AErr(_(u"No password set for '%s'.") % self._addr,
                       ACCOUNT_MISSING_PASSWORD)
        if cfg_dget('misc.dovecot_version') >= 0x10200b02:
            sieve_col = 'sieve'
        else:
            sieve_col = 'managesieve'
        self._prepare(MailLocation(self._dbh, mbfmt=cfg_dget('mailbox.format'),
                                   directory=cfg_dget('mailbox.root')))
        sql = "INSERT INTO users (local_part, passwd, uid, gid, mid, tid,\
 smtp, pop3, imap, %s) VALUES ('%s', '%s', %d, %d, %d, %d, %s, %s, %s, %s)" % (
            sieve_col, self._addr.localpart, pwhash(self._passwd,
                                                    user=self._addr),
            self._uid, self._domain.gid, self._mail.mid, self._transport.tid,
            cfg_dget('account.smtp'), cfg_dget('account.pop3'),
            cfg_dget('account.imap'), cfg_dget('account.sieve'))
        dbc = self._dbh.cursor()
        dbc.execute(sql)
        self._dbh.commit()
        dbc.close()
        self._new = False

    def modify(self, field, value):
        """Update the Account's *field* to the new *value*.

        Possible values for *field* are: 'name', 'password' and
        'transport'.  *value* is the *field*'s new value.

        Arguments:

        `field` : basestring
          The attribute name: 'name', 'password' or 'transport'
        `value` : basestring
          The new value of the attribute.
        """
        if field not in ('name', 'password', 'transport'):
            raise AErr(_(u"Unknown field: '%s'") % field, INVALID_ARGUMENT)
        self._chk_state()
        dbc = self._dbh.cursor()
        if field == 'password':
            dbc.execute('UPDATE users SET passwd = %s WHERE uid = %s',
                        pwhash(value, user=self._addr), self._uid)
        elif field == 'transport':
            if value != self._transport.transport:
                self._transport = Transport(self._dbh, transport=value)
                dbc.execute('UPDATE users SET tid = %s WHERE uid = %s',
                            self._transport.tid, self._uid)
        else:
            dbc.execute('UPDATE users SET name = %s WHERE uid = %s',
                        value, self._uid)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def get_info(self):
        """Returns a dict with some information about the Account.

        The keys of the dict are: 'address', 'gid', 'home', 'imap'
        'mail_location', 'name', 'pop3', 'sieve', 'smtp', transport' and
        'uid'.
        """
        self._chk_state()
        if cfg_dget('misc.dovecot_version') >= 0x10200b02:
            sieve_col = 'sieve'
        else:
            sieve_col = 'managesieve'
        sql = 'SELECT name, smtp, pop3, imap, %s FROM users WHERE uid = %d' % \
            (sieve_col, self._uid)
        dbc = self._dbh.cursor()
        dbc.execute(sql)
        info = dbc.fetchone()
        dbc.close()
        if info:
            keys = ('name', 'smtp', 'pop3', 'imap', sieve_col)
            info = dict(zip(keys, info))
            for service in keys[1:]:
                if info[service]:
                    # TP: A service (pop3/imap) is enabled/usable for a user
                    info[service] = _('enabled')
                else:
                    # TP: A service (pop3/imap) isn't enabled/usable for a user
                    info[service] = _('disabled')
            info['address'] = self._addr
            info['gid'] = self._domain.gid
            info['home'] = '%s/%s' % (self._domain.directory, self._uid)
            info['mail_location'] = self._mail.mail_location
            info['transport'] = self._transport.transport
            info['uid'] = self._uid
            return info
        # nearly impossible‽
        raise AErr(_(u"Couldn't fetch information for account: '%s'") %
                   self._addr, NO_SUCH_ACCOUNT)

    def get_aliases(self):
        """Return a list with all alias e-mail addresses, whose destination
        is the address of the Account."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute("SELECT address ||'@'|| domainname FROM alias, "
                    "domain_name WHERE destination = %s AND domain_name.gid = "
                    "alias.gid AND domain_name.is_primary ORDER BY address",
                    str(self._addr))
        addresses = dbc.fetchall()
        dbc.close()
        aliases = []
        if addresses:
            aliases = [alias[0] for alias in addresses]
        return aliases

    def delete(self, force=False):
        """Delete the Account from the database.

        Argument:

        `force` : bool
          if *force* is `True`, all aliases, which points to the Account,
          will be also deleted.  If there are aliases and *force* is
          `False`, an AccountError will be raised.
        """
        if not isinstance(force, bool):
            raise TypeError('force must be a bool')
        self._chk_state()
        dbc = self._dbh.cursor()
        if force:
            dbc.execute('DELETE FROM users WHERE uid = %s', self._uid)
            # delete also all aliases where the destination address is the same
            # as for this account.
            dbc.execute("DELETE FROM alias WHERE destination = %s",
                        str(self._addr))
            self._dbh.commit()
        else:  # check first for aliases
            a_count = self._count_aliases()
            if a_count > 0:
                dbc.close()
                raise AErr(_(u"There are %(count)d aliases with the "
                             u"destination address '%(address)s'.") %
                           {'count': a_count, 'address': self._addr},
                           ALIAS_PRESENT)
            dbc.execute('DELETE FROM users WHERE uid = %s', self._uid)
            self._dbh.commit()
        dbc.close()
        self._new = True
        self._uid = 0
        self._addr = self._dbh = self._domain = self._passwd = None
        self._mail = self._transport = None


def get_account_by_uid(uid, dbh):
    """Search an Account by its UID.

    This function returns a dict (keys: 'address', 'gid' and 'uid'), if an
    Account with the given *uid* exists.

    Argument:

    `uid` : long
      The Account unique ID.
    `dbh` : pyPgSQL.PgSQL.Connection
      a database connection for the database access.
    """
    try:
        uid = long(uid)
    except ValueError:
        raise AErr(_(u'UID must be an int/long.'), INVALID_ARGUMENT)
    if uid < 1:
        raise AErr(_(u'UID must be greater than 0.'), INVALID_ARGUMENT)
    dbc = dbh.cursor()
    dbc.execute("SELECT local_part||'@'|| domain_name.domainname AS address, "
                "uid, users.gid FROM users LEFT JOIN domain_name ON "
                "(domain_name.gid = users.gid AND is_primary) WHERE uid = %s",
                uid)
    info = dbc.fetchone()
    dbc.close()
    if not info:
        raise AErr(_(u"There is no account with the UID '%d'.") % uid,
                   NO_SUCH_ACCOUNT)
    info = dict(zip(('address', 'uid', 'gid'), info))
    return info

del _, cfg_dget
