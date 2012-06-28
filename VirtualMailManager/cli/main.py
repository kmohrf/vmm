# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2012, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.cli.main
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    VirtualMailManager's command line interface.
"""

from ConfigParser import NoOptionError, NoSectionError

from VirtualMailManager import ENCODING, errors
from VirtualMailManager.config import BadOptionError, ConfigValueError
from VirtualMailManager.cli import w_err
from VirtualMailManager.cli.handler import CliHandler
from VirtualMailManager.constants import DATABASE_ERROR, EX_MISSING_ARGS, \
     EX_SUCCESS, EX_UNKNOWN_COMMAND, EX_USER_INTERRUPT, INVALID_ARGUMENT
from VirtualMailManager.cli.subcommands import RunContext, cmd_map, \
     update_cmd_map, usage


_ = lambda msg: msg


def _get_handler():
    """Try to get a CliHandler. Exit the program when an error occurs."""
    try:
        handler = CliHandler()
    except (errors.NotRootError, errors.PermissionError, errors.VMMError,
            errors.ConfigError), err:
        w_err(err.code, _(u'Error: %s') % err.msg)
    else:
        handler.cfg_install()
        return handler


def run(argv):
    update_cmd_map()
    if len(argv) < 2:
        usage(EX_MISSING_ARGS, _(u"You must specify a subcommand at least."))

    sub_cmd = argv[1].lower()
    if sub_cmd in cmd_map:
        cmd_func = cmd_map[sub_cmd].func
    else:
        for cmd in cmd_map.itervalues():
            if cmd.alias == sub_cmd:
                cmd_func = cmd.func
                sub_cmd = cmd.name
                break
        else:
            usage(EX_UNKNOWN_COMMAND, _(u"Unknown subcommand: '%s'") % sub_cmd)

    handler = _get_handler()
    run_ctx = RunContext(argv, handler, sub_cmd)
    try:
        cmd_func(run_ctx)
    except (EOFError, KeyboardInterrupt):
        # TP: We have to cry, because root has killed/interrupted vmm
        # with Ctrl+C or Ctrl+D.
        w_err(EX_USER_INTERRUPT, '', _(u'Ouch!'), '')
    except errors.VMMError, err:
        if err.code != DATABASE_ERROR:
            w_err(err.code, _(u'Error: %s') % err.msg)
        w_err(err.code, unicode(err.msg, ENCODING, 'replace'))
    except (BadOptionError, ConfigValueError), err:
        w_err(INVALID_ARGUMENT, _(u'Error: %s') % err)
    except NoSectionError, err:
        w_err(INVALID_ARGUMENT,
              _(u"Error: Unknown section: '%s'") % err.section)
    except NoOptionError, err:
        w_err(INVALID_ARGUMENT,
              _(u"Error: No option '%(option)s' in section: '%(section)s'") %
              {'option': err.option, 'section': err.section})
    if handler.has_warnings():
        w_err(0, _(u'Warnings:'), *handler.get_warnings())
    return EX_SUCCESS

del _
