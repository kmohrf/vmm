:mod:`VirtualMailManager.Exceptions` --- Exception classes
==========================================================

.. module:: VirtualMailManager.Exceptions
  :synopsis: Exception classes

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2

Exceptions, used by VirtualMailManager's classes.


Exceptions
----------

.. exception:: VMMException(msg, code)

  Bases: :exc:`exceptions.Exception`

  :param msg: the error message
  :type msg: :obj:`basestring`
  :param code: the error code (one of :mod:`VirtualMailManager.constants.ERROR`)
  :type code: :obj:`int`

  Base class for all other Exceptions in the VirtualMailManager package.


  .. method:: msg

    :rtype: :obj:`basestring`

    Returns the error message of the exception.


  .. method:: code

    :rtype: :obj:`int`

    Returns the numerical error code of the exception.


.. exception:: VMMConfigException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for configuration (:mod:`VirtualMailManager.Config`)
  exceptions.


.. exception:: VMMNotRootException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for non-root exceptions.


.. exception:: VMMDomainException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for Domain (:mod:`VirtualMailManager.Domain`) exceptions.


.. exception:: VMMAliasDomainException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for AliasDomain (:mod:`VirtualMailManager.AliasDomain`)
  exceptions.


.. exception:: VMMAccountException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for Account (:mod:`VirtualMailManager.Account`) exceptions.


.. exception:: VMMAliasException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for Alias (:mod:`VirtualMailManager.Alias`) exceptions.


.. exception:: VMMEmailAddressException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for EmailAddress (:mod:`VirtualMailManager.EmailAddress`)
  exceptions.


.. exception:: VMMMailLocationException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for MailLocation (:mod:`VirtualMailManager.MailLocation`)
  exceptions.


.. exception:: VMMRelocatedException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for Relocated (:mod:`VirtualMailManager.Relocated`)
  exceptions.


.. exception:: VMMTransportException(msg, code)

  Bases: :exc:`VirtualMailManager.Exceptions.VMMException`

  Exception class for Transport (:mod:`VirtualMailManager.Transport`)
  exceptions.

