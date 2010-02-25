:mod:`VirtualMailManager.Config` ---  Simplified configuration access
======================================================================

.. module:: VirtualMailManager.Config
  :synopsis: Simplified configuration access

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2


This module provides a few classes for simplified configuration handling
and the validation of the setting's  *type* and *value*.

:class:`LazyConfig` is derived from Python's
:class:`ConfigParser.RawConfigParser`. It doesn't use ``RawConfigParser``'s
``DEFAULT`` section. All settings and their defaults, if supposed, are
handled by :class:`LazyConfigOption` objects in the :attr:`LazyConfig._cfg`
*dict*.

``LazyConfig``'s setters and getters for options are taking a single string
for the *section* and *option* argument, e.g. ``config.pget('database.user')``
instead of ``config.get('database', 'user')``.



LazyConfig
----------
.. class:: LazyConfig

  Bases: :class:`ConfigParser.RawConfigParser`

  .. versionadded:: 0.6.0

  .. attribute:: _cfg

    a multi dimensional :class:`dict`, containing *sections* and *options*,
    represented by :class:`LazyConfigOption` objects.

    For example::

      from VirtualMailManager.Config import LazyConfig, LazyConfigOption

      class FooConfig(LazyConfig):
          def __init__(self, ...):
              LazyConfig.__init__(self)
              ...
              LCO = LazyConfigOption
              self._cfg = {
                  'database': {# section database:
                      'host': LCO(str, '::1', self.get), # options of the
                      'name': LCO(str, 'dbx', self.get), # database section.
                      'pass': LCO(str, None, self.get),  # No defaults for the
                      'user': LCO(str, None, self.get),  # user and pass options
                  }
              }

          ...


  .. method:: bool_new(value)

    Converts the string *value* into a `bool` and returns it.

    | ``'1'``, ``'on'``, ``'yes'`` and ``'true'`` will become :const:`True`
    | ``'0'``, ``'off'``, ``'no'`` and ``'false'`` will become :const:`False`

    :param value: one of the above mentioned strings
    :type value: :obj:`basestring`
    :rtype: bool
    :raise ConfigValueError: for all other values, except ``bool``\ s

  .. method:: dget(option)

    Like :meth:`pget`, but returns the *option*'s default value, from
    :attr:`_cfg` (defined by :attr:`LazyConfigOption.default`) if the *option*
    is not configured in a ini-like configuration file.

    :param option: the section.option combination
    :type option: :obj:`basestring`
    :raise NoDefaultError: if the *option* couldn't be found in the
      configuration file and no default value was passed to
      :class:`LazyConfigOption`'s constructor for the requested *option*.

  .. method:: getboolean(section, option)

    Returns the boolean value of the *option*, in the given *section*.

    For a boolean :const:`True`, the value must be set to ``'1'``, ``'on'``,
    ``'yes'``, ``'true'`` or :const:`True`. For a boolean :const:`False`, the
    value must set to ``'0'``, ``'off'``, ``'no'``, ``'false'`` or
    :const:`False`.

    :param section: The section's name
    :type section: :obj:`basestring`
    :param option: The option's name
    :type option: :obj:`basestring`
    :rtype: bool
    :raise ValueError: if the option has an other value than the values
      mentioned above.

  .. method:: has_option(option)

    Checks if the *option* (section\ **.**\ option) is a known configuration
    option.

    :param option: The option's name
    :type option: :obj:`basestring`
    :rtype: bool

  .. method:: has_section(section)

    Checks if *section* is a known configuration section.

    :param section: The section's name
    :type section: :obj:`basestring`
    :rtype: bool

  .. method:: items(section)

    Returns an iterator for ``key, value`` :obj:`tuple`\ s for each option in
    the given *section*.

    :param section: The section's name
    :type section: :obj:`basestring`
    :raise NoSectionError: if the given *section* is not known.

  .. method:: pget(option)

    Polymorphic getter which returns the *option*'s value (by calling
    :attr:`LazyConfigOption.getter`) with the appropriate type, defined by
    :attr:`LazyConfigOption.cls`.

    :param option: the section.option combination
    :type option: :obj:`basestring`

  .. method:: sections()

    Returns an iterator object for all configuration sections from the
    :attr:`_cfg` dictionary.

    :rtype: :obj:`dictionary-keyiterator`

  .. method:: set(option, value)

    Like :meth:`ConfigParser.RawConfigParser.set`, but converts the *option*'s
    new *value* (by calling :attr:`LazyConfigOption.cls`) to the appropriate
    type/class. When the ``LazyConfigOption``'s optional parameter *validate*
    was not :const:`None`, the new *value* will be also validated.

    :param option: the section.option combination
    :type option: :obj:`basestring`
    :param value: the new value to be set
    :type value: :obj:`basestring`
    :rtype: :const:`None`
    :raise ConfigValueError: if a boolean value shout be set (:meth:`bool_new`)
      and it fails
    :raise ValueError: if an other setter (:attr:`LazyConfigOption.cls`) or
      validator (:attr:`LazyConfigOption.validate`) fails.
    :raise VirtualMailManager.Exceptions.VMMException: if
      :attr:`LazyConfigOption.validate` is set to
      :func:`VirtualMailManager.exec_ok` or :func:`VirtualMailManager.is_dir`.


