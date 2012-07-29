:mod:`VirtualMailManager.errors` --- Exception classes
======================================================

.. module:: VirtualMailManager.errors
  :synopsis: Exception classes

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2

Exceptions, used by VirtualMailManager's classes.


Exceptions
----------

.. exception:: VMMError(msg, code)

  Bases: :exc:`exceptions.Exception`

  :param msg: the error message
  :type msg: :obj:`basestring`
  :param code: the error code (one of :mod:`VirtualMailManager.constants.ERROR`)
  :type code: :obj:`int`

  Base class for all other Exceptions in the VirtualMailManager package.

  The *msg* and *code* are accessible via the both attributes:

  .. attribute:: msg

    The error message of the exception.


  .. attribute:: code

    The numerical error code of the exception.


.. exception:: ConfigError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for configuration (:mod:`VirtualMailManager.Config`)
  exceptions.


.. exception:: PermissionError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for file permission exceptions.


.. exception:: NotRootError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for non-root exceptions.


.. exception:: DomainError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for Domain (:mod:`VirtualMailManager.Domain`) exceptions.


.. exception:: AliasDomainError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for AliasDomain (:mod:`VirtualMailManager.AliasDomain`)
  exceptions.


.. exception:: AccountError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for Account (:mod:`VirtualMailManager.Account`) exceptions.


.. exception:: AliasError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for Alias (:mod:`VirtualMailManager.Alias`) exceptions.


.. exception:: EmailAddressError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for EmailAddress (:mod:`VirtualMailManager.EmailAddress`)
  exceptions.


.. exception:: MailLocationError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for MailLocation (:mod:`VirtualMailManager.MailLocation`)
  exceptions.


.. exception:: RelocatedError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for Relocated (:mod:`VirtualMailManager.Relocated`)
  exceptions.


.. exception:: TransportError(msg, code)

  Bases: :exc:`VirtualMailManager.errors.VMMError`

  Exception class for Transport (:mod:`VirtualMailManager.Transport`)
  exceptions.

