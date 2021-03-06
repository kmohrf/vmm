# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.cli.handler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A derived Handler class with a few changes/additions for cli use.
"""

import os
from gettext import gettext as _

from vmm.errors import VMMError
from vmm.handler import Handler
from vmm.cli import read_pass
from vmm.cli.config import CliConfig as Cfg
from vmm.constants import ACCOUNT_EXISTS, INVALID_SECTION, NO_SUCH_ACCOUNT, TYPE_ACCOUNT
from vmm.password import randompw, verify_scheme


class CliHandler(Handler):
    """This class uses a `CliConfig` for configuration stuff, instead of
    the non-interactive `Config` class.

    It provides the additional methods cfgSet() and configure().

    Additionally it uses `vmm.cli.read_pass()` for for the
    interactive password dialog.
    """

    __slots__ = ()  # nothing additional, also no __dict__/__weakref__

    def __init__(self):
        """Creates a new CliHandler instance.

        Throws a NotRootError if your uid is greater 0.
        """
        # Overwrite the parent CTor partly, we use the CliConfig class
        # and add some command line checks.
        skip_some_checks = os.sys.argv[1] in ("cf", "configure", "cs", "configset")
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
            raise VMMError(_("Invalid section: '%s'") % section, INVALID_SECTION)

    def user_add(self, emailaddress, password=None, note=None):
        """Override the parent user_add() - add the interactive password
        dialog.

        Returns the generated password, if account.random_password == True.
        """
        acc = self._get_account(emailaddress)
        if acc:
            raise VMMError(
                _("The account '%s' already exists.") % acc.address, ACCOUNT_EXISTS
            )
        self._is_other_address(acc.address, TYPE_ACCOUNT)
        should_create_random_password = self._cfg.dget("account.random_password")
        if password is None:
            if should_create_random_password:
                password = randompw(self._cfg.dget("account.password_length"))
            else:
                password = read_pass()
        acc.set_password(password)
        if note:
            acc.set_note(note)
        acc.save()
        self._make_account_dirs(acc)
        return password if should_create_random_password else None

    def user_password(self, emailaddress, password=None, scheme=None):
        """Override the parent user_password() - add the interactive
        password dialog."""
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(
                _("The account '%s' does not exist.") % acc.address, NO_SUCH_ACCOUNT
            )
        if scheme:
            scheme, encoding = verify_scheme(scheme)
            if encoding:
                scheme = "%s.%s" % (scheme, encoding)
        if not isinstance(password, str) or not password:
            password = read_pass()
        acc.update_password(password, scheme)
