# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.cli.main
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's command line interface.
"""

from configparser import NoOptionError, NoSectionError
from gettext import gettext as _

from vmm import errors
from vmm.config import BadOptionError, ConfigValueError
from vmm.cli import w_err
from vmm.cli.handler import CliHandler
from vmm.constants import (
    EX_MISSING_ARGS,
    EX_SUCCESS,
    EX_USER_INTERRUPT,
    INVALID_ARGUMENT,
)
from vmm.cli.subcommands import RunContext, setup_parser


def _get_handler():
    """Try to get a CliHandler. Exit the program when an error occurs."""
    try:
        handler = CliHandler()
    except (
        errors.NotRootError,
        errors.PermissionError,
        errors.VMMError,
        errors.ConfigError,
    ) as err:
        w_err(err.code, _("Error: %s") % err.msg)
    else:
        handler.cfg_install()
        return handler


def run(argv):
    parser = setup_parser()
    if len(argv) < 2:
        parser.print_usage()
        parser.exit(
            status=EX_MISSING_ARGS,
            message=_("You must specify a subcommand at least.") + "\n",
        )
    args = parser.parse_args()
    handler = _get_handler()
    run_ctx = RunContext(args, handler)
    try:
        args.func(run_ctx)
    except (EOFError, KeyboardInterrupt):
        # TP: We have to cry, because root has killed/interrupted vmm
        # with Ctrl+C or Ctrl+D.
        w_err(EX_USER_INTERRUPT, "", _("Ouch!"), "")
    except errors.VMMError as err:
        if handler.has_warnings():
            w_err(0, _("Warnings:"), *handler.get_warnings())
        w_err(err.code, _("Error: %s") % err.msg)
    except (BadOptionError, ConfigValueError) as err:
        w_err(INVALID_ARGUMENT, _("Error: %s") % err)
    except NoSectionError as err:
        w_err(INVALID_ARGUMENT, _("Error: Unknown section: '%s'") % err.section)
    except NoOptionError as err:
        w_err(
            INVALID_ARGUMENT,
            _("Error: No option '%(option)s' in section: '%(section)s'")
            % {"option": err.option, "section": err.section},
        )
    if handler.has_warnings():
        w_err(0, _("Warnings:"), *handler.get_warnings())
    return EX_SUCCESS
