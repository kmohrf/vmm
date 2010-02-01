# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""vmm's configuration module for simplified configuration access.

This module defines a few classes:

``LazyConfig``
    This class provides the following additonal methods

    * `LazyConfig.pget()`
        polymorphic getter which returns the value with the appropriate
        type.
    * `LazyConfig.dget()`
        like *pget()*, but checks additonal for default values in
        `LazyConfig._cfg`.
    * `LazyConfig.set()`
        like `RawConfigParser.set()`, but converts the new value to the
        appropriate type/class and optional validates the new value.
    * `LazyConfig.bool_new()`
        converts data from raw_input into boolean values.
    * `LazyConfig.get_boolean()`
        like `RawConfigParser.getboolean()`, but doesn't fail on real
        `bool` values.

``Config``
    The Config class used by vmm.

``LazyConfigOption``
    The class for the configuration objects in the ``Config`` class'
    ``_cfg`` dictionary.
"""


from shutil import copy2
from ConfigParser import (Error, MissingSectionHeaderError, NoOptionError,
                          NoSectionError, ParsingError, RawConfigParser)
from cStringIO import StringIO

from __main__ import os, ENCODING, ERR, get_unicode, w_std
from Exceptions import VMMConfigException


class BadOptionError(Error):
    """Raised when a option isn't in the format 'section.option'."""
    pass


class ConfigValueError(Error):
    """Raised when creating or validating of new values fails."""
    pass


class NoDefaultError(Error):
    """Raised when the requested option has no default value."""

    def __init__(self, section, option):
        Error.__init__(self, 'Option %r in section %r has no default value' %(
                       option, section))


class LazyConfig(RawConfigParser):
    """The **lazy** derivate of the `RawConfigParser`.
    
    There are two additional getters:
    
    `LazyConfig.pget()`
        The polymorphic getter, which returns a option's value with the
        appropriate type.
    `LazyConfig.dget()`
        Like `LazyConfig.pget()`, but returns the option's default, from
        `LazyConfig._cfg['sectionname']['optionname'].default`, if the
        option is not configured in a ini-like configuration file.


    `LazyConfig.set()` differs from ``RawConfigParser``'s ``set()`` method.
    ``LazyConfig.set()`` takes the ``section`` and ``option`` arguments
    combined to a single string in the form
    "``section``\ **.**\ ``option``".
    """
    def __init__(self):
        RawConfigParser.__init__(self)
        self._modified = False
        self._cfg = {
            'sectionname': {
                'optionname': LazyConfigOption(int, 1, self.getint)
            }
        }
        """sample _cfg dictionary. Create your own in your derived class."""

    def bool_new(self, value):
        """Converts the string `value` into a `bool` and returns it.

        | '1', 'on', 'yes' and 'true' will become ``True``
        | '0', 'off', 'no' and 'false' will become ``False``

        Throws a `ConfigValueError` for all other values, except ``bool``\ s.
        """
        if isinstance(value, bool):
            return value
        if value.lower() in self._boolean_states:
            return self._boolean_states[value.lower()]
        else:
            raise ConfigValueError(_(u'Not a boolean: “%s”') % \
                                   get_unicode(value))

    def get_boolean(self, section, option):
        # if the setting was not written to the configuration file, it may
        # be still a boolean value - lets see
        if self._modified:
           tmp = self.get(section, option)
           if isinstance(tmp, bool):
               return tmp
        return self.getboolean(section, option)

    def __get_section_option(self, section_option):
        """splits ``section_option`` (section\ **.**\ option) in two parts
        and returns them as list ``[section, option]``, if:

            * it likes the format of ``section_option``
            * the ``section`` is known
            * the ``option`` is known

        Else one of the following exceptions will be thrown:

            * `BadOptionError`
            * `NoSectionError`
            * `NoOptionError`
        """ 
        sect_opt = section_option.lower().split('.')
        if len(sect_opt) != 2:# do we need a regexp to check the format?
            raise BadOptionError(
                        _(u'Bad format: “%s” - expected: section.option') % \
                        get_unicode(section_option))
        if not sect_opt[0] in self._cfg:
            raise NoSectionError(sect_opt[0])
        if not sect_opt[1] in self._cfg[sect_opt[0]]:
            raise NoOptionError(sect_opt[1], sect_opt[0])
        return sect_opt

    def items(self, section):
        """returns an iterable that returns key, value ``tuples`` from the
        given ``section``."""
        if section in self._sections:# check if the section was parsed
            d2 = self._sections[section]
        elif not section in self._cfg:
            raise NoSectionError(section)
        else:
            return ((k, self._cfg[section][k].default) \
                    for k in self._cfg[section].iterkeys())
        # still here? Get defaults and merge defaults with configured setting
        d = dict((k, self._cfg[section][k].default) \
                 for k in self._cfg[section].iterkeys())
        d.update(d2)
        if '__name__' in d: del d['__name__']
        return d.iteritems()

    def dget(self, option):
        """Returns the value of the `option`.
        
        If the option could not be found in the configuration file, the
        configured default value, from ``LazyConfig._cfg`` will be
        returned.
        
        Arguments:
        
        `option` : string
            the configuration option in the form
            "``section``\ **.**\ ``option``"

        Throws a `NoDefaultError`, if no default value was passed to
        `LazyConfigOption.__init__()` for the `option`.
        """
        section, option = self.__get_section_option(option)
        try:
            return self._cfg[section][option].getter(section, option)
        except (NoSectionError, NoOptionError):
            if not self._cfg[section][option].default is None:
                return self._cfg[section][option].default
            else:
                raise NoDefaultError(section, option)

    def pget(self, option):
        """Returns the value of the `option`."""
        section, option = self.__get_section_option(option)
        return self._cfg[section][option].getter(section, option)

    def set(self, option, value):
        """Set the value of an option.
        
        Throws a ``ValueError`` if `value` couldn't be converted to
        ``LazyConfigOption.cls``"""
        section, option = self.__get_section_option(option)
        val = self._cfg[section][option].cls(value)
        if not self._cfg[section][option].validate is None:
            val = self._cfg[section][option].validate(val)
        if not RawConfigParser.has_section(self, section):
            self.add_section(section)
        RawConfigParser.set(self, section, option, val)
        self._modified = True

    def has_section(self, section):
        """Checks if ``section`` is a known configuration section."""
        return section.lower() in self._cfg 

    def has_option(self, option):
        """Checks if the option (section\ **.**\ option) is a known
        configuration option."""
        try:
            self.__get_section_option(option)
            return True
        except(BadOptionError, NoSectionError, NoOptionError):
            return False



