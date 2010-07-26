# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.Transport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's Transport class to manage the transport for
    domains and accounts.
"""

from VirtualMailManager.constants import UNKNOWN_TRANSPORT_ID
from VirtualMailManager.errors import TransportError
from VirtualMailManager.pycompat import any


class Transport(object):
    """A wrapper class that provides access to the transport table"""
    __slots__ = ('_tid', '_transport', '_dbh')

    def __init__(self, dbh, tid=None, transport=None):
        """Creates a new Transport instance.

        Either tid or transport must be specified. When both arguments
        are given, tid will be used.

        Keyword arguments:
        dbh -- a pyPgSQL.PgSQL.connection
        tid -- the id of a transport (int/long)
        transport -- the value of the transport (str)

        """
        self._dbh = dbh
        assert any((tid, transport))
        if tid:
            assert not isinstance(tid, bool) and isinstance(tid, (int, long))
            self._tid = tid
            self._loadByID()
        else:
            assert isinstance(transport, basestring)
            self._transport = transport
            self._loadByName()

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
            return self._tid == other.tid
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._tid != other.tid
        return NotImplemented

    def __str__(self):
        return self._transport

    def _loadByID(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT transport FROM transport WHERE tid=%s', self._tid)
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._transport = result[0]
        else:
            raise TransportError(_(u'Unknown tid specified.'),
                                 UNKNOWN_TRANSPORT_ID)

    def _loadByName(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT tid FROM transport WHERE transport = %s',
                    self._transport)
        result = dbc.fetchone()
        dbc.close()
        if result:
            self._tid = result[0]
        else:
            self._save()

    def _save(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('transport_id')")
        self._tid = dbc.fetchone()[0]
        dbc.execute('INSERT INTO transport VALUES (%s, %s)', self._tid,
                    self._transport)
        self._dbh.commit()
        dbc.close()
