# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.alias
    ~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's Alias class to manage e-mail aliases.
"""

from gettext import gettext as _

from vmm.domain import get_gid
from vmm.emailaddress import EmailAddress, DestinationEmailAddress as DestAddr
from vmm.errors import AliasError as AErr
from vmm.ext.postconf import Postconf
from vmm.constants import ALIAS_EXCEEDS_EXPANSION_LIMIT, NO_SUCH_ALIAS, NO_SUCH_DOMAIN


cfg_dget = lambda option: None


class Alias:
    """Class to manage e-mail aliases."""

    __slots__ = ("_addr", "_dests", "_gid", "_dbh")

    def __init__(self, dbh, address):
        assert isinstance(address, EmailAddress)
        self._addr = address
        self._dbh = dbh
        self._gid = get_gid(self._dbh, self._addr.domainname)
        if not self._gid:
            raise AErr(
                _("The domain '%s' does not exist.") % self._addr.domainname,
                NO_SUCH_DOMAIN,
            )
        self._dests = []

        self._load_dests()

    def _load_dests(self):
        """Loads all known destination addresses into the _dests list."""
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT destination "
            "FROM alias "
            "WHERE gid = %s AND address = %s "
            "ORDER BY destination",
            (self._gid, self._addr.localpart),
        )
        # fmt: on
        dests = dbc.fetchall()
        if dbc.rowcount > 0:
            self._dests.extend(DestAddr(dest[0], self._dbh) for dest in dests)
        dbc.close()

    def _check_expansion(self, count_new):
        """Checks the current expansion limit of the alias."""
        postconf = Postconf(cfg_dget("bin.postconf"))
        limit = int(postconf.read("virtual_alias_expansion_limit"))
        dcount = len(self._dests)
        failed = False
        if dcount == limit or dcount + count_new > limit:
            failed = True
            errmsg = _(
                """Cannot add %(count_new)i new destination(s) to alias '%(address)s'.
Currently this alias expands into %(count)i/%(limit)i recipients.
%(count_new)i additional destination(s) will render this alias unusable.
Hint: Increase Postfix' virtual_alias_expansion_limit"""
            )
        elif dcount > limit:
            failed = True
            errmsg = _(
                """Cannot add %(count_new)i new destination(s) to alias '%(address)s'.
This alias already exceeds its expansion limit (%(count)i/%(limit)i).
So its unusable, all messages addressed to this alias will be bounced.
Hint: Delete some destination addresses."""
            )
        if failed:
            raise AErr(
                errmsg
                % {
                    "address": self._addr,
                    "count": dcount,
                    "limit": limit,
                    "count_new": count_new,
                },
                ALIAS_EXCEEDS_EXPANSION_LIMIT,
            )

    def _delete(self, destinations=None):
        """Deletes the *destinations* from the alias, if ``destinations``
        is not ``None``.  If ``destinations`` is None, the alias with all
        its destination addresses will be deleted.

        """
        dbc = self._dbh.cursor()
        if not destinations:
            # fmt: off
            dbc.execute(
                "DELETE FROM alias "
                "WHERE gid = %s AND address = %s",
                (self._gid, self._addr.localpart),
            )
            # fmt: on
        else:
            # fmt: off
            dbc.executemany(
                "DELETE FROM alias "
                "WHERE gid = %s AND address = %s AND destination = %s",
                ((self._gid, self._addr.localpart, str(dest)) for dest in destinations),
            )
            # fmt: on
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def __len__(self):
        """Returns the number of destinations of the alias."""
        return len(self._dests)

    @property
    def address(self):
        """The Alias' EmailAddress instance."""
        return self._addr

    def add_destinations(self, destinations, warnings=None):
        """Adds the `EmailAddress`es from *destinations* list to the
        destinations of the alias.

        Destinations, that are already assigned to the alias, will be
        removed from *destinations*.  When done, this method will return
        a set with all destinations, that were saved in the database.
        """
        destinations = set(destinations)
        assert destinations and all(
            isinstance(dest, EmailAddress) for dest in destinations
        )
        if warnings is not None:
            assert isinstance(warnings, list)
        if self._addr in destinations:
            destinations.remove(self._addr)
            if warnings is not None:
                warnings.append(self._addr)
        duplicates = destinations.intersection(set(self._dests))
        if duplicates:
            destinations.difference_update(set(self._dests))
            if warnings is not None:
                warnings.extend(duplicates)
        if not destinations:
            return destinations
        self._check_expansion(len(destinations))
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.executemany(
            "INSERT INTO alias (gid, address, destination) "
            "VALUES (%s, %s, %s)",
            (
                (self._gid, self._addr.localpart, str(destination))
                for destination in destinations
            ),
        )
        # fmt: on
        self._dbh.commit()
        dbc.close()
        self._dests.extend(destinations)
        return destinations

    def del_destinations(self, destinations, warnings=None):
        """Delete the specified `EmailAddress`es of *destinations* from
        the alias's destinations.

        """
        destinations = set(destinations)
        assert destinations and all(
            isinstance(dest, EmailAddress) for dest in destinations
        )
        if warnings is not None:
            assert isinstance(warnings, list)
        if self._addr in destinations:
            destinations.remove(self._addr)
            if warnings is not None:
                warnings.append(self._addr)
        if not self._dests:
            raise AErr(_("The alias '%s' does not exist.") % self._addr, NO_SUCH_ALIAS)
        unknown = destinations.difference(set(self._dests))
        if unknown:
            destinations.intersection_update(set(self._dests))
            if warnings is not None:
                warnings.extend(unknown)
        if not destinations:
            raise AErr(
                _("No suitable destinations left to remove from alias " "'%s'.")
                % self._addr,
                NO_SUCH_ALIAS,
            )
        self._delete(destinations)
        for destination in destinations:
            self._dests.remove(destination)

    def get_destinations(self):
        """Returns an iterator for all destinations of the alias."""
        if not self._dests:
            raise AErr(_("The alias '%s' does not exist.") % self._addr, NO_SUCH_ALIAS)
        return iter(self._dests)

    def delete(self):
        """Deletes the alias with all its destinations."""
        if not self._dests:
            raise AErr(_("The alias '%s' does not exist.") % self._addr, NO_SUCH_ALIAS)
        self._delete()
        del self._dests[:]


del cfg_dget