class LazyConfigOption(object):
    """A simple container class for configuration settings.

   ``LazyConfigOption`` instances are required by `LazyConfig` instances,
   and instances of classes derived from ``LazyConfig``, like the
   `Config` class.
    """
    __slots__ = ('cls', 'default', 'getter', 'validate')

    def __init__(self, cls, default, getter, validate=None):
        """Creates a new ``LazyConfigOption`` instance.

        Arguments:

        ``cls`` : type
            The class/type of the option's value
        ``default``
            Default value of the option. Use ``None`` if the option should
            not have a default value.
        ``getter`` : callable
            A method's name of `RawConfigParser` and derived classes, to
            get a option's value, e.g. `self.getint`.
        ``validate`` : NoneType or a callable
            None or any method, that takes one argument, in order to check
            the value, when `LazyConfig.set()` is called.
        """
        self.cls = cls
        """The class of the option's value e.g. `str`, `unicode` or `bool`"""
        self.default = default
        """The option's default value, may be ``None``"""
        if callable(getter):
            self.getter = getter
            """The getter method to get the option's value"""
        else:
            raise TypeError('getter has to be a callable, got a %r'\
                            % getter.__class__.__name__)
        if validate is None or callable(validate):
            self.validate = validate
            """A method to validate the value"""
        else:
            raise TypeError('validate has to be callable or None, got a %r'\
                            % validate.__class__.__name__)


