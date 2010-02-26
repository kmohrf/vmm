# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.cli.Handler

    A derived Handler class with a few changes/additions for cli use.
"""

import os

from VirtualMailManager.errors import VMMError
from VirtualMailManager.Handler import Handler
from VirtualMailManager.cli import read_pass
from VirtualMailManager.cli.Config import CliConfig as Cfg
from VirtualMailManager.constants.ERROR import INVALID_SECTION
from VirtualMailManager.ext.Postconf import Postconf


class CliHandler(Handler):
    """This class uses a `CliConfig` for configuration stuff, instead of
    the non-interactive `Config` class.

    It provides the additional methods cfgSet() and configure().

    Additionally it uses `VirtualMailManager.cli.read_pass()` for for the
    interactive password dialog.
    """

    __slots__ = ()# nothing additional, also no __dict__/__weakref__

    def __init__(self):
        """Creates a new CliHandler instance.

        Throws a NotRootError if your uid is greater 0.
        """
        # Overwrite the parent CTor partly, we use the CliConfig class
        # and add some command line checks.
        skip_some_checks = os.sys.argv[1] in ('cf', 'configure', 'h', 'help',
                                              'v', 'version')
        super(CliHandler, self).__init__(skip_some_checks)

        self._Cfg = Cfg(self._cfgFileName)
        self._Cfg.load()
        if not skip_some_checks:
            self._Cfg.check()
            self._chkenv()
            self._scheme = self._Cfg.dget('misc.password_scheme')
            self._postconf = Postconf(self._Cfg.dget('bin.postconf'))

    def cfgSet(self, option, value):
        return self._Cfg.set(option, value)

    def configure(self, section=None):
        """Starts the interactive configuration.

        Configures in interactive mode options in the given ``section``.
        If no section is given (default) all options from all sections
        will be prompted.
        """
        if section is None:
            self._Cfg.configure(self._Cfg.sections())
        elif self._Cfg.has_section(section):
            self._Cfg.configure([section])
        else:
            raise VMMError(_(u'Invalid section: “%s”') % section,
                           INVALID_SECTION)

    def userAdd(self, emailaddress, password):
        if password is None:
            password = read_pass()
        super(CliHandler, self).userAdd(emailaddress, password)

    def userPassword(self, emailaddress, password):
        if password is None:
            password = read_pass()
        super(CliHandler, self).userPassword(emailaddress, password)
