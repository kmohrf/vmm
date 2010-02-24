:mod:`VirtualMailManager.EmailAddress` --- Handling of e-mail addresses
=======================================================================

.. module:: VirtualMailManager.EmailAddress
  :synopsis: Handling of e-mail addresses

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2


This module provides the :class:`EmailAddress` class to handle validated e-mail
addresses.


EmailAddress
------------

.. class:: EmailAddress(address)

  Creates a new EmailAddress instance.

  :param address: string representation of an e-mail addresses
  :type address: :obj:`basestring`
  :raise VirtualMailManager.Exceptions.VMMEmailAddressException: if the
    *address* is syntactically wrong.
  :raise VirtualMailManager.Exceptions.VMMException: if the validation of the
    local-part or domain name fails.

  An EmailAddress instance has the both read-only attributes:

  .. attribute:: localpart

    The local-part of the address *local-part@domain*


  .. attribute:: domainname

    The domain part of the address *local-part@domain*


Examples
--------

  >>> from VirtualMailManager.EmailAddress import EmailAddress
  >>> john = EmailAddress('john.doe@example.com')
  >>> john.localpart
  'john.doe'
  >>> john.domainname
  'example.com'
  >>> jane = EmailAddress('jane.doe@example.com')
  >>> jane != john
  True
  >>> EmailAddress('info@xn--pypal-4ve.tld') == EmailAddress(u'info@pаypal.tld')
  True
  >>> jane
  EmailAddress('jane.doe@example.com')
  >>> print john
  john.doe@example.com
  >>> 