class Config(LazyConfig):
    """This class is for reading and modifying vmm's configuration file."""

    def __init__(self, filename):
        """Creates a new Config instance

        Arguments:
     
        ``filename``
            path to the configuration file
        """
        LazyConfig.__init__(self)
        self.__cfgFileName = filename
        self.__cfgFile = None
        self.__missing = {}

        LCO = LazyConfigOption
        bool_t = self.bool_new
        self._cfg = {
            'account': {
                'delete_directory': LCO(bool_t, False, self.get_boolean),
                'directory_mode':   LCO(int,    448,   self.getint),
                'disk_usage':       LCO(bool_t, False, self.get_boolean),
                'password_length':  LCO(int,    8,     self.getint),
                'random_password':  LCO(bool_t, False, self.get_boolean),
                'imap' :            LCO(bool_t, True,  self.get_boolean),
                'pop3' :            LCO(bool_t, True,  self.get_boolean),
                'sieve':            LCO(bool_t, True,  self.get_boolean),
                'smtp' :            LCO(bool_t, True,  self.get_boolean),
            },
            'bin': {
                'dovecotpw': LCO(str, '/usr/sbin/dovecotpw', self.get,
                                 self.exec_ok),
                'du':        LCO(str, '/usr/bin/du', self.get, self.exec_ok),
                'postconf':  LCO(str, '/usr/sbin/postconf', self.get,
                                 self.exec_ok),
            },
            'database': {
                'host': LCO(str, 'localhost', self.get),
                'name': LCO(str, 'mailsys',   self.get),
                'pass': LCO(str, None,        self.get),
                'user': LCO(str, None,        self.get),
            },
            'domain': {
                'auto_postmaster':  LCO(bool_t, True,  self.get_boolean),
                'delete_directory': LCO(bool_t, False, self.get_boolean),
                'directory_mode':   LCO(int,    504,   self.getint),
                'force_deletion':   LCO(bool_t, False, self.get_boolean),
            },
            'maildir': {
                'folders': LCO(str, 'Drafts:Sent:Templates:Trash', self.get),
                'name':    LCO(str, 'Maildir',                     self.get),
            },
            'misc': {
                'base_directory':  LCO(str, '/srv/mail', self.get, self.is_dir),
                'dovecot_version': LCO(int, 12,          self.getint),
                'gid_mail':        LCO(int, 8,           self.getint),
                'password_scheme': LCO(str, 'CRAM-MD5',  self.get,
                                       self.known_scheme),
                'transport':       LCO(str, 'dovecot:',  self.get),
            },
        }

    def load(self):
        """Loads the configuration, read only.

        Raises a VMMConfigException if the configuration syntax is invalid.
        """
        try:
            self.__cfgFile = open(self.__cfgFileName, 'r')
            self.readfp(self.__cfgFile)
        except (MissingSectionHeaderError, ParsingError), e:
            raise VMMConfigException(str(e), ERR.CONF_ERROR)
        finally:
            if not self.__cfgFile is None and not self.__cfgFile.closed:
                self.__cfgFile.close()

    def check(self):
        """Performs a configuration check.

        Raises a VMMConfigException if the check fails.
        """
        if not self.__chkCfg():
            errmsg = StringIO()
            errmsg.write(_(u'Missing options, which have no default value.\n'))
            errmsg.write(_(u'Using configuration file: %s\n') %\
                         self.__cfgFileName)
            for section, options in self.__missing.iteritems():
                errmsg.write(_(u'* Section: %s\n') % section)
                for option in options:
                    errmsg.write((u'    %s\n') % option)
            raise VMMConfigException(errmsg.getvalue(), ERR.CONF_ERROR)

    def getsections(self):
        """Returns an iterator object for all configuration sections."""
        return self._cfg.iterkeys()

    def is_dir(self, path):
        """Checks if ``path`` is a directory.
        
        Throws a `ConfigValueError` if ``path`` is not a directory.
        """
        path = self.__expand_path(path)
        if not os.path.isdir(path):
            raise ConfigValueError(_(u'“%s” is not a directory') % \
                                   get_unicode(path))
        return path

    def exec_ok(self, binary):
        """Checks if the ``binary`` exists and if it is executable.
        
        Throws a `ConfigValueError` if the ``binary`` isn't a file or is
        not executable.
        """
        binary = self.__expand_path(binary)
        if not os.path.isfile(binary):
            raise ConfigValueError(_(u'“%s” is not a file') % \
                                   get_unicode(binary))
        if not os.access(binary, os.X_OK):
            raise ConfigValueError(_(u'File is not executable: “%s”') % \
                                   get_unicode(binary))
        return binary

    def known_scheme(self, scheme):
        """Converts ``scheme`` to upper case and checks if is known by
        Dovecot (listed in VirtualMailManager.SCHEMES).
        
        Throws a `ConfigValueError` if the scheme is not listed in
        VirtualMailManager.SCHEMES.
        """
        scheme = scheme.upper()
        # TODO: VMM.SCHEMES

    def unicode(self, section, option):
        """Returns the value of the ``option`` from ``section``, converted
        to Unicode.
        """
        return get_unicode(self.get(section, option))

    def configure(self, sections):
        """Interactive method for configuring all options in the given sections

        Arguments:
        sections -- list of strings with section names
        """
        input_fmt = _(u'Enter new value for option %(option)s \
[%(current_value)s]: ')
        failures = 0

        w_std(_(u'Using configuration file: %s\n') % self.__cfgFileName)
        for s in sections:
            w_std(_(u'* Configuration section: “%s”') % s )
            for opt, val in self.items(s):
                failures = 0
                while True:
                    newval = raw_input(input_fmt.encode(ENCODING,'replace') %{
                                       'option': opt, 'current_value': val})
                    if newval and newval != val:
                        try:
                            self.set('%s.%s' % (s, opt), newval)
                            break
                        except (ValueError, ConfigValueError), e:
                            w_std(_(u'Warning: %s') % e)
                            failures += 1
                            if failures > 2:
                                raise VMMConfigException(
                                    _(u'Too many failures - try again later.'),
                                    ERR.VMM_TOO_MANY_FAILURES)
                    else:
                        break
            print
        if self._modified:
            self.__saveChanges()

    def __saveChanges(self):
        """Writes changes to the configuration file."""
        copy2(self.__cfgFileName, self.__cfgFileName+'.bak')
        self.__cfgFile = open(self.__cfgFileName, 'w')
        self.write(self.__cfgFile)
        self.__cfgFile.close()

    def __chkCfg(self):
        """Checks all section's options for settings w/o default values.
        
        Returns ``True`` if everything is fine, else ``False``."""
        errors = False
        for section in self._cfg.iterkeys():
            missing = []
            for option, value in self._cfg[section].iteritems():
                if (value.default is None
                and not RawConfigParser.has_option(self, section, option)):
                    missing.append(option)
                    errors = True
            if len(missing):
                self.__missing[section] = missing
        return not errors

    def __expand_path(self, path):
        """Expands paths, starting with ``.`` or ``~``, to an absolute path."""
        if path.startswith('.'):
            return os.path.abspath(path)
        if path.startswith('~'):
            return os.path.expanduser(path)
        return path