LazyConfigOption
----------------
LazyConfigOption instances are required by :class:`LazyConfig` instances, and
instances of classes derived from `LazyConfig`, like the :class:`Config`
class.

.. class:: LazyConfigOption (cls, default, getter[, validate=None])

  .. versionadded:: 0.6.0

  The constructor's parameters are:

  ``cls`` : :obj:`type`
    The class/type of the option's value.
  ``default`` : :obj:`str` or the one defined by ``cls``
    Default value of the option. Use :const:`None` if the option shouldn't
    have a default value.
  ``getter``: :obj:`callable`
    A method's name of :class:`ConfigParser.RawConfigParser` and derived
    classes, to get a option's value, e.g. `self.getint`.
  ``validate`` : :obj:`callable` or :const:`None`
    :const:`None` or any function, which takes one argument and returns the
    validated argument with the appropriate type (for example:
    :meth:`LazyConfig.bool_new`). The function should raise a 
    :exc:`ConfigValueError` if the validation fails. This function checks the
    new value when :meth:`LazyConfig.set()` is called.

  Each LazyConfigOption object has the following read-only attributes:

  .. attribute:: cls

    The class of the option's value e.g. `str`, `unicode` or `bool`. Used as
    setter method when :meth:`LazyConfig.set` (or the ``set()`` method of a
    derived class) is called.

  .. attribute:: default

    The option's default value, may be ``None``

  .. attribute:: getter

    A method's name of :class:`ConfigParser.RawConfigParser` and derived
    classes, to get a option's value, e.g. ``self.getint``.

  .. attribute:: validate

    A method or function to validate the option's new value.


Config
------
The final configuration class of the virtual mail manager.

.. class:: Config (filename)

  Bases: :class:`LazyConfig`

  :param filename: absolute path to the configuration file.
  :type filename: :obj:`basestring`

  .. attribute:: _cfg

    The configuration ``dict``, containing all configuration sections and
    options, as described in :attr:`LazyConfig._cfg`.

  .. method:: check()

    Checks all section's options for settings w/o a default value.

    :raise VirtualMailManager.Exceptions.VMMConfigException: if the check fails

  .. method:: load()

    Loads the configuration read-only.

    :raise VirtualMailManager.Exceptions.VMMConfigException: if the
      configuration syntax is invalid

  .. method:: unicode(section, option)

    Returns the value of the *option* from *section*, converted to Unicode.
    This method is intended for the :attr:`LazyConfigOption.getter`.

    :param section: The name of the configuration section
    :type section: :obj:`basestring`
    :param option: The name of the configuration option
    :type option: :obj:`basestring`
    :rtype: :obj:`unicode`


Exceptions
----------

.. exception:: BadOptionError (msg)

  Bases: :exc:`ConfigParser.Error`

  Raised when a option isn't in the format 'section.option'.

.. exception:: ConfigValueError (msg)

  Bases: :exc:`ConfigParser.Error`

  Raised when creating or validating of new values fails.

.. exception:: NoDefaultError (section, option)

  Bases: :exc:`ConfigParser.Error`

  Raised when the requested option has no default value.
