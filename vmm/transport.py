# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.transport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's Transport class to manage the transport for
    domains and accounts.
"""


class Transport:
    """A wrapper class that provides access to the transport table"""

    __slots__ = ("_tid", "_transport", "_dbh")

    def __init__(self, dbh, tid=None, transport=None):
        """Creates a new Transport instance.

        Either tid or transport must be specified. When both arguments
        are given, tid will be used.

        Keyword arguments:
        dbh -- a psycopg2._psycopg.connection
        tid -- the id of a transport (int)
        transport -- the value of the transport (str)

        """
        self._dbh = dbh
        self._tid = 0
        assert any((tid, transport))
        if tid:
            assert not isinstance(tid, bool) and isinstance(tid, int)
            self._load_by_id(tid)
        else:
            assert isinstance(transport, str)
            self._transport = transport
            self._load_by_name()

    @property
    def tid(self):
        """The transport's unique ID."""
        return self._tid

    @property
    def transport(self):
        """The transport's value, ex: 'dovecot:'"""
        return self._transport

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._tid == other._tid
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._tid != other._tid
        return NotImplemented

    def __str__(self):
        return self._transport

    def _load_by_id(self, tid):
        """load a transport by its id from the database"""
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT transport "
            "FROM transport "
            "WHERE tid = %s",
            (tid,)
        )
        # fmt: on
        result = dbc.fetchone()
        dbc.close()
        if not result:
            raise ValueError("Unknown transport id specified: %r" % tid)
        self._transport = result[0]
        self._tid = tid

    def _load_by_name(self):
        """Load a transport by its transport name from the database."""
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT tid "
            "FROM transport "
            "WHERE transport = %s",
            (self._transport,)
        )
        # fmt: on
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._tid = result[0]
        else:
            self._save()

    def _save(self):
        """Save the new transport in the database."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('transport_id')")
        self._tid = dbc.fetchone()[0]
        # fmt: off
        dbc.execute(
            "INSERT INTO transport (tid, transport) "
            "VALUES (%s, %s)",
            (self._tid, self._transport),
        )
        # fmt: on
        self._dbh.commit()
        dbc.close()
