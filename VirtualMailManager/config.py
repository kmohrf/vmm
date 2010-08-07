# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.config
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    VMM's configuration module for simplified configuration access.
"""

from ConfigParser import \
     Error, MissingSectionHeaderError, NoOptionError, NoSectionError, \
     ParsingError, RawConfigParser
from cStringIO import StringIO# TODO: move interactive stff to cli

from VirtualMailManager.common import VERSION_RE, \
     exec_ok, expand_path, get_unicode, lisdir, version_hex
from VirtualMailManager.constants import CONF_ERROR
from VirtualMailManager.errors import ConfigError, VMMError
from VirtualMailManager.maillocation import known_format
from VirtualMailManager.password import verify_scheme as _verify_scheme


_ = lambda msg: msg


class BadOptionError(Error):
    """Raised when a option isn't in the format 'section.option'."""
    pass


class ConfigValueError(Error):
    """Raised when creating or validating of new values fails."""
    pass


class NoDefaultError(Error):
    """Raised when the requested option has no default value."""

    def __init__(self, section, option):
        Error.__init__(self, 'Option %r in section %r has no default value' %
                             (option, section))


class LazyConfig(RawConfigParser):
    """The **lazy** derivate of the `RawConfigParser`.

    There are two additional getters:

    `pget()`
      The polymorphic getter, which returns a option's value with the
      appropriate type.
    `dget()`
      Like `LazyConfig.pget()`, but returns the option's default, from
      `LazyConfig._cfg['sectionname']['optionname'].default`, if the
      option is not configured in a ini-like configuration file.

    `set()` differs from `RawConfigParser`'s `set()` method. `set()`
    takes the `section` and `option` arguments combined to a single
    string in the form "section.option".
    """

    def __init__(self):
        RawConfigParser.__init__(self)
        self._modified = False
        # sample _cfg dict.  Create your own in your derived class.
        self._cfg = {
            'sectionname': {
                'optionname': LazyConfigOption(int, 1, self.getint),
            }
        }

    def bool_new(self, value):
        """Converts the string `value` into a `bool` and returns it.

        | '1', 'on', 'yes' and 'true' will become `True`
        | '0', 'off', 'no' and 'false' will become `False`

        Throws a `ConfigValueError` for all other values, except bools.
        """
        if isinstance(value, bool):
            return value
        if value.lower() in self._boolean_states:
            return self._boolean_states[value.lower()]
        else:
            raise ConfigValueError(_(u"Not a boolean: '%s'") %
                                   get_unicode(value))

    def getboolean(self, section, option):
        """Returns the boolean value of the option, in the given
        section.

        For a boolean True, the value must be set to '1', 'on', 'yes',
        'true' or True. For a boolean False, the value must set to '0',
        'off', 'no', 'false' or False.
        If the option has another value assigned this method will raise
        a ValueError.
        """
        # if the setting was modified it may be still a boolean value lets see
        tmp = self.get(section, option)
        if isinstance(tmp, bool):
            return tmp
        if not tmp.lower() in self._boolean_states:
            raise ValueError('Not a boolean: %s' % tmp)
        return self._boolean_states[tmp.lower()]

    def _get_section_option(self, section_option):
        """splits ``section_option`` (section.option) in two parts and
        returns them as list ``[section, option]``, if:

          * it likes the format of ``section_option``
          * the ``section`` is known
          * the ``option`` is known

        Else one of the following exceptions will be thrown:

          * `BadOptionError`
          * `NoSectionError`
          * `NoOptionError`
        """
        sect_opt = section_option.lower().split('.')
        # TODO: cache it
        if len(sect_opt) != 2 or not sect_opt[0] or not sect_opt[1]:
            raise BadOptionError(_(u"Bad format: '%s' - expected: "
                                   u"section.option") %
                                 get_unicode(section_option))
        if not sect_opt[0] in self._cfg:
            raise NoSectionError(sect_opt[0])
        if not sect_opt[1] in self._cfg[sect_opt[0]]:
            raise NoOptionError(sect_opt[1], sect_opt[0])
        return sect_opt

    def items(self, section):
        """returns an iterable that returns key, value ``tuples`` from
        the given ``section``.
        """
        if section in self._sections:  # check if the section was parsed
            sect = self._sections[section]
        elif not section in self._cfg:
            raise NoSectionError(section)
        else:
            return ((k, self._cfg[section][k].default) \
                    for k in self._cfg[section].iterkeys())
        # still here? Get defaults and merge defaults with configured setting
        defaults = dict((k, self._cfg[section][k].default) \
                        for k in self._cfg[section].iterkeys())
        defaults.update(sect)
        if '__name__' in defaults:
            del defaults['__name__']
        return defaults.iteritems()

    def dget(self, option):
        """Returns the value of the `option`.

        If the option could not be found in the configuration file, the
        configured default value, from ``LazyConfig._cfg`` will be
        returned.

        Arguments:

        `option` : string
            the configuration option in the form "section.option"

        Throws a `NoDefaultError`, if no default value was passed to
        `LazyConfigOption.__init__()` for the `option`.
        """
        section, option = self._get_section_option(option)
        try:
            return self._cfg[section][option].getter(section, option)
        except (NoSectionError, NoOptionError):
            if not self._cfg[section][option].default is None:  # may be False
                return self._cfg[section][option].default
            else:
                raise NoDefaultError(section, option)

    def pget(self, option):
        """Returns the value of the `option`."""
        section, option = self._get_section_option(option)
        return self._cfg[section][option].getter(section, option)

    def set(self, option, value):
        """Set the `value` of the `option`.

        Throws a `ValueError` if `value` couldn't be converted using
        `LazyConfigOption.cls`.
        """
        # pylint: disable=W0221
        # @pylint: _L A Z Y_
        section, option = self._get_section_option(option)
        val = self._cfg[section][option].cls(value)
        if self._cfg[section][option].validate:
            val = self._cfg[section][option].validate(val)
        if not RawConfigParser.has_section(self, section):
            self.add_section(section)
        RawConfigParser.set(self, section, option, val)
        self._modified = True

    def has_section(self, section):
        """Checks if `section` is a known configuration section."""
        return section.lower() in self._cfg

    def has_option(self, option):
        """Checks if the option (section.option) is a known
        configuration option.
        """
        # pylint: disable=W0221
        # @pylint: _L A Z Y_
        try:
            self._get_section_option(option)
            return True
        except(BadOptionError, NoSectionError, NoOptionError):
            return False

    def sections(self):
        """Returns an iterator object for all configuration sections."""
        return self._cfg.iterkeys()


