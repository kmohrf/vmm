# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.Alias

    Virtual Mail Manager's Alias class to manage e-mail aliases.
"""

from VirtualMailManager.Domain import get_gid
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.Exceptions import VMMAliasException as VMMAE
from VirtualMailManager.constants.ERROR import ALIAS_ADDR_DEST_IDENTICAL, \
     ALIAS_EXCEEDS_EXPANSION_LIMIT, ALIAS_EXISTS, NO_SUCH_ALIAS


_ = lambda msg: msg


class Alias(object):
    """Class to manage e-mail aliases."""
    __slots__ = ('_addr', '_dests', '_gid', '_dbh')

    def __init__(self, dbh, address):
        assert isinstance(address, EmailAddress)
        self._addr = address
        self._dbh = dbh
        self._gid = get_gid(self._dbh, self._addr.domainname)
        self._dests = []

        self.__load_dests()

    def __load_dests(self):
        """Loads all known destination addresses into the _dests list."""
        dbc = self._dbh.cursor()
        dbc.execute(
                'SELECT destination FROM alias WHERE gid=%s AND address=%s',
                    self._gid, self._addr.localpart)
        dests = iter(dbc.fetchall())
        if dbc.rowcount > 0:
            dest_add = self._dests.append
            for dest in dests:
                dest_add(EmailAddress(dest[0]))
        dbc.close()

    def __check_expansion(self, limit):
        """Checks the current expansion limit of the alias."""
        dcount = len(self._dests)
        failed = False
        if dcount == limit:
            failed = True
            errmsg = _(
u"""Can't add new destination to alias %(address)r.
Currently this alias expands into %(count)i/%(limit)i recipients.
One more destination will render this alias unusable.
Hint: Increase Postfix' virtual_alias_expansion_limit""")
        elif dcount > limit:
            failed = True
            errmsg = _(
u"""Can't add new destination to alias %(address)r.
This alias already exceeds it's expansion limit (%(count)i/%(limit)i).
So its unusable, all messages addressed to this alias will be bounced.
Hint: Delete some destination addresses.""")
        if failed:
            raise VMMAE(errmsg % {'address': str(self._addr), 'count': dcount,
                                  'limit': limit},
                        ALIAS_EXCEEDS_EXPANSION_LIMIT)

    def __delete(self, destination=None):
        """Deletes a destination from the alias, if ``destination`` is not
        ``None``. If ``destination`` is None, the alias with all it's
        destination addresses will be deleted."""
        dbc = self._dbh.cursor()
        if not destination:
            dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s",
                        self._gid, self._addr.localpart)
        else:
            dbc.execute("DELETE FROM alias WHERE gid=%s AND address=%s AND \
 destination=%s",
                        self._gid, self._addr.localpart, str(destination))
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def __len__(self):
        """Returns the number of destinations of the alias."""
        return len(self._dests)

    def addDestination(self, destination, expansion_limit):
        """Adds the ``destination`` `EmailAddress` to the alias."""
        assert isinstance(destination, EmailAddress)
        if self._addr == destination:
            raise VMMAE(_(u"Address and destination are identical."),
                        ALIAS_ADDR_DEST_IDENTICAL)
        if destination in self._dests:
            raise VMMAE(_(
                u'The alias %(a)r has already the destination %(d)r.') %
                        {'a': str(self._addr), 'd': str(destination)},
                        ALIAS_EXISTS)
        self.__check_expansion(expansion_limit)
        dbc = self._dbh.cursor()
        dbc.execute('INSERT INTO alias (gid, address, destination) \
VALUES (%s, %s, %s)',
                    self._gid, self._addr.localpart, str(destination))
        self._dbh.commit()
        dbc.close()
        self._dests.append(destination)

    def delDestination(self, destination):
        """Deletes the specified ``destination`` address from the alias."""
        assert isinstance(destination, EmailAddress)
        if not self._dests:
            raise VMMAE(_(u"The alias %r doesn't exist.") % str(self._addr),
                        NO_SUCH_ALIAS)
        if not destination in self._dests:
            raise VMMAE(_(u"The address %(d)r isn't a destination of \
the alias %(a)r.") %
                        {'a': str(self._addr), 'd': str(destination)},
                        NO_SUCH_ALIAS)
        self.__delete(destination)
        self._dests.remove(destination)

    def getDestinations(self):
        """Returns an iterator for all destinations of the alias."""
        if not self._dests:
            raise VMMAE(_(u"The alias %r doesn't exist.") % str(self._addr),
                        NO_SUCH_ALIAS)
        return iter(self._dests)

    def delete(self):
        """Deletes the alias with all it's destinations."""
        if not self._dests:
            raise VMMAE(_(u"The alias %r doesn't exist.") % str(self._addr),
                        NO_SUCH_ALIAS)
        self.__delete()
        del self._dests[:]


del _
