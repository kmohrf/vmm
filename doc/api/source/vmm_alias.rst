:mod:`VirtualMailManager.Alias` --- Handling of alias e-mail addresses
======================================================================

.. module:: VirtualMailManager.Alias
  :synopsis: Handling of alias e-mail addresses

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2


This module provides the :class:`Alias` class. The data are read from/stored
in the ``alias`` table. This table is used by Postfix to rewrite recipient
addresses.


Alias
---------
.. class:: Alias(dbh, address)
  
  Creates a new *Alias* instance. Alias instances provides the :func:`__len__`
  method. So the existence of an alias in the database can be tested with a
  simple if condition.
  
  :param dbh: a database connection
  :type dbh: :class:`pyPgSQL.PgSQL.Connection`
  :param address: the alias e-mail address.
  :type address: :class:`VirtualMailManager.EmailAddress.EmailAddress`

  .. method:: add_destinations(destinations, expansion_limit [, warnings=None])

    Adds the *destinations* to the destinations of the alias. This method
    returns a ``set`` of all addresses which successfully were stored into the
    database.

    If one of the e-mail addresses in *destinations* is the same as the alias
    address, it will be silently discarded. Destination addresses, that are
    already assigned to the alias, will be also ignored.

    When the optional *warnings* list is given, all ignored addresses will be
    appended to it.

    :param destinations: The destination addresses of the alias
    :type destinations: :obj:`list` of
      :class:`VirtualMailManager.EmailAddress.EmailAddress` instances
    :param expansion_limit: The maximal number of destinations (see also:
      `virtual_alias_expansion_limit
      <http://www.postfix.org/postconf.5.html#virtual_alias_expansion_limit>`_)
    :type expansion_limit: :obj:`int`
    :param warnings: A optional list, to record all ignored addresses
    :type warnings: :obj:`list`
    :rtype: :obj:`set`
    :raise VirtualMailManager.errors.AliasError: if the additional
      *destinations* will exceed the *expansion_limit* or if the alias
      already exceeds its *expansion_limit*.

    .. seealso:: :mod:`VirtualMailManager.ext.postconf` -- to read actual
      values of Postfix configuration parameters.


  .. method:: del_destination(destination)

    Deletes the given *destination* address from the alias.

    :param destination: a destination address of the alias
    :type destination: :class:`VirtualMailManager.EmailAddress.EmailAddress`
    :rtype: :obj:`None`
    :raise VirtualMailManager.errors.AliasError: if the destination wasn't
      assigned to the alias or the alias doesn't exist.


  .. method:: delete()
    
    Deletes the alias with all its destinations.

    :rtype: :obj:`None`
    :raise VirtualMailManager.errors.AliasError: if the alias doesn't exist.


  .. method:: get_destinations()

    Returns an iterator for all destinations (``EmailAddress`` instances) of
    the alias.

    :rtype: :obj:`listiterator`
    :raise VirtualMailManager.errors.AliasError: if the alias doesn't exist.
