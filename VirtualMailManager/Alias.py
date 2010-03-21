# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.Alias

    Virtual Mail Manager's Alias class to manage e-mail aliases.
"""

from VirtualMailManager.Domain import get_gid
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.errors import AliasError as AErr
from VirtualMailManager.pycompat import all
from VirtualMailManager.constants.ERROR import \
     ALIAS_EXCEEDS_EXPANSION_LIMIT, NO_SUCH_ALIAS, NO_SUCH_DOMAIN


_ = lambda msg: msg


class Alias(object):
    """Class to manage e-mail aliases."""
    __slots__ = ('_addr', '_dests', '_gid', '_dbh')

    def __init__(self, dbh, address):
        assert isinstance(address, EmailAddress)
        self._addr = address
        self._dbh = dbh
        self._gid = get_gid(self._dbh, self._addr.domainname)
        if not self._gid:
            raise AErr(_(u"The domain %r doesn't exist.") %
                       self._addr.domainname, NO_SUCH_DOMAIN)
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
            self._dests.extend(EmailAddress(dest[0]) for dest in dests)
        dbc.close()

    def __check_expansion(self, count_new, limit):
        """Checks the current expansion limit of the alias."""
        dcount = len(self._dests)
        failed = False
        if dcount == limit or dcount + count_new > limit:
            failed = True
            errmsg = _(
u"""Can't add %(count_new)i new destination(s) to alias %(address)r.
Currently this alias expands into %(count)i/%(limit)i recipients.
%(count_new)i additional destination(s) will render this alias unusable.
Hint: Increase Postfix' virtual_alias_expansion_limit""")
        elif dcount > limit:
            failed = True
            errmsg = _(
u"""Can't add %(count_new)i new destination(s) to alias %(address)r.
This alias already exceeds it's expansion limit (%(count)i/%(limit)i).
So its unusable, all messages addressed to this alias will be bounced.
Hint: Delete some destination addresses.""")
        if failed:
            raise AErr(errmsg % {'address': str(self._addr), 'count': dcount,
                                 'limit': limit, 'count_new': count_new},
                       ALIAS_EXCEEDS_EXPANSION_LIMIT)

    def __delete(self, destination=None):
        """Deletes a destination from the alias, if ``destination`` is
        not ``None``.  If ``destination`` is None, the alias with all
        it's destination addresses will be deleted.

        """
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

    def add_destinations(self, destinations, expansion_limit, warnings=None):
        """Adds the `EmailAddress`es from *destinations* list to the
        destinations of the alias.

        Destinations, that are already assigned to the alias, will be
        removed from *destinations*.  When done, this method will return
        a set with all destinations, that was saved in the database.
        """
        destinations = set(destinations)
        assert destinations and \
                all(isinstance(dest, EmailAddress) for dest in destinations)
        if not warnings is None:
            assert isinstance(warnings, list)
        if self._addr in destinations:
            destinations.remove(self._addr)
            if not warnings is None:
                warnings.append(self._addr)
        duplicates = destinations.intersection(set(self._dests))
        if duplicates:
            destinations.difference_update(set(self._dests))
            if not warnings is None:
                warnings.extend(duplicates)
        if not destinations:
            return destinations
        self.__check_expansion(len(destinations), expansion_limit)
        dbc = self._dbh.cursor()
        dbc.executemany("INSERT INTO alias VALUES (%d, '%s', %%s)" %
                        (self._gid, self._addr.localpart),
                        (str(destination) for destination in destinations))
        self._dbh.commit()
        dbc.close()
        self._dests.extend(destinations)
        return destinations

    def del_destination(self, destination):
        """Deletes the specified ``destination`` address from the alias."""
        assert isinstance(destination, EmailAddress)
        if not self._dests:
            raise AErr(_(u"The alias %r doesn't exist.") % str(self._addr),
                       NO_SUCH_ALIAS)
        if not destination in self._dests:
            raise AErr(_(u"The address %(d)r isn't a destination of \
the alias %(a)r.") %
                       {'a': str(self._addr), 'd': str(destination)},
                       NO_SUCH_ALIAS)
        self.__delete(destination)
        self._dests.remove(destination)

    def get_destinations(self):
        """Returns an iterator for all destinations of the alias."""
        if not self._dests:
            raise AErr(_(u"The alias %r doesn't exist.") % str(self._addr),
                       NO_SUCH_ALIAS)
        return iter(self._dests)

    def delete(self):
        """Deletes the alias with all its destinations."""
        if not self._dests:
            raise AErr(_(u"The alias %r doesn't exist.") % str(self._addr),
                       NO_SUCH_ALIAS)
        self.__delete()
        del self._dests[:]


del _