class LazyConfigOption(object):
    """A simple container class for configuration settings.

    `LazyConfigOption` instances are required by `LazyConfig` instances,
    and instances of classes derived from `LazyConfig`, like the
    `Config` class.
    """
    __slots__ = ('__cls', '__default', '__getter', '__validate')

    def __init__(self, cls, default, getter, validate=None):
        """Creates a new `LazyConfigOption` instance.

        Arguments:

        `cls` : type
          The class/type of the option's value
        `default`
          Default value of the option. Use ``None`` if the option should
          not have a default value.
        `getter` : callable
          A method's name of `RawConfigParser` and derived classes, to
          get a option's value, e.g. `self.getint`.
        `validate` : NoneType or a callable
          None or any method, that takes one argument, in order to
          check the value, when `LazyConfig.set()` is called.
        """
        self.__cls = cls
        if not default is None:  # enforce the type of the default value
            self.__default = self.__cls(default)
        else:
            self.__default = default
        if not callable(getter):
            raise TypeError('getter has to be a callable, got a %r' %
                            getter.__class__.__name__)
        self.__getter = getter
        if validate and not callable(validate):
            raise TypeError('validate has to be callable or None, got a %r' %
                            validate.__class__.__name__)
        self.__validate = validate

    @property
    def cls(self):
        """The class of the option's value e.g. `str`, `unicode` or `bool`."""
        return self.__cls

    @property
    def default(self):
        """The option's default value, may be `None`"""
        return self.__default

    @property
    def getter(self):
        """The getter method or function to get the option's value"""
        return self.__getter

    @property
    def validate(self):
        """A method or function to validate the value"""
        return self.__validate


