# -*- coding: UTF-8 -*-
# Copyright (c) 2012 - 2014, martin f. krafft
# See COPYING for distribution information.
"""
    vmm.catchall
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's CatchallAlias class to manage domain catch-all
    aliases.

    This is heavily based on (more or less a copy of) the Alias class, because
    fundamentally, catchall aliases are aliases, but without a localpart.
    While Alias could potentially derive from CatchallAlias to reuse some of
    the functionality, it's probably not worth it. I found no sensible way to
    derive CatchallAlias from Alias, or at least none that would harness the
    powers of polymorphism.

    Yet, we reuse the AliasError exception class, which makes sense.
"""

from gettext import gettext as _

from vmm.domain import get_gid
from vmm.emailaddress import EmailAddress, DestinationEmailAddress as DestAddr
from vmm.errors import AliasError as AErr
from vmm.ext.postconf import Postconf
from vmm.constants import ALIAS_EXCEEDS_EXPANSION_LIMIT, NO_SUCH_ALIAS, NO_SUCH_DOMAIN


cfg_dget = lambda option: None


class CatchallAlias(object):
    """Class to manage domain catch-all aliases."""

    __slots__ = ("_domain", "_dests", "_gid", "_dbh")

    def __init__(self, dbh, domain):
        self._domain = domain
        self._dbh = dbh
        self._gid = get_gid(self._dbh, self.domain)
        if not self._gid:
            raise AErr(
                _("The domain '%s' does not exist.") % self.domain, NO_SUCH_DOMAIN
            )
        self._dests = []

        self._load_dests()

    def _load_dests(self):
        """Loads all known destination addresses into the _dests list."""
        dbc = self._dbh.cursor()
        # fmt: off
        dbc.execute(
            "SELECT destination "
            "FROM catchall "
            "WHERE gid = %s",
            (self._gid,)
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
                """Cannot add %(count_new)i new destination(s) to catch-all alias for
domain '%(domain)s'. Currently this alias expands into %(count)i/%(limit)i
recipients. %(count_new)i additional destination(s) will render this alias
unusable.
Hint: Increase Postfix' virtual_alias_expansion_limit"""
            )
        elif dcount > limit:
            failed = True
            errmsg = _(
                """Cannot add %(count_new)i new destination(s) to catch-all alias for domain
'%(domain)s'. This alias already exceeds its expansion limit \
(%(count)i/%(limit)i).
So its unusable, all messages addressed to this alias will be bounced.
Hint: Delete some destination addresses."""
            )
        if failed:
            raise AErr(
                errmsg
                % {
                    "domain": self._domain,
                    "count": dcount,
                    "limit": limit,
                    "count_new": count_new,
                },
                ALIAS_EXCEEDS_EXPANSION_LIMIT,
            )

    def _delete(self, destinations=None):
        """Delete one ore multiple destinations from the catchall alias, if
        ``destinations`` is not ``None``.  If ``destinations`` is None, the
        catchall alias with all its destination addresses will be deleted.

        """
        dbc = self._dbh.cursor()
        if not destinations:
            # fmt: off
            dbc.execute(
                "DELETE FROM catchall "
                "WHERE gid = %s",
                (self._gid,)
            )
            # fmt: on
        else:
            # fmt: off
            dbc.executemany(
                "DELETE FROM catchall "
                "WHERE gid = %s AND destination = %s",
                ((self._gid, str(dest)) for dest in destinations),
            )
            # fmt: on
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()

    def __len__(self):
        """Returns the number of destinations of the catchall alias."""
        return len(self._dests)

    @property
    def domain(self):
        """The Alias' domain."""
        return self._domain

    def add_destinations(self, destinations, warnings=None):
        """Adds the `EmailAddress`es from *destinations* list to the
        destinations of the catchall alias.

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
            "INSERT INTO catchall (gid, destination) "
            "VALUES (%s, %s)",
            ((self._gid, str(destination)) for destination in destinations),
        )
        # fmt: on
        self._dbh.commit()
        dbc.close()
        self._dests.extend(destinations)
        return destinations

    def del_destinations(self, destinations, warnings=None):
        """Deletes the specified ``destinations`` from the catchall alias."""
        destinations = set(destinations)
        assert destinations and all(
            isinstance(dest, EmailAddress) for dest in destinations
        )
        if warnings is not None:
            assert isinstance(warnings, list)
        if not self._dests:
            raise AErr(
                _("There are no catch-all aliases defined for " "domain '%s'.")
                % self._domain,
                NO_SUCH_ALIAS,
            )
        unknown = destinations.difference(set(self._dests))
        if unknown:
            destinations.intersection_update(set(self._dests))
            if warnings is not None:
                warnings.extend(unknown)
        if not destinations:
            raise AErr(
                _(
                    "No suitable destinations left to remove from the "
                    "catch-all alias of domain '%s'."
                )
                % self._domain,
                NO_SUCH_ALIAS,
            )
        self._delete(destinations)
        for destination in destinations:
            self._dests.remove(destination)

    def get_destinations(self):
        """Returns an iterator for all destinations of the catchall alias."""
        if not self._dests:
            raise AErr(
                _("There are no catch-all aliases defined for " "domain '%s'.")
                % self._domain,
                NO_SUCH_ALIAS,
            )
        return iter(self._dests)

    def delete(self):
        """Deletes all catchall destinations for the domain."""
        if not self._dests:
            raise AErr(
                _("There are no catch-all aliases defined for " "domain '%s'.")
                % self._domain,
                NO_SUCH_ALIAS,
            )
        self._delete()
        del self._dests[:]


del cfg_dget
