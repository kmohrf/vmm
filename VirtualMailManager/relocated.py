# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2013, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.relocated
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's Relocated class to handle relocated users.
"""

from VirtualMailManager.domain import get_gid
from VirtualMailManager.emailaddress import EmailAddress, \
     DestinationEmailAddress
from VirtualMailManager.errors import RelocatedError as RErr
from VirtualMailManager.constants import DOMAIN_INVALID, NO_SUCH_DOMAIN, \
     NO_SUCH_RELOCATED, RELOCATED_ADDR_DEST_IDENTICAL, RELOCATED_EXISTS


_ = lambda msg: msg


class Relocated(object):
    """Class to handle e-mail addresses of relocated users."""
    __slots__ = ('_addr', '_dest', '_gid', '_dbh')

    def __init__(self, dbh, address):
        """Creates a new *Relocated* instance.  The ``address`` is the
        old e-mail address of the user.

        Use `setDestination()` to set/update the new address, where the
        user has moved to.

        """
        assert isinstance(address, EmailAddress)
        self._addr = address
        self._dbh = dbh
        self._gid = get_gid(self._dbh, self._addr.domainname)
        if not self._gid:
            raise RErr(_(u"The domain '%s' does not exist.") %
                       self._addr.domainname, NO_SUCH_DOMAIN)
        self._dest = None

        self._load()

    def __nonzero__(self):
        """Returns `True` if the Relocated is known, `False` if it's new."""
        return self._dest is not None

    def _load(self):
        """Loads the destination address from the database into the
        `_dest` attribute.

        """
        dbc = self._dbh.cursor()
        dbc.execute('SELECT destination FROM relocated WHERE gid = %s AND '
                    'address = %s', (self._gid, self._addr.localpart))
        destination = dbc.fetchone()
        dbc.close()
        if destination:
            destination = DestinationEmailAddress(destination[0], self._dbh)
            if destination.at_localhost:
                raise RErr(_(u"The destination address' domain name must not "
                             u"be localhost."), DOMAIN_INVALID)
            self._dest = destination

    @property
    def address(self):
        """The Relocated's EmailAddress instance."""
        return self._addr

    def set_destination(self, destination):
        """Sets/updates the new address of the relocated user."""
        update = False
        assert isinstance(destination, DestinationEmailAddress)
        if destination.at_localhost:
            raise RErr(_(u"The destination address' domain name must not be "
                         u"localhost."), DOMAIN_INVALID)
        if self._addr == destination:
            raise RErr(_(u'Address and destination are identical.'),
                       RELOCATED_ADDR_DEST_IDENTICAL)
        if self._dest:
            if self._dest == destination:
                raise RErr(_(u"The relocated user '%s' already exists.") %
                           self._addr, RELOCATED_EXISTS)
            else:
                self._dest = destination
                update = True
        else:
            self._dest = destination

        dbc = self._dbh.cursor()
        if not update:
            dbc.execute('INSERT INTO relocated (gid, address, destination) '
                        'VALUES (%s, %s, %s)',
                        (self._gid, self._addr.localpart, str(self._dest)))
        else:
            dbc.execute('UPDATE relocated SET destination = %s WHERE gid = %s '
                        'AND address = %s',
                        (str(self._dest), self._gid, self._addr.localpart))
        self._dbh.commit()
        dbc.close()

    def get_info(self):
        """Returns the address to which mails should be sent."""
        if not self._dest:
            raise RErr(_(u"The relocated user '%s' does not exist.") %
                       self._addr, NO_SUCH_RELOCATED)
        return self._dest

    def delete(self):
        """Deletes the relocated entry from the database."""
        if not self._dest:
            raise RErr(_(u"The relocated user '%s' does not exist.") %
                       self._addr, NO_SUCH_RELOCATED)
        dbc = self._dbh.cursor()
        dbc.execute('DELETE FROM relocated WHERE gid = %s AND address = %s',
                    (self._gid, self._addr.localpart))
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()
        self._dest = None

del _
