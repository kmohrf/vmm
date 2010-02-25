:mod:`VirtualMailManager.Relocated` --- Handling of relocated users
===================================================================

.. module:: VirtualMailManager.Relocated
  :synopsis: Handling of relocated users

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2


This module provides the :class:`Relocated` class. The data are read
from/stored in the ``relocated`` table. An optional lookup table, used
by Postfix for the "``user has moved to new_location``" reject/bounce message.


Relocated
---------
.. class:: Relocated(dbh, address)

  Creates a new *Relocated* instance. If the relocated user with the given
  *address* is already stored in the database use :meth:`get_info` to get the
  destination address of the relocated user. To set or update the destination
  of the relocated user use :meth:`set_destination`. Use :meth:`delete` in
  order to delete the relocated user from the database.
  
  :param dbh: a database connection
  :type dbh: :class:`PgSQL.Connection`
  :param address: the e-mail address of the relocated user.
  :type address: :class:`VirtualMailManager.EmailAddress.EmailAddress`


  .. method:: delete()
  
    :rtype: :obj:`None`
    :raise VirtualMailManager.Exceptions.VMMRelocatedException: if the
      relocated user doesn't exist.

    Deletes the relocated user from the database.


  .. method:: get_info()

    :rtype: :class:`VirtualMailManager.EmailAddress.EmailAddress`
    :raise VirtualMailManager.Exceptions.VMMRelocatedException: if the
      relocated user doesn't exist.

    Returns the destination e-mail address of the relocated user.


  .. method:: set_destination(destination)

    :param destination: the new address where the relocated user has moved to
    :type destination: :class:`VirtualMailManager.EmailAddress.EmailAddress`
    :rtype: :obj:`None`
    :raise VirtualMailManager.Exceptions.VMMRelocatedException: if the
      *destination* address is already saved or is the same as the relocated
      user's address.

    Sets or updates the *destination* address of the relocated user.
