# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.Relocated

    Virtual Mail Manager's Relocated class to handle relocated users.
"""

from VirtualMailManager.Domain import Domain
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.Exceptions import VMMRelocatedException as VMMRE
from VirtualMailManager.constants.ERROR import NO_SUCH_DOMAIN, \
     NO_SUCH_RELOCATED, RELOCATED_ADDR_DEST_IDENTICAL, RELOCATED_EXISTS


_ = lambda msg: msg


class Relocated(object):
    """Class to handle e-mail addresses of relocated users."""
    __slots__ = ('_addr', '_dest', '_gid', '_dbh')

    def __init__(self, dbh, address):
        """Creates a new *Relocated* instance. The ``address`` is the
        old e-mail address of the user.

        Use `setDestination()` to set/update the new address, where the
        user has moved to."""
        if isinstance(address, EmailAddress):
            self._addr = address
        else:
            raise TypeError("Argument 'address' is not an EmailAddress")
        self._dbh = dbh
        self._gid = 0
        self._dest = None

        self.__set_gid()
        self.__load()

    def __set_gid(self):
        """Sets the `_gid` attribute, based on the `_addr.domainname`."""
        dom = Domain(self._dbh, self._addr.domainname)
        self._gid = dom.getID()
        if self._gid == 0:
            raise VMMRE(_(u"The domain “%s” doesn't exist.") %
                        self._addr.domainname, NO_SUCH_DOMAIN)

    def __load(self):
        """Loads the destination address from the database into the
        `_dest` attribute."""
        dbc = self._dbh.cursor()
        dbc.execute(
            'SELECT destination FROM relocated WHERE gid=%s AND address=%s',
                    self._gid, self._addr.localpart)
        destination = dbc.fetchone()
        dbc.close()
        if destination:
            self._dest = EmailAddress(destination[0])

    def setDestination(self, destination):
        """Sets/updates the new address of the relocated user."""
        update = False
        if isinstance(destination, EmailAddress):
            if self._addr == destination:
                raise VMMRE(_(u'Address and destination are identical.'),
                            RELOCATED_ADDR_DEST_IDENTICAL)
            if self._dest:
                if self._dest == destination:
                    raise VMMRE(
                            _(u'The relocated user “%s” already exists.') %
                                self._addr, RELOCATED_EXISTS)
                else:
                    self._dest = destination
                    update = True
            else:
                self._dest = destination
        else:
            raise TypeError("Argument 'destination' is not an EmailAddress")

        dbc = self._dbh.cursor()
        if not update:
            dbc.execute('INSERT INTO relocated VALUES (%s, %s, %s)',
                        self._gid, self._addr.localpart, str(self._dest))
        else:
            dbc.execute('UPDATE relocated SET destination=%s \
WHERE gid=%s AND address=%s',
                        str(self._dest), self._gid, self._addr.localpart)
        self._dbh.commit()
        dbc.close()

    def getInfo(self):
        """Returns the address to which mails should be sent."""
        if self._dest:
            return self._dest
        else:
            raise VMMRE(_(u"The relocated user “%s” doesn't exist.") %
                        self._addr, NO_SUCH_RELOCATED)

    def delete(self):
        """Deletes the relocated entry from the database."""
        if not self._dest:
            raise VMMRE(_(u"The relocated user “%s” doesn't exist.") %
                        self._addr, NO_SUCH_RELOCATED)
        dbc = self._dbh.cursor()
        dbc.execute("DELETE FROM relocated WHERE gid = %s AND address = %s",
                    self._gid, self._addr.localpart)
        if dbc.rowcount > 0:
            self._dbh.commit()
        dbc.close()
        self._dest = None


del _
