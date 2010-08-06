# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.cli.handler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A derived Handler class with a few changes/additions for cli use.
"""

import os

from VirtualMailManager.errors import VMMError
from VirtualMailManager.handler import Handler
from VirtualMailManager.cli import read_pass
from VirtualMailManager.cli.config import CliConfig as Cfg
from VirtualMailManager.constants import ACCOUNT_EXISTS, INVALID_SECTION, \
     NO_SUCH_ACCOUNT

_ = lambda msg: msg


class CliHandler(Handler):
    """This class uses a `CliConfig` for configuration stuff, instead of
    the non-interactive `Config` class.

    It provides the additional methods cfgSet() and configure().

    Additionally it uses `VirtualMailManager.cli.read_pass()` for for the
    interactive password dialog.
    """

    __slots__ = ()  # nothing additional, also no __dict__/__weakref__

    def __init__(self):
        """Creates a new CliHandler instance.

        Throws a NotRootError if your uid is greater 0.
        """
        # Overwrite the parent CTor partly, we use the CliConfig class
        # and add some command line checks.
        skip_some_checks = os.sys.argv[1] in ('cf', 'configure', 'h', 'help',
                                              'v', 'version')
        super(CliHandler, self).__init__(skip_some_checks)

        self._cfg = Cfg(self._cfg_fname)
        self._cfg.load()

    def cfg_set(self, option, value):
        """Set a new value for the given option."""
        return self._cfg.set(option, value)

    def configure(self, section=None):
        """Starts the interactive configuration.

        Configures in interactive mode options in the given ``section``.
        If no section is given (default) all options from all sections
        will be prompted.
        """
        if section is None:
            self._cfg.configure(self._cfg.sections())
        elif self._cfg.has_section(section):
            self._cfg.configure([section])
        else:
            raise VMMError(_(u"Invalid section: '%s'") % section,
                           INVALID_SECTION)

    def user_add(self, emailaddress, password=None):
        """Override the parent user_add() - add the interactive password
        dialog."""
        acc = self._get_account(emailaddress)
        if acc:
            raise VMMError(_(u"The account '%s' already exists.") %
                           acc.address, ACCOUNT_EXISTS)
        if password is None:
            password = read_pass()
        acc.set_password(password)
        acc.save()
        self._make_account_dirs(acc)

    def user_password(self, emailaddress, password=None):
        """Override the parent user_password() - add the interactive
        password dialog."""
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, NO_SUCH_ACCOUNT)
        if not isinstance(password, basestring) or not password:
            password = read_pass()
        acc.modify('password', password)

del _
