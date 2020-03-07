# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.aliasdomain
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's AliasDomain class to manage alias domains.
"""

from vmm.domain import Domain, check_domainname
from vmm.constants import (
    ALIASDOMAIN_EXISTS,
    ALIASDOMAIN_ISDOMAIN,
    ALIASDOMAIN_NO_DOMDEST,
    NO_SUCH_ALIASDOMAIN,
    NO_SUCH_DOMAIN,
)
from vmm.errors import AliasDomainError as ADErr


_ = lambda msg: msg


class AliasDomain(object):
    """Class to manage e-mail alias domains."""

    __slots__ = ("_gid", "_name", "_domain", "_dbh")

    def __init__(self, dbh, domainname):
        """Creates a new AliasDomain instance.

        Arguments:

        `dbh` : psycopg2._psycopg.connection
          a database connection for the database access
        `domainname` : basestring
          the name of the AliasDomain"""
        self._dbh = dbh
        self._name = check_domainname(domainname)
        self._gid = 0
        self._domain = None
        self._load()

    def _load(self):
        """Loads the AliasDomain's GID from the database and checks if the
        domain name is marked as primary."""
        dbc = self._dbh.cursor()
        dbc.execute(
            "SELECT gid, is_primary FROM domain_name WHERE " "domainname = %s",
            (self._name,),
        )
        result = dbc.fetchone()
        dbc.close()
        if result:
            if result[1]:
                raise ADErr(
                    _("The domain '%s' is a primary domain.") % self._name,
                    ALIASDOMAIN_ISDOMAIN,
                )
            self._gid = result[0]

    def set_destination(self, dest_domain):
        """Set the destination of a new AliasDomain or updates the
        destination of an existing AliasDomain.

        Argument:

        `dest_domain` : vmm.Domain.Domain
          the AliasDomain's destination domain
        """
        assert isinstance(dest_domain, Domain)
        self._domain = dest_domain

    def save(self):
        """Stores information about the new AliasDomain in the database."""
        if self._gid > 0:
            raise ADErr(
                _("The alias domain '%s' already exists.") % self._name,
                ALIASDOMAIN_EXISTS,
            )
        if not self._domain:
            raise ADErr(
                _("No destination domain set for the alias domain."),
                ALIASDOMAIN_NO_DOMDEST,
            )
        if self._domain.gid < 1:
            raise ADErr(
                _("The target domain '%s' does not exist.") % self._domain.name,
                NO_SUCH_DOMAIN,
            )
        dbc = self._dbh.cursor()
        dbc.execute(
            "INSERT INTO domain_name (domainname, gid, is_primary) "
            "VALUES (%s, %s, FALSE)",
            (self._name, self._domain.gid),
        )
        self._dbh.commit()
        dbc.close()
        self._gid = self._domain.gid

    def info(self):
        """Returns a dict (keys: "alias" and "domain") with the names of the
        AliasDomain and its primary domain."""
        if self._gid < 1:
            raise ADErr(
                _("The alias domain '%s' does not exist.") % self._name,
                NO_SUCH_ALIASDOMAIN,
            )
        dbc = self._dbh.cursor()
        dbc.execute(
            "SELECT domainname FROM domain_name WHERE gid = %s AND " "is_primary",
            (self._gid,),
        )
        domain = dbc.fetchone()
        dbc.close()
        if domain:
            return {"alias": self._name, "domain": domain[0]}
        else:  # an almost unlikely case, isn't it?
            raise ADErr(
                _("There is no primary domain for the alias domain " "'%s'.")
                % self._name,
                NO_SUCH_DOMAIN,
            )

    def switch(self):
        """Switch the destination of the AliasDomain to the new destination,
        set with the method `set_destination()`.
        """
        if not self._domain:
            raise ADErr(
                _("No destination domain set for the alias domain."),
                ALIASDOMAIN_NO_DOMDEST,
            )
        if self._domain.gid < 1:
            raise ADErr(
                _("The target domain '%s' does not exist.") % self._domain.name,
                NO_SUCH_DOMAIN,
            )
        if self._gid < 1:
            raise ADErr(
                _("The alias domain '%s' does not exist.") % self._name,
                NO_SUCH_ALIASDOMAIN,
            )
        if self._gid == self._domain.gid:
            raise ADErr(
                _(
                    "The alias domain '%(alias)s' is already assigned "
                    "to the domain '%(domain)s'."
                )
                % {"alias": self._name, "domain": self._domain.name},
                ALIASDOMAIN_EXISTS,
            )
        dbc = self._dbh.cursor()
        dbc.execute(
            "UPDATE domain_name SET gid = %s WHERE gid = %s AND "
            "domainname = %s AND NOT is_primary",
            (self._domain.gid, self._gid, self._name),
        )
        self._dbh.commit()
        dbc.close()
        self._gid = self._domain.gid

    def delete(self):
        """Delete the AliasDomain's record form the database.

        Raises an AliasDomainError if the AliasDomain doesn't exist.
        """
        if self._gid < 1:
            raise ADErr(
                _("The alias domain '%s' does not exist.") % self._name,
                NO_SUCH_ALIASDOMAIN,
            )
        dbc = self._dbh.cursor()
        dbc.execute(
            "DELETE FROM domain_name WHERE domainname = %s AND NOT " "is_primary",
            (self._name,),
        )
        if dbc.rowcount > 0:
            self._dbh.commit()
            self._gid = 0
        dbc.close()


del _