class Config(LazyConfig):
    """This class is for reading vmm's configuration file."""

    def __init__(self, filename):
        """Creates a new Config instance

        Arguments:

        `filename` : str
          path to the configuration file
        """
        LazyConfig.__init__(self)
        self._cfg_filename = filename
        self._cfg_file = None
        self.__missing = {}

        LCO = LazyConfigOption
        bool_t = self.bool_new
        self._cfg = {
            'account': {
                'delete_directory': LCO(bool_t, False, self.getboolean),
                'directory_mode': LCO(int, 448, self.getint),
                'disk_usage': LCO(bool_t, False, self.getboolean),
                'password_length': LCO(int, 8, self.getint),
                'random_password': LCO(bool_t, False, self.getboolean),
                'imap': LCO(bool_t, True, self.getboolean),
                'pop3': LCO(bool_t, True, self.getboolean),
                'sieve': LCO(bool_t, True, self.getboolean),
                'smtp': LCO(bool_t, True, self.getboolean),
            },
            'bin': {
                'dovecotpw': LCO(str, '/usr/sbin/dovecotpw', self.get,
                                 exec_ok),
                'du': LCO(str, '/usr/bin/du', self.get, exec_ok),
                'postconf': LCO(str, '/usr/sbin/postconf', self.get, exec_ok),
            },
            'database': {
                'host': LCO(str, 'localhost', self.get),
                'name': LCO(str, 'mailsys', self.get),
                'pass': LCO(str, None, self.get),
                'user': LCO(str, None, self.get),
            },
            'domain': {
                'auto_postmaster': LCO(bool_t, True, self.getboolean),
                'delete_directory': LCO(bool_t, False, self.getboolean),
                'directory_mode': LCO(int, 504, self.getint),
                'force_deletion': LCO(bool_t, False, self.getboolean),
            },
            'mailbox': {
                'folders': LCO(str, 'Drafts:Sent:Templates:Trash',
                               self.unicode),
                'format': LCO(str, 'maildir', self.get, check_mailbox_format),
                'root': LCO(str, 'Maildir', self.unicode),
                'subscribe': LCO(bool_t, True, self.getboolean),
            },
            'misc': {
                'base_directory': LCO(str, '/srv/mail', self.get, is_dir),
                'crypt_blowfish_rounds': LCO(int, 5, self.getint),
                'crypt_sha256_rounds': LCO(int, 5000, self.getint),
                'crypt_sha512_rounds': LCO(int, 5000, self.getint),
                'dovecot_version': LCO(str, None, self.hexversion,
                                       check_version_format),
                'password_scheme': LCO(str, 'CRAM-MD5', self.get,
                                       verify_scheme),
                'transport': LCO(str, 'dovecot:', self.get),
            },
        }

    def load(self):
        """Loads the configuration, read only.

        Raises a ConfigError if the configuration syntax is
        invalid.
        """
        try:
            self._cfg_file = open(self._cfg_filename, 'r')
            self.readfp(self._cfg_file)
        except (MissingSectionHeaderError, ParsingError), err:
            raise ConfigError(str(err), CONF_ERROR)
        finally:
            if self._cfg_file and not self._cfg_file.closed:
                self._cfg_file.close()

    def check(self):
        """Performs a configuration check.

        Raises a ConfigError if settings w/o a default value are missed.
        Or a ConfigValueError if 'misc.dovecot_version' has the wrong
        format.
        """
        # TODO: There are only two settings w/o defaults.
        #       So there is no need for cStringIO
        if not self._chk_cfg():
            errmsg = StringIO()
            errmsg.write(_(u'Missing options, which have no default value.\n'))
            errmsg.write(_(u'Using configuration file: %s\n') %
                         self._cfg_filename)
            for section, options in self.__missing.iteritems():
                errmsg.write(_(u'* Section: %s\n') % section)
                for option in options:
                    errmsg.write((u'    %s\n') % option)
            raise ConfigError(errmsg.getvalue(), CONF_ERROR)
        check_version_format(self.get('misc', 'dovecot_version'))

    def hexversion(self, section, option):
        """Converts the version number (e.g.: 1.2.3) from the *option*'s
        value to an int."""
        return version_hex(self.get(section, option))

    def unicode(self, section, option):
        """Returns the value of the `option` from `section`, converted
        to Unicode."""
        return get_unicode(self.get(section, option))

    def _chk_cfg(self):
        """Checks all section's options for settings w/o a default
        value.

        Returns `True` if everything is fine, else `False`.
        """
        errors = False
        for section in self._cfg.iterkeys():
            missing = []
            for option, value in self._cfg[section].iteritems():
                if (value.default is None and
                    not RawConfigParser.has_option(self, section, option)):
                    missing.append(option)
                    errors = True
            if missing:
                self.__missing[section] = missing
        return not errors


def is_dir(path):
    """Check if the expanded path is a directory.  When the expanded path
    is a directory the expanded path will be returned.  Otherwise a
    ConfigValueError will be raised.
    """
    path = expand_path(path)
    if lisdir(path):
        return path
    raise ConfigValueError(_(u"No such directory: %s") % get_unicode(path))


def check_mailbox_format(format):
    """
    Check if the mailbox format *format* is supported.  When the *format*
    is supported it will be returned, otherwise a `ConfigValueError` will
    be raised.
    """
    format = format.lower()
    if known_format(format):
        return format
    raise ConfigValueError(_(u"Unsupported mailbox format: '%s'") %
                           get_unicode(format))


def check_version_format(version_string):
    """Check if the *version_string* has the proper format, e.g.: '1.2.3'.
    Returns the validated version string if it has the expected format.
    Otherwise a `ConfigValueError` will be raised.
    """
    if not VERSION_RE.match(version_string):
        raise ConfigValueError(_(u"Not a valid Dovecot version: '%s'") %
                               get_unicode(version_string))
    return version_string


def verify_scheme(scheme):
    """Checks if the password scheme *scheme* can be accepted and returns
    the verified scheme.
    """
    try:
        scheme, encoding = _verify_scheme(scheme)
    except VMMError, err:  # 'cast' it
        raise ConfigValueError(err.msg)
    if not encoding:
        return scheme
    return '%s.%s' % (scheme, encoding)

del _
