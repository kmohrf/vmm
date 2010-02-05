# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Virtual Mail Manager's Transport class to manage the transport for
domains and accounts."""

import VirtualMailManager.constants.ERROR as ERR
from VirtualMailManager.Exceptions import VMMTransportException

class Transport(object):
    """A wrapper class that provides access to the transport table"""
    __slots__ = ('__id', '__transport', '_dbh')
    def __init__(self, dbh, tid=None, transport=None):
        """Creates a new Transport instance.

        Either tid or transport must be specified.

        Keyword arguments:
        dbh -- a pyPgSQL.PgSQL.connection
        tid -- the id of a transport (long)
        transport -- the value of the transport (str)
        """
        self._dbh = dbh
        if tid is None and transport is None:
            raise VMMTransportException(
                _('Either tid or transport must be specified.'),
                ERR.TRANSPORT_INIT)
        elif tid is not None:
            try:
                self.__id = long(tid)
            except ValueError:
                raise VMMTransportException(_('tid must be an int/long.'),
                    ERR.TRANSPORT_INIT)
            self._loadByID()
        else:
            self.__transport = transport
            self._loadByName()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__id == other.getID()
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.__id != other.getID()
        return NotImplemented

    def __str__(self):
        return self.__transport

    def _loadByID(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT transport FROM transport WHERE tid = %s', self.__id)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self.__transport = result[0]
        else:
            raise VMMTransportException(_('Unknown tid specified.'),
                ERR.UNKNOWN_TRANSPORT_ID)

    def _loadByName(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT tid FROM transport WHERE transport = %s',
                self.__transport)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self.__id = result[0]
        else:
            self._save()

    def _save(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('transport_id')")
        self.__id = dbc.fetchone()[0]
        dbc.execute('INSERT INTO transport (tid, transport) VALUES (%s, %s)',
                self.__id, self.__transport)
        self._dbh.commit()
        dbc.close()

    def getID(self):
        """Returns the unique ID of the transport."""
        return self.__id

    def getTransport(self):
        """Returns the value of transport, ex: 'dovecot:'"""
        return self.__transport
