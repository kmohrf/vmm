# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.cli.config
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Adds some interactive stuff to the Config class.
"""

from configparser import RawConfigParser
from gettext import gettext as _
from shutil import copy2
from string import Template

from vmm import ENCODING
from vmm.config import Config, ConfigValueError, LazyConfig
from vmm.errors import ConfigError, VMMError
from vmm.cli import w_err, w_std
from vmm.constants import CONF_ERROR, VMM_TOO_MANY_FAILURES


class CliConfig(Config):
    """Adds the interactive ``configure`` method to the `Config` class
    and overwrites `LazyConfig.set(), in order to update a single option
    in the configuration file with a single command line command.
    """

    def configure(self, sections):
        """Interactive method for configuring all options of the given
        iterable ``sections`` object."""
        input_tpl = Template(
            _("Enter new value for option $option " "[$current_value]: ")
        )
        failures = 0

        w_std(_("Using configuration file: %s\n") % self._cfg_filename)
        for section in sections:
            w_std(_("* Configuration section: '%s'") % section)
            for opt, val in self.items(section):
                failures = 0
                while True:
                    if isinstance(val, str):
                        val = val.encode(ENCODING, "replace").decode(ENCODING)
                    newval = input(input_tpl.substitute(option=opt, current_value=val))
                    if newval and newval != val:
                        try:
                            LazyConfig.set(self, "%s.%s" % (section, opt), newval)
                            break
                        except (ValueError, ConfigValueError, VMMError) as err:
                            w_err(0, _("Warning: %s") % err)
                            failures += 1
                            if failures > 2:
                                raise ConfigError(
                                    _("Too many failures - try " "again later."),
                                    VMM_TOO_MANY_FAILURES,
                                )
                    else:
                        break
            print()
        if self._modified:
            self._save_changes()

    def set(self, option, value):
        """Set the value of an option.

        If the new `value` has been set, the configuration file will be
        immediately updated.

        Throws a ``ConfigError`` if `value` couldn't be converted to
        ``LazyConfigOption.cls`` or ``LazyConfigOption.validate`` fails."""
        section, option_ = self._get_section_option(option)
        try:
            val = self._cfg[section][option_].cls(value)
            if self._cfg[section][option_].validate:
                val = self._cfg[section][option_].validate(val)
        except (ValueError, ConfigValueError) as err:
            raise ConfigError(str(err), CONF_ERROR)
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
        self._save_changes()

    def _save_changes(self):
        """Writes changes to the configuration file."""
        copy2(self._cfg_filename, self._cfg_filename + ".bak")
        with open(self._cfg_filename, "w", encoding="utf-8") as self._cfg_file:
            self.write(self._cfg_file)
