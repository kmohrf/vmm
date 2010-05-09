# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.cli.CliConfig

    Adds some interactive stuff to the Config class.
"""

from ConfigParser import RawConfigParser
from shutil import copy2

from VirtualMailManager import ENCODING
from VirtualMailManager.Config import Config, ConfigValueError, LazyConfig
from VirtualMailManager.errors import ConfigError
from VirtualMailManager.cli import w_std
from VirtualMailManager.constants.ERROR import VMM_TOO_MANY_FAILURES


class CliConfig(Config):
    """Adds the interactive ``configure`` method to the `Config` class
    and overwrites `LazyConfig.set(), in order to update a single option
    in the configuration file with a single command line command.
    """

    def configure(self, sections):
        """Interactive method for configuring all options of the given
        iterable ``sections`` object."""
        input_fmt = _(u'Enter new value for option %(option)s '
                      u'[%(current_value)s]: ')
        failures = 0

        w_std(_(u'Using configuration file: %s\n') % self._cfg_filename)
        for s in sections:
            w_std(_(u'* Configuration section: %r') % s)
            for opt, val in self.items(s):
                failures = 0
                while True:
                    newval = raw_input(input_fmt.encode(ENCODING, 'replace') %
                                       {'option': opt, 'current_value': val})
                    if newval and newval != val:
                        try:
                            LazyConfig.set(self, '%s.%s' % (s, opt), newval)
                            break
                        except (ValueError, ConfigValueError), e:
                            w_std(_(u'Warning: %s') % e)
                            failures += 1
                            if failures > 2:
                                raise ConfigError(_(u'Too many failures - try '
                                                    u'again later.'),
                                                  VMM_TOO_MANY_FAILURES)
                    else:
                        break
            print
        if self._modified:
            self.__saveChanges()

    def set(self, option, value):
        """Set the value of an option.

        If the new `value` has been set, the configuration file will be
        immediately updated.

        Throws a ``ValueError`` if `value` couldn't be converted to
        ``LazyConfigOption.cls``"""
        section, option_ = self._get_section_option(option)
        val = self._cfg[section][option_].cls(value)
        if self._cfg[section][option_].validate:
            val = self._cfg[section][option_].validate(val)
        # Do not write default values also skip identical values
        if not self._cfg[section][option_].default is None:
            old_val = self.dget(option)
        else:
            old_val = self.pget(option)
        if val == old_val:
            return
        if not RawConfigParser.has_section(self, section):
            self.add_section(section)
        RawConfigParser.set(self, section, option_, val)
        self.__saveChanges()

    def __saveChanges(self):
        """Writes changes to the configuration file."""
        copy2(self._cfg_filename, self._cfg_filename + '.bak')
        self._cfg_file = open(self._cfg_filename, 'w')
        self.write(self._cfg_file)
        self._cfg_file.close()
