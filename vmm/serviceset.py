# coding: utf-8
# Copyright (c) 2011 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.serviceset
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's ServiceSet class for simplified database access
    to the service_set table.
"""

SERVICES = ("smtp", "pop3", "imap", "sieve")


class ServiceSet(object):
    """A wrapper class that provides access to the service_set table.

    Each ServiceSet object provides following - read only - attributes:

    `ssid` : int
      The id of the service set
    `smtp` : bool
      Boolean flag for service smtp
    `pop3` : bool
      Boolean flag for service pop3
    `imap` : bool
      Boolean flag for service imap
    `sieve` : bool
      Boolean flag for service sieve
    `services` : dict
      The four services above with boolean values
    """

    __slots__ = ("_ssid", "_services", "_dbh")
    _kwargs = ("ssid",) + SERVICES

    def __init__(self, dbh, **kwargs):
        """Creates a new ServiceSet instance.

        Either the 'ssid' keyword argument or one or more of the service
        arguments ('smtp', 'pop3',  'imap', 'sieve') must be provided.

        Arguments:
        `dbh` : psycopg2.extensions.connection
          A database connection for the database access.

        Keyword arguments:
        `ssid` : int
          The id of the service set (>0)
        `smtp` : bool
          Boolean flag for service smtp - default `True`
        `pop3` : bool
          Boolean flag for service pop3 - default `True`
        `imap` : bool
          Boolean flag for service imap - default `True`
        `sieve` : bool
          Boolean flag for service sieve - default `True`
        """
        self._dbh = dbh
        self._ssid = 0
        self._services = dict.fromkeys(SERVICES, True)

        for key in kwargs.keys():
            if key not in self.__class__._kwargs:
                raise ValueError("unrecognized keyword: %r" % key)
            if key == "ssid":
                assert (
                    not isinstance(kwargs[key], bool)
                    and isinstance(kwargs[key], int)
                    and kwargs[key] > 0
                )
                self._load_by_ssid(kwargs[key])
                break
            else:
                assert isinstance(kwargs[key], bool)
                if not kwargs[key]:
                    self._services[key] = kwargs[key]
        if not self._ssid:
            self._load_by_services()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._ssid == other._ssid
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._ssid != other._ssid
        return NotImplemented

    def __getattr__(self, name):
        if name not in self.__class__._kwargs:
            raise AttributeError(
                "%r object has no attribute %r" % (self.__class__.__name__, name)
            )
        if name == "ssid":
            return self._ssid
        else:
            return self._services[name]

    def __repr__(self):
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            self._dbh,
            ", ".join("%s=%r" % s for s in self._services.items()),
        )

    def _load_by_services(self):
        """Try to load the service_set by it's service combination."""
        dbc = self._dbh.cursor()
        # TODO PY3PORT: possible SQL injection?
        service_queries = " AND ".join(
            f"{k} = {str(v).upper()}" for k, v in self._services.items()
        )
        # fmt: off
        dbc.execute(
            f"SELECT ssid "
            f"FROM service_set "
            f"WHERE {service_queries}"
        )
        # fmt: on
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._ssid = result[0]
        else:
            self._save()

    def _load_by_ssid(self, ssid):
        """Try to load the service_set by it's primary key."""
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT ssid, smtp, pop3, imap, sieve "
            "FROM service_set "
            "WHERE ssid = %s",
            (ssid,),
        )
        # fmt: on
        result = dbc.fetchone()
        dbc.close()
        if not result:
            raise ValueError("Unknown service_set id specified: %r" % ssid)
        self._ssid = result[0]
        self._services.update(list(zip(SERVICES, result[1:])))

    def _save(self):
        """Store a new service_set in the database."""
        # fmt: off
        sql = (
            "INSERT INTO service_set (ssid, smtp, pop3, imap, sieve) "
            "VALUES (%(ssid)s, %(smtp)s, %(pop3)s, %(imap)s, %(sieve)s)"
        )
        # fmt: on
        self._set_ssid()
        values = {"ssid": self._ssid}
        values.update(self._services)
        dbc = self._dbh.cursor()
        dbc.execute(sql, values)
        self._dbh.commit()
        dbc.close()

    def _set_ssid(self):
        """Set the unique ID for the new service_set."""
        assert self._ssid == 0
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('service_set_id')")
        self._ssid = dbc.fetchone()[0]
        dbc.close()

    @property
    def services(self):
        """A dictionary: Keys: `smtp`, `pop3`, `imap` and `sieve` with
        boolean values."""
        return self._services.copy()
