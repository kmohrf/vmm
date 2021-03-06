# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.account
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's Account class to manage e-mail accounts.
"""

from gettext import gettext as _

from vmm.common import version_str, format_domain_default
from vmm.constants import (
    ACCOUNT_EXISTS,
    ACCOUNT_MISSING_PASSWORD,
    ALIAS_PRESENT,
    INVALID_ARGUMENT,
    INVALID_MAIL_LOCATION,
    NO_SUCH_ACCOUNT,
    NO_SUCH_DOMAIN,
)
from vmm.common import validate_transport
from vmm.domain import Domain
from vmm.emailaddress import EmailAddress
from vmm.errors import AccountError as AErr
from vmm.maillocation import MailLocation
from vmm.password import pwhash
from vmm.quotalimit import QuotaLimit
from vmm.transport import Transport
from vmm.serviceset import ServiceSet

__all__ = ("Account", "get_account_by_uid")

cfg_dget = lambda option: None


class Account:
    """Class to manage e-mail accounts."""

    __slots__ = (
        "_addr",
        "_dbh",
        "_domain",
        "_mail",
        "_new",
        "_passwd",
        "_qlimit",
        "_services",
        "_transport",
        "_note",
        "_uid",
    )

    def __init__(self, dbh, address):
        """Creates a new Account instance.

        When an account with the given *address* could be found in the
        database all relevant data will be loaded.

        Arguments:

        `dbh` : psycopg2._psycopg.connection
          A database connection for the database access.
        `address` : vmm.EmailAddress.EmailAddress
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
            raise AErr(
                _("The domain '%s' does not exist.") % self._addr.domainname,
                NO_SUCH_DOMAIN,
            )
        self._uid = 0
        self._mail = None
        self._qlimit = None
        self._services = None
        self._transport = None
        self._note = None
        self._passwd = None
        self._new = True
        self._load()

    def __bool__(self):
        """Returns `True` if the Account is known, `False` if it's new."""
        return not self._new

    def _load(self):
        """Load 'uid', 'mid', 'qid', 'ssid', 'tid' and 'note' from the
        database and set _new to `False` - if the user could be found. """
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT uid, mid, qid, ssid, tid, note "
            "FROM users "
            "WHERE gid = %s AND local_part = %s",
            (self._domain.gid, self._addr.localpart),
        )
        # fmt: on
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._uid, _mid, _qid, _ssid, _tid, _note = result

            def load_helper(ctor, own, field, dbresult):
                cur = None if own is None else getattr(own, field)
                if cur != dbresult:
                    kwargs = {field: dbresult}
                    if dbresult is None:
                        return dbresult
                    else:
                        return ctor(self._dbh, **kwargs)

            self._qlimit = load_helper(QuotaLimit, self._qlimit, "qid", _qid)
            self._services = load_helper(ServiceSet, self._services, "ssid", _ssid)
            self._transport = load_helper(Transport, self._transport, "tid", _tid)
            self._mail = MailLocation(self._dbh, mid=_mid)
            self._note = _note
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
        if maillocation.dovecot_version > cfg_dget("misc.dovecot_version"):
            raise AErr(
                _("The mailbox format '%(mbfmt)s' requires Dovecot " ">= v%(version)s.")
                % {
                    "mbfmt": maillocation.mbformat,
                    "version": version_str(maillocation.dovecot_version),
                },
                INVALID_MAIL_LOCATION,
            )
        transport = self._transport or self._domain.transport
        validate_transport(transport, maillocation)
        self._mail = maillocation
        self._set_uid()

    def _update_tables(self, column, value):
        """Update various columns in the users table.

        Arguments:

        `column` : basestring
          Name of the table column. Currently: qid, ssid and tid
        `value` : int
          The referenced key
        """
        if column not in ("qid", "ssid", "tid"):
            raise ValueError("Unknown column: %r" % column)
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            f"UPDATE users "
            f"SET {column} = %s "
            f"WHERE uid = %s",
            (value, self._uid)
        )
        # fmt: on
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def _count_aliases(self):
        """Count all alias addresses where the destination address is the
        address of the Account."""
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT COUNT(destination) "
            "FROM alias "
            "WHERE destination = %s",
            (str(self._addr),),
        )
        # fmt: on
        a_count = dbc.fetchone()[0]
        dbc.close()
        return a_count

    def _chk_state(self):
        """Raise an AccountError if the Account is new - not yet saved in the
        database."""
        if self._new:
            raise AErr(
                _("The account '%s' does not exist.") % self._addr, NO_SUCH_ACCOUNT
            )

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
            return "%s/%s" % (self._domain.directory, self._uid)
        return None

    @property
    def mail_location(self):
        """The Account's MailLocation."""
        return self._mail

    @property
    def note(self):
        """The Account's note."""
        return self._note

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
            raise AErr(
                _("The account '%s' already exists.") % self._addr, ACCOUNT_EXISTS
            )
        if not isinstance(password, str) or not password:
            raise AErr(
                _("Could not accept password: '%s'") % password,
                ACCOUNT_MISSING_PASSWORD,
            )
        self._passwd = password

    def set_note(self, note):
        """Set the account's (optional) note.

        Argument:

        `note` : basestring or None
          The note, or None to remove
        """
        assert note is None or isinstance(note, str)
        self._note = note

    def save(self):
        """Save the new Account in the database."""
        if not self._new:
            raise AErr(
                _("The account '%s' already exists.") % self._addr, ACCOUNT_EXISTS
            )
        if not self._passwd:
            raise AErr(
                _("No password set for account: '%s'") % self._addr,
                ACCOUNT_MISSING_PASSWORD,
            )
        self._prepare(
            MailLocation(
                self._dbh,
                mbfmt=cfg_dget("mailbox.format"),
                directory=cfg_dget("mailbox.root"),
            )
        )
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "INSERT INTO users ("
            "   local_part, "
            "   passwd, "
            "   uid, "
            "   gid, "
            "   mid, "
            "   qid, "
            "   ssid, "
            "   tid, "
            "   note"
            ") "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                self._addr.localpart,
                pwhash(self._passwd, user=self._addr),
                self._uid,
                self._domain.gid,
                self._mail.mid,
                self._qlimit.qid if self._qlimit else None,
                self._services.ssid if self._services else None,
                self._transport.tid if self._transport else None,
                self._note,
            ),
        )
        # fmt: on
        self._dbh.commit()
        dbc.close()
        self._new = False

    def modify(self, field, value):
        """Update the Account's *field* to the new *value*.

        Possible values for *field* are: 'name', 'note' and 'pwhash'.

        Arguments:

        `field` : str
          The attribute name: 'name', 'note' or 'pwhash'
        `value` : str
          The new value of the attribute.
        """
        if field not in ("name", "note", "pwhash"):
            raise AErr(_("Unknown field: '%s'") % field, INVALID_ARGUMENT)
        if field == "pwhash":
            field = "passwd"
        self._chk_state()
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            f"UPDATE users "
            f"SET {field} = %s "
            f"WHERE uid = %s",
            (value, self._uid)
        )
        # fmt: on
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def update_password(self, password, scheme=None):
        """Update the Account's password.

        The given *password* will be hashed using password.pwhash.
        When no *scheme* is specified, the configured scheme
        (misc.password_scheme) will be used.

        Arguments:

        `password' : str
          The Account's new plain text password
        `scheme' : str
          The password scheme used for password hashing; default None
        """
        self._chk_state()
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "UPDATE users "
            "SET passwd = %s "
            "WHERE uid = %s",
            (pwhash(password, scheme, self._addr), self.uid),
        )
        # fmt: on
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def update_quotalimit(self, quotalimit):
        """Update the user's quota limit.

        Arguments:

        `quotalimit` : vmm.quotalimit.QuotaLimit
          the new quota limit of the domain.
        """
        self._chk_state()
        if quotalimit == self._qlimit:
            return
        self._qlimit = quotalimit
        if quotalimit is not None:
            assert isinstance(quotalimit, QuotaLimit)
            quotalimit = quotalimit.qid
        self._update_tables("qid", quotalimit)

    def update_serviceset(self, serviceset):
        """Assign a different set of services to the Account.

        Argument:

        `serviceset` : vmm.serviceset.ServiceSet
          the new service set.
        """
        self._chk_state()
        if serviceset == self._services:
            return
        self._services = serviceset
        if serviceset is not None:
            assert isinstance(serviceset, ServiceSet)
            serviceset = serviceset.ssid
        self._update_tables("ssid", serviceset)

    def update_transport(self, transport):
        """Sets a new transport for the Account.

        Arguments:

        `transport` : vmm.transport.Transport
          the new transport
        """
        self._chk_state()
        if transport == self._transport:
            return
        self._transport = transport
        if transport is not None:
            assert isinstance(transport, Transport)
            validate_transport(transport, self._mail)
            transport = transport.tid
        self._update_tables("tid", transport)

    def _get_info_transport(self):
        if self._transport:
            return self._transport.transport
        return format_domain_default(self._domain.transport.transport)

    def _get_info_serviceset(self):
        if self._services:
            services = self._services.services

            def fmt(s):
                return s

        else:
            services = self._domain.serviceset.services
            fmt = format_domain_default

        ret = {}
        for service, state in services.items():
            # TP: A service (e.g. pop3 or imap) may be enabled/usable or
            # disabled/unusable for a user.
            ret[service] = fmt((_("disabled"), _("enabled"))[state])
        return ret

    def get_info(self):
        """Returns a dict with some information about the Account.

        The keys of the dict are: 'address', 'gid', 'home', 'imap'
        'mail_location', 'name', 'pop3', 'sieve', 'smtp', transport', 'uid',
        'uq_bytes', 'uq_messages', 'ql_bytes', 'ql_messages', and
        'ql_domaindefault'.
        """
        self._chk_state()
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT ("
            "   name, "
            "   CASE WHEN bytes IS NULL THEN 0 ELSE bytes END, "
            "   CASE WHEN messages IS NULL THEN 0 ELSE messages END "
            ") "
            "FROM users "
            "LEFT JOIN userquota USING (uid) "
            "WHERE users.uid = %s",
            (self._uid,),
        )
        # fmt: on
        info = dbc.fetchone()
        dbc.close()
        if info:
            info = dict(list(zip(("name", "uq_bytes", "uq_messages"), info)))
            info.update(self._get_info_serviceset())
            info["address"] = self._addr
            info["gid"] = self._domain.gid
            info["home"] = "%s/%s" % (self._domain.directory, self._uid)
            info["mail_location"] = self._mail.mail_location
            if self._qlimit:
                info["ql_bytes"] = self._qlimit.bytes
                info["ql_messages"] = self._qlimit.messages
                info["ql_domaindefault"] = False
            else:
                info["ql_bytes"] = self._domain.quotalimit.bytes
                info["ql_messages"] = self._domain.quotalimit.messages
                info["ql_domaindefault"] = True
            info["transport"] = self._get_info_transport()
            info["note"] = self._note
            info["uid"] = self._uid
            return info
        # nearly impossible‽
        raise AErr(
            _("Could not fetch information for account: '%s'") % self._addr,
            NO_SUCH_ACCOUNT,
        )

    def get_aliases(self):
        """Return a list with all alias e-mail addresses, whose destination
        is the address of the Account."""
        self._chk_state()
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT address ||'@'|| domainname "
            "FROM alias, domain_name "
            "WHERE ("
            "   destination = %s "
            "   AND domain_name.gid = alias.gid "
            "   AND domain_name.is_primary"
            ") "
            "ORDER BY address",
            (str(self._addr),),
        )
        # fmt: on
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
            raise TypeError("force must be a bool")
        self._chk_state()
        dbc = self._dbh.cursor()
        if force:
            # fmt: off
            dbc.execute(
                "DELETE FROM users "
                "WHERE uid = %s",
                (self._uid,)
            )
            # fmt: on
            # delete also all aliases where the destination address is the same
            # as for this account.
            # fmt: off
            dbc.execute(
                "DELETE FROM alias "
                "WHERE destination = %s",
                (str(self._addr),)
            )
            # fmt: on
            self._dbh.commit()
        else:  # check first for aliases
            a_count = self._count_aliases()
            if a_count > 0:
                dbc.close()
                raise AErr(
                    _(
                        "There are %(count)d aliases with the "
                        "destination address '%(address)s'."
                    )
                    % {"count": a_count, "address": self._addr},
                    ALIAS_PRESENT,
                )
            # fmt: off
            dbc.execute(
                "DELETE FROM users "
                "WHERE uid = %s",
                (self._uid,)
            )
            # fmt: on
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

    `uid` : int
      The Account unique ID.
    `dbh` : psycopg2._psycopg.connection
      a database connection for the database access.
    """
    try:
        uid = int(uid)
    except ValueError:
        raise AErr(_("UID must be an integer."), INVALID_ARGUMENT)
    if uid < 1:
        raise AErr(_("UID must be greater than 0."), INVALID_ARGUMENT)
    dbc = dbh.cursor()
    # fmt: off
    dbc.execute(
        "SELECT local_part||'@'|| domain_name.domainname AS address, "
        "   uid, users.gid, note "
        "FROM users "
        "LEFT JOIN domain_name ON (domain_name.gid = users.gid AND is_primary) "
        "WHERE uid = %s",
        (uid,),
    )
    # fmt: on
    info = dbc.fetchone()
    dbc.close()
    if not info:
        raise AErr(_("There is no account with the UID: '%d'") % uid, NO_SUCH_ACCOUNT)
    info = dict(list(zip(("address", "uid", "gid", "note"), info)))
    return info


del cfg_dget
