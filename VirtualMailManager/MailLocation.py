# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Virtual Mail Manager's MailLocation class to manage the mail_location
for accounts."""

import re

import VirtualMailManager.constants.ERROR as ERR
from VirtualMailManager.Exceptions import VMMMailLocationException as MLE

RE_MAILLOCATION = """^\w{1,20}$"""

class MailLocation(object):
    """A wrapper class thats provide access to the maillocation table"""
    __slots__ = ('__id', '__maillocation', '_dbh')
    def __init__(self, dbh, mid=None, maillocation=None):
        """Creates a new MailLocation instance.

        Either mid or maillocation must be specified.

        Keyword arguments:
        dbh -- a pyPgSQL.PgSQL.connection
        mid -- the id of a maillocation (long)
        maillocation -- the value of the maillocation (str)
        """
        self._dbh = dbh
        if mid is None and maillocation is None:
            raise MLE(_('Either mid or maillocation must be specified.'),
                ERR.MAILLOCATION_INIT)
        elif mid is not None:
            try:
                self.__id = long(mid)
            except ValueError:
                raise MLE(_('mid must be an int/long.'), ERR.MAILLOCATION_INIT)
            self._loadByID()
        else:
            if re.match(RE_MAILLOCATION, maillocation):
                self.__maillocation = maillocation
                self._loadByName()
            else:
                raise MLE(
                    _(u'Invalid folder name “%s”, it may consist only of\n\
1 - 20 single byte characters (A-Z, a-z, 0-9 and _).') % maillocation,
                        ERR.MAILLOCATION_INIT)

    def _loadByID(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT maillocation FROM maillocation WHERE mid = %s',
                self.__id)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self.__maillocation = result[0]
        else:
            raise MLE(_('Unknown mid specified.'), ERR.UNKNOWN_MAILLOCATION_ID)

    def _loadByName(self):
        dbc = self._dbh.cursor()
        dbc.execute('SELECT mid FROM maillocation WHERE maillocation = %s',
                self.__maillocation)
        result = dbc.fetchone()
        dbc.close()
        if result is not None:
            self.__id = result[0]
        else:
            self._save()

    def _save(self):
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('maillocation_id')")
        self.__id = dbc.fetchone()[0]
        dbc.execute('INSERT INTO maillocation(mid,maillocation) VALUES(%s,%s)',
                self.__id, self.__maillocation)
        self._dbh.commit()
        dbc.close()

    def getID(self):
        """Returns the unique ID of the maillocation."""
        return self.__id

    def getMailLocation(self):
        """Returns the value of maillocation, ex: 'Maildir'"""
        return self.__maillocation

