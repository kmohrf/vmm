# -*- coding: UTF-8 -*-
# Copyright (c) 2011 - 2012, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.quotalimit
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's QuotaLimit class to manage quota limits
    for domains and accounts.
"""

_ = lambda msg: msg


class QuotaLimit(object):
    """Class to handle quota limit specific data."""
    __slots__ = ('_dbh', '_qid', '_bytes', '_messages')
    _kwargs = ('qid', 'bytes', 'messages')

    def __init__(self, dbh, **kwargs):
        """Create a new QuotaLimit instance.

        Either the `qid` keyword or the `bytes` and `messages` keywords
        must be specified.

        Arguments:

        `dbh` : pyPgSQL.PgSQL.Connection || psycopg2._psycopg.connection
          A database connection for the database access.

        Keyword arguments:

        `qid` : int
          The id of a quota limit
        `bytes` : int
          The quota limit in bytes.
        `messages` : int
          The quota limit in number of messages
        """
        self._dbh = dbh
        self._qid = 0
        self._bytes = 0
        self._messages = 0

        for key in kwargs.keys():
            if key not in self.__class__._kwargs:
                raise ValueError('unrecognized keyword: %r' % key)
        qid = kwargs.get('qid')
        if qid is not None:
            assert isinstance(qid, int)
            self._load_by_qid(qid)
        else:
            bytes_, msgs = kwargs.get('bytes'), kwargs.get('messages')
            assert all(isinstance(i, int) for i in (bytes_, msgs))
            self._bytes = -bytes_ if bytes_ < 0 else bytes_
            self._messages = -msgs if msgs < 0 else msgs
            self._load_by_limit()

    @property
    def bytes(self):
        """Quota limit in bytes."""
        return self._bytes

    @property
    def messages(self):
        """Quota limit in number of messages."""
        return self._messages

    @property
    def qid(self):
        """The quota limit's unique ID."""
        return self._qid

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._qid == other._qid
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._qid != other._qid
        return NotImplemented

    def _load_by_limit(self):
        """Load the quota limit by limit values from the database."""
        dbc = self._dbh.cursor()
        dbc.execute('SELECT qid FROM quotalimit WHERE bytes = %s AND '
                    'messages = %s', (self._bytes, self._messages))
        res = dbc.fetchone()
        dbc.close()
        if res:
            self._qid = res[0]
        else:
            self._save()

    def _load_by_qid(self, qid):
        """Load the quota limit by its unique ID from the database."""
        dbc = self._dbh.cursor()
        dbc.execute('SELECT bytes, messages FROM quotalimit WHERE qid = %s',
                    (qid,))
        res = dbc.fetchone()
        dbc.close()
        if not res:
            raise ValueError('Unknown quota limit id specified: %r' % qid)
        self._qid = qid
        self._bytes, self._messages = res

    def _save(self):
        """Store a new quota limit in the database."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('quotalimit_id')")
        self._qid = dbc.fetchone()[0]
        dbc.execute('INSERT INTO quotalimit (qid, bytes, messages) VALUES '
                    '(%s, %s, %s)', (self._qid, self._bytes, self._messages))
        self._dbh.commit()
        dbc.close()

del _
