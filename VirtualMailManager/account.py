# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2011, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.account
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's Account class to manage e-mail accounts.
"""

from VirtualMailManager.common import version_str
from VirtualMailManager.constants import \
     ACCOUNT_EXISTS, ACCOUNT_MISSING_PASSWORD, ALIAS_PRESENT, \
     INVALID_ARGUMENT, INVALID_MAIL_LOCATION, NO_SUCH_ACCOUNT, \
     NO_SUCH_DOMAIN, VMM_ERROR
from VirtualMailManager.domain import Domain
from VirtualMailManager.emailaddress import EmailAddress
from VirtualMailManager.errors import VMMError, AccountError as AErr
from VirtualMailManager.maillocation import MailLocation
from VirtualMailManager.password import pwhash
from VirtualMailManager.quotalimit import QuotaLimit
from VirtualMailManager.transport import Transport
from VirtualMailManager.serviceset import ServiceSet

__all__ = ('Account', 'get_account_by_uid')

_ = lambda msg: msg
cfg_dget = lambda option: None


class Account(object):
    """Class to manage e-mail accounts."""
    __slots__ = ('_addr', '_dbh', '_domain', '_mail', '_new', '_passwd',
                 '_qlimit', '_services', '_transport', '_uid')

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
            # TP: Hm, what “quotation marks” should be used?
            # If you are unsure have a look at:
            # http://en.wikipedia.org/wiki/Quotation_mark,_non-English_usage
            raise AErr(_(u"The domain '%s' does not exist.") %
                       self._addr.domainname, NO_SUCH_DOMAIN)
        self._uid = 0
        self._mail = None
        self._qlimit = self._domain.quotalimit
        self._services = self._domain.serviceset
        self._transport = self._domain.transport
        self._passwd = None
        self._new = True
        self._load()

    def __nonzero__(self):
        """Returns `True` if the Account is known, `False` if it's new."""
        return not self._new

    def _load(self):
        """Load 'uid', 'mid', 'qid', 'ssid'  and 'tid' from the database and
        set _new to `False` - if the user could be found. """
        dbc = self._dbh.cursor()
        dbc.execute('SELECT uid, mid, qid, ssid, tid FROM users WHERE gid = '
                    '%s AND local_part = %s', (self._domain.gid,
                                               self._addr.localpart))
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._uid, _mid, _qid, _ssid, _tid = result
            if _qid != self._qlimit.qid:
                self._qlimit = QuotaLimit(self._dbh, qid=_qid)
            if _ssid != self._services.ssid:
                self._services = ServiceSet(self._dbh, ssid=_ssid)
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
                         u">= v%(version)s.") % {
                       'mbfmt': maillocation.mbformat,
                       'version': version_str(maillocation.dovecot_version)},
                       INVALID_MAIL_LOCATION)
        if not maillocation.postfix and \
          self._transport.transport.lower() in ('virtual:', 'virtual'):
            raise AErr(_(u"Invalid transport '%(transport)s' for mailbox "
                         u"format '%(mbfmt)s'.") %
                       {'transport': self._transport,
                        'mbfmt': maillocation.mbformat}, INVALID_MAIL_LOCATION)
        self._mail = maillocation
        self._set_uid()

    def _update_tables(self, column, value):
        """Update various columns in the users table.

        Arguments:

        `column` : basestring
          Name of the table column. Currently: qid, ssid and tid
        `value` : long
          The referenced key
        """
        if column not in ('qid', 'ssid', 'tid'):
            raise ValueError('Unknown column: %r' % column)
        dbc = self._dbh.cursor()
        dbc.execute('UPDATE users SET %s = %%s WHERE uid = %%s' % column,
                    (value, self._uid))
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def _count_aliases(self):
        """Count all alias addresses where the destination address is the
        address of the Account."""
        dbc = self._dbh.cursor()
        dbc.execute('SELECT COUNT(destination) FROM alias WHERE destination '
                    '= %s', (str(self._addr),))
        a_count = dbc.fetchone()[0]
        dbc.close()
        return a_count

    def _chk_state(self):
        """Raise an AccountError if the Account is new - not yet saved in the
        database."""
        if self._new:
            raise AErr(_(u"The account '%s' does not exist.") % self._addr,
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
        if not self._new:
            raise AErr(_(u"The account '%s' already exists.") % self._addr,
                       ACCOUNT_EXISTS)
        if not isinstance(password, basestring) or not password:
            raise AErr(_(u"Could not accept password: '%s'") % password,
                       ACCOUNT_MISSING_PASSWORD)
        self._passwd = password

    def save(self):
        """Save the new Account in the database."""
        if not self._new:
            raise AErr(_(u"The account '%s' already exists.") % self._addr,
                       ACCOUNT_EXISTS)
        if not self._passwd:
            raise AErr(_(u"No password set for account: '%s'") % self._addr,
                       ACCOUNT_MISSING_PASSWORD)
        self._prepare(MailLocation(self._dbh, mbfmt=cfg_dget('mailbox.format'),
                                   directory=cfg_dget('mailbox.root')))
        dbc = self._dbh.cursor()
        dbc.execute('INSERT INTO users (local_part, passwd, uid, gid, mid, '
                    'qid, ssid, tid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (self._addr.localpart,
                     pwhash(self._passwd, user=self._addr), self._uid,
                     self._domain.gid, self._mail.mid, self._qlimit.qid,
                     self._services.ssid, self._transport.tid))
        self._dbh.commit()
        dbc.close()
        self._new = False

    def modify(self, field, value):
        """Update the Account's *field* to the new *value*.

        Possible values for *field* are: 'name', 'password'.

        Arguments:

        `field` : basestring
          The attribute name: 'name' or 'password'
        `value` : basestring
          The new value of the attribute.
        """
        if field not in ('name', 'password'):
            raise AErr(_(u"Unknown field: '%s'") % field, INVALID_ARGUMENT)
        self._chk_state()
        dbc = self._dbh.cursor()
        if field == 'password':
            dbc.execute('UPDATE users SET passwd = %s WHERE uid = %s',
                        (pwhash(value, user=self._addr), self._uid))
        else:
            dbc.execute('UPDATE users SET name = %s WHERE uid = %s',
                        (value, self._uid))
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def update_quotalimit(self, quotalimit):
        """Update the user's quota limit.

        Arguments:

        `quotalimit` : VirtualMailManager.quotalimit.QuotaLimit
          the new quota limit of the domain.
        """
        if cfg_dget('misc.dovecot_version') < 0x10102f00:
            raise VMMError(_(u'PostgreSQL-based dictionary quota requires '
                             u'Dovecot >= v1.1.2.'), VMM_ERROR)
        self._chk_state()
        assert isinstance(quotalimit, QuotaLimit)
        if quotalimit == self._qlimit:
            return
        self._update_tables('qid', quotalimit.qid)
        self._qlimit = quotalimit

    def update_serviceset(self, serviceset):
        """Assign a different set of services to the Account.

        Argument:

        `serviceset` : VirtualMailManager.serviceset.ServiceSet
          the new service set.
        """
        self._chk_state()
        assert isinstance(serviceset, ServiceSet)
        if serviceset == self._services:
            return
        self._update_tables('ssid', serviceset.ssid)
        self._services = serviceset

    def update_transport(self, transport):
        """Sets a new transport for the Account.

        Arguments:

        `transport` : VirtualMailManager.transport.Transport
          the new transport
        """
        self._chk_state()
        assert isinstance(transport, Transport)
        if transport == self._transport:
            return
        if transport.transport.lower() in ('virtual', 'virtual:') and \
           not self._mail.postfix:
            raise AErr(_(u"Invalid transport '%(transport)s' for mailbox "
                         u"format '%(mbfmt)s'.") %
                       {'transport': transport, 'mbfmt': self._mail.mbformat},
                       INVALID_MAIL_LOCATION)
        self._update_tables('tid', transport.tid)
        self._transport = transport

    def get_info(self):
        """Returns a dict with some information about the Account.

        The keys of the dict are: 'address', 'gid', 'home', 'imap'
        'mail_location', 'name', 'pop3', 'sieve', 'smtp', transport', 'uid',
        'uq_bytes', 'uq_messages', 'ql_bytes', and 'ql_messages'.
        """
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute('SELECT name, CASE WHEN bytes IS NULL THEN 0 ELSE bytes '
                    'END, CASE WHEN messages IS NULL THEN 0 ELSE messages END '
                    'FROM users LEFT JOIN userquota USING (uid) WHERE '
                    'users.uid = %s', (self._uid,))
        info = dbc.fetchone()
        dbc.close()
        if info:
            info = dict(zip(('name', 'uq_bytes', 'uq_messages'), info))
            for service, state in self._services.services.iteritems():
                # TP: A service (e.g. pop3 or imap) may be enabled/usable or
                # disabled/unusable for a user.
                info[service] = (_('disabled'), _('enabled'))[state]
            info['address'] = self._addr
            info['gid'] = self._domain.gid
            info['home'] = '%s/%s' % (self._domain.directory, self._uid)
            info['mail_location'] = self._mail.mail_location
            info['ql_bytes'] = self._qlimit.bytes
            info['ql_messages'] = self._qlimit.messages
            info['transport'] = self._transport.transport
            info['uid'] = self._uid
            return info
        # nearly impossible‽
        raise AErr(_(u"Could not fetch information for account: '%s'") %
                   self._addr, NO_SUCH_ACCOUNT)

    def get_aliases(self):
        """Return a list with all alias e-mail addresses, whose destination
        is the address of the Account."""
        self._chk_state()
        dbc = self._dbh.cursor()
        dbc.execute("SELECT address ||'@'|| domainname FROM alias, "
                    "domain_name WHERE destination = %s AND domain_name.gid = "
                    "alias.gid AND domain_name.is_primary ORDER BY address",
                    (str(self._addr),))
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
            dbc.execute('DELETE FROM users WHERE uid = %s', (self._uid),)
            # delete also all aliases where the destination address is the same
            # as for this account.
            dbc.execute("DELETE FROM alias WHERE destination = %s",
                        (str(self._addr),))
            self._dbh.commit()
        else:  # check first for aliases
            a_count = self._count_aliases()
            if a_count > 0:
                dbc.close()
                raise AErr(_(u"There are %(count)d aliases with the "
                             u"destination address '%(address)s'.") %
                           {'count': a_count, 'address': self._addr},
                           ALIAS_PRESENT)
            dbc.execute('DELETE FROM users WHERE uid = %s', (self._uid,))
            self._dbh.commit()
        dbc.close()
        self._new = True
        self._uid = 0
        self._addr = self._dbh = self._domain = self._passwd = None
        self._mail = self._qlimit = self._services = self._transport = None


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
                (uid,))
    info = dbc.fetchone()
    dbc.close()
    if not info:
        raise AErr(_(u"There is no account with the UID: '%d'") % uid,
                   NO_SUCH_ACCOUNT)
    info = dict(zip(('address', 'uid', 'gid'), info))
    return info

del _, cfg_dget