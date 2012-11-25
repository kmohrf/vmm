# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2012, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.cli.subcommands
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    VirtualMailManager's cli subcommands.
"""

import locale
import os

from textwrap import TextWrapper
from time import strftime, strptime

from VirtualMailManager import ENCODING
from VirtualMailManager.cli import get_winsize, prog, w_err, w_std
from VirtualMailManager.cli.clihelp import help_msgs
from VirtualMailManager.common import human_size, size_in_bytes, \
     version_str, format_domain_default
from VirtualMailManager.constants import __copyright__, __date__, \
     __version__, ACCOUNT_EXISTS, ALIAS_EXISTS, ALIASDOMAIN_ISDOMAIN, \
     DOMAIN_ALIAS_EXISTS, INVALID_ARGUMENT, EX_MISSING_ARGS, \
     RELOCATED_EXISTS, TYPE_ACCOUNT, TYPE_ALIAS, TYPE_RELOCATED
from VirtualMailManager.errors import VMMError
from VirtualMailManager.password import list_schemes
from VirtualMailManager.serviceset import SERVICES

__all__ = (
    'Command', 'RunContext', 'cmd_map', 'usage', 'alias_add', 'alias_delete',
    'alias_info', 'aliasdomain_add', 'aliasdomain_delete', 'aliasdomain_info',
    'aliasdomain_switch', 'catchall_add', 'catchall_info', 'catchall_delete',
    'config_get', 'config_set', 'configure',
    'domain_add', 'domain_delete',  'domain_info', 'domain_quota',
    'domain_services', 'domain_transport', 'domain_note', 'get_user', 'help_',
    'list_domains', 'list_pwschemes', 'list_users', 'list_aliases',
    'list_relocated', 'list_addresses', 'relocated_add', 'relocated_delete',
    'relocated_info', 'user_add', 'user_delete', 'user_info', 'user_name',
    'user_password', 'user_quota', 'user_services', 'user_transport',
    'user_note', 'version',
)

_ = lambda msg: msg
txt_wrpr = TextWrapper(width=get_winsize()[1] - 1)
cmd_map = {}


class Command(object):
    """Container class for command information."""
    __slots__ = ('name', 'alias', 'func', 'args', 'descr')
    FMT_HLP_USAGE = """
usage: %(prog)s %(name)s %(args)s
       %(prog)s %(alias)s %(args)s
"""

    def __init__(self, name, alias, func, args, descr):
        """Create a new Command instance.

        Arguments:

        `name` : str
          the command name, e.g. ``addalias``
        `alias` : str
          the command's short alias, e.g. ``aa``
        `func` : callable
          the function to handle the command
        `args` : str
          argument placeholders, e.g. ``aliasaddress``
        `descr` : str
          short description of the command
        """
        self.name = name
        self.alias = alias
        self.func = func
        self.args = args
        self.descr = descr

    @property
    def usage(self):
        """the command's usage info."""
        return '%s %s %s' % (prog, self.name, self.args)

    def help_(self):
        """Print the Command's help message to stdout."""
        old_ii = txt_wrpr.initial_indent
        old_si = txt_wrpr.subsequent_indent

        txt_wrpr.subsequent_indent = (len(self.name) + 2) * ' '
        w_std(txt_wrpr.fill('%s: %s' % (self.name, self.descr)))

        info = Command.FMT_HLP_USAGE % dict(alias=self.alias, args=self.args,
                                            name=self.name, prog=prog)
        w_std(info)

        txt_wrpr.initial_indent = txt_wrpr.subsequent_indent = ' '
        try:
            [w_std(txt_wrpr.fill(_(para)) + '\n') for para
                    in help_msgs[self.name]]
        except KeyError:
            w_err(1, _("Subcommand '%s' is not yet documented." % self.name),
                  'see also: vmm(1)')


class RunContext(object):
    """Contains all information necessary to run a subcommand."""
    __slots__ = ('argc', 'args', 'cget', 'hdlr', 'scmd')
    plan_a_b = _('Plan A failed ... trying Plan B: %(subcommand)s %(object)s')

    def __init__(self, argv, handler, command):
        """Create a new RunContext"""
        self.argc = len(argv)
        self.args = argv[:]  # will be moved to argparse
        self.cget = handler.cfg_dget
        self.hdlr = handler
        self.scmd = command


def alias_add(ctx):
    """create a new alias e-mail address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias address and destination.'),
              ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing destination address.'), ctx.scmd)
    ctx.hdlr.alias_add(ctx.args[2].lower(), *ctx.args[3:])


def alias_delete(ctx):
    """delete the specified alias e-mail address or one of its destinations"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias address.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.alias_delete(ctx.args[2].lower())
    else:
        ctx.hdlr.alias_delete(ctx.args[2].lower(), ctx.args[3:])


def alias_info(ctx):
    """show the destination(s) of the specified alias"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias address.'), ctx.scmd)
    address = ctx.args[2].lower()
    try:
        _print_aliase_info(address, ctx.hdlr.alias_info(address))
    except VMMError as err:
        if err.code is ACCOUNT_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'userinfo',
                  'object': address})
            ctx.scmd = ctx.args[1] = 'userinfo'
            user_info(ctx)
        elif err.code is RELOCATED_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'relocatedinfo',
                  'object': address})
            ctx.scmd = ctx.args[1] = 'relocatedinfo'
            relocated_info(ctx)
        else:
            raise


def aliasdomain_add(ctx):
    """create a new alias for an existing domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias domain name and destination '
                                 'domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing destination domain name.'),
              ctx.scmd)
    ctx.hdlr.aliasdomain_add(ctx.args[2].lower(), ctx.args[3].lower())


def aliasdomain_delete(ctx):
    """delete the specified alias domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias domain name.'), ctx.scmd)
    ctx.hdlr.aliasdomain_delete(ctx.args[2].lower())


def aliasdomain_info(ctx):
    """show the destination of the given alias domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias domain name.'), ctx.scmd)
    try:
        _print_aliasdomain_info(ctx.hdlr.aliasdomain_info(ctx.args[2].lower()))
    except VMMError as err:
        if err.code is ALIASDOMAIN_ISDOMAIN:
            w_err(0, ctx.plan_a_b % {'subcommand': 'domaininfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'domaininfo'
            domain_info(ctx)
        else:
            raise


def aliasdomain_switch(ctx):
    """assign the given alias domain to an other domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing alias domain name and destination '
                                 'domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing destination domain name.'),
              ctx.scmd)
    ctx.hdlr.aliasdomain_switch(ctx.args[2].lower(), ctx.args[3].lower())


def catchall_add(ctx):
    """create a new catchall alias e-mail address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain and destination.'),
              ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing destination address.'), ctx.scmd)
    ctx.hdlr.catchall_add(ctx.args[2].lower(), *ctx.args[3:])


def catchall_delete(ctx):
    """delete the specified destination or all of the catchall destination"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.catchall_delete(ctx.args[2].lower())
    else:
        ctx.hdlr.catchall_delete(ctx.args[2].lower(), ctx.args[3:])


def catchall_info(ctx):
    """show the catchall destination(s) of the specified domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'), ctx.scmd)
    address = ctx.args[2].lower()
    _print_catchall_info(address, ctx.hdlr.catchall_info(address))


def config_get(ctx):
    """show the actual value of the configuration option"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _("Missing option name."), ctx.scmd)

    noop = lambda option: option
    opt_formater = {
        'misc.dovecot_version': version_str,
        'domain.quota_bytes': human_size,
    }

    option = ctx.args[2].lower()
    w_std('%s = %s' % (option, opt_formater.get(option,
                       noop)(ctx.cget(option))))


def config_set(ctx):
    """set a new value for the configuration option"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing option and new value.'), ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing new configuration value.'),
              ctx.scmd)
    ctx.hdlr.cfg_set(ctx.args[2].lower(), ctx.args[3])


def configure(ctx):
    """start interactive configuration mode"""
    if ctx.argc < 3:
        ctx.hdlr.configure()
    else:
        ctx.hdlr.configure(ctx.args[2].lower())


def domain_add(ctx):
    """create a new domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.domain_add(ctx.args[2].lower())
    else:
        ctx.hdlr.domain_add(ctx.args[2].lower(), ctx.args[3])
    if ctx.cget('domain.auto_postmaster'):
        w_std(_('Creating account for postmaster@%s') % ctx.args[2].lower())
        ctx.scmd = 'useradd'
        ctx.args = [prog, ctx.scmd, 'postmaster@' + ctx.args[2].lower()]
        ctx.argc = 3
        user_add(ctx)


def domain_delete(ctx):
    """delete the given domain and all its alias domains"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.domain_delete(ctx.args[2].lower())
    elif ctx.args[3].lower() == 'force':
        ctx.hdlr.domain_delete(ctx.args[2].lower(), True)
    else:
        usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % ctx.args[3],
              ctx.scmd)


def domain_info(ctx):
    """display information about the given domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'), ctx.scmd)
    if ctx.argc < 4:
        details = None
    else:
        details = ctx.args[3].lower()
        if details not in ('accounts', 'aliasdomains', 'aliases', 'full',
                           'relocated', 'catchall'):
            usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % details,
                  ctx.scmd)
    try:
        info = ctx.hdlr.domain_info(ctx.args[2].lower(), details)
    except VMMError as err:
        if err.code is DOMAIN_ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'aliasdomaininfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'aliasdomaininfo'
            aliasdomain_info(ctx)
        else:
            raise
    else:
        q_limit = 'Storage: %(bytes)s; Messages: %(messages)s'
        if not details:
            info['bytes'] = human_size(info['bytes'])
            info['messages'] = locale.format('%d', info['messages'], True)
            info['quota limit/user'] = q_limit % info
            _print_info(ctx, info, _('Domain'))
        else:
            info[0]['bytes'] = human_size(info[0]['bytes'])
            info[0]['messages'] = locale.format('%d', info[0]['messages'],
                                                True).decode(ENCODING,
                                                             'replace')
            info[0]['quota limit/user'] = q_limit % info[0]
            _print_info(ctx, info[0], _('Domain'))
            if details == 'accounts':
                _print_list(info[1], _('accounts'))
            elif details == 'aliasdomains':
                _print_list(info[1], _('alias domains'))
            elif details == 'aliases':
                _print_list(info[1], _('aliases'))
            elif details == 'relocated':
                _print_list(info[1], _('relocated users'))
            elif details == 'catchall':
                _print_list(info[1], _('catch-all destinations'))
            else:
                _print_list(info[1], _('alias domains'))
                _print_list(info[2], _('accounts'))
                _print_list(info[3], _('aliases'))
                _print_list(info[4], _('relocated users'))
                _print_list(info[5], _('catch-all destinations'))


def domain_quota(ctx):
    """update the quota limit of the specified domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name and storage value.'),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing storage value.'), ctx.scmd)
    messages = 0
    force = None
    try:
        bytes_ = size_in_bytes(ctx.args[3])
    except (ValueError, TypeError):
        usage(INVALID_ARGUMENT, _("Invalid storage value: '%s'") %
              ctx.args[3], ctx.scmd)
    if ctx.argc < 5:
        pass
    elif ctx.argc < 6:
        try:
            messages = int(ctx.args[4])
        except ValueError:
            if ctx.args[4].lower() != 'force':
                usage(INVALID_ARGUMENT,
                      _("Neither a valid number of messages nor the keyword "
                        "'force': '%s'") % ctx.args[4], ctx.scmd)
            force = 'force'
    else:
        try:
            messages = int(ctx.args[4])
        except ValueError:
            usage(INVALID_ARGUMENT,
                  _("Not a valid number of messages: '%s'") % ctx.args[4],
                  ctx.scmd)
        if ctx.args[5].lower() != 'force':
            usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % ctx.args[5],
                  ctx.scmd)
        force = 'force'
    ctx.hdlr.domain_quotalimit(ctx.args[2].lower(), bytes_, messages, force)


def domain_services(ctx):
    """allow all named service and block the uncredited."""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'), ctx.scmd)
    services = []
    force = False
    if ctx.argc is 3:
        pass
    elif ctx.argc is 4:
        arg = ctx.args[3].lower()
        if arg in SERVICES:
            services.append(arg)
        elif arg == 'force':
            force = True
        else:
            usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % arg,
                  ctx.scmd)
    else:
        services.extend([service.lower() for service in ctx.args[3:-1]])
        arg = ctx.args[-1].lower()
        if arg == 'force':
            force = True
        else:
            services.append(arg)
        unknown = [service for service in services if service not in SERVICES]
        if unknown:
            usage(INVALID_ARGUMENT, _('Invalid service arguments: %s') %
                  ' '.join(unknown), ctx.scmd)
    ctx.hdlr.domain_services(ctx.args[2].lower(), (None, 'force')[force],
                             *services)


def domain_transport(ctx):
    """update the transport of the specified domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name and new transport.'),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing new transport.'), ctx.scmd)
    if ctx.argc < 5:
        ctx.hdlr.domain_transport(ctx.args[2].lower(), ctx.args[3])
    else:
        force = ctx.args[4].lower()
        if force != 'force':
            usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % force,
                  ctx.scmd)
        ctx.hdlr.domain_transport(ctx.args[2].lower(), ctx.args[3], force)


def domain_note(ctx):
    """update the note of the given domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing domain name.'),
              ctx.scmd)
    elif ctx.argc < 4:
        note = None
    else:
        note = ' '.join(ctx.args[3:])
    ctx.hdlr.domain_note(ctx.args[2].lower(), note)


def get_user(ctx):
    """get the address of the user with the given UID"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing UID.'), ctx.scmd)
    _print_info(ctx, ctx.hdlr.user_by_uid(ctx.args[2]), _('Account'))


def help_(ctx):
    """print help messages."""
    if ctx.argc > 2:
        hlptpc = ctx.args[2].lower()
        if hlptpc in cmd_map:
            topic = hlptpc
        else:
            for scmd in cmd_map.values():
                if scmd.alias == hlptpc:
                    topic = scmd.name
                    break
            else:
                usage(INVALID_ARGUMENT, _("Unknown help topic: '%s'") %
                      ctx.args[2], ctx.scmd)
        if topic != 'help':
            return cmd_map[topic].help_()

    old_ii = txt_wrpr.initial_indent
    old_si = txt_wrpr.subsequent_indent
    txt_wrpr.initial_indent = ' '
    # len(max(_overview.iterkeys(), key=len)) #Py25
    txt_wrpr.subsequent_indent = 20 * ' '
    order = sorted(list(cmd_map.keys()))

    w_std(_('List of available subcommands:') + '\n')
    for key in order:
        w_std('\n'.join(txt_wrpr.wrap('%-18s %s' % (key, cmd_map[key].descr))))

    txt_wrpr.initial_indent = old_ii
    txt_wrpr.subsequent_indent = old_si
    txt_wrpr.initial_indent = ''


def list_domains(ctx):
    """list all domains / search domains by pattern"""
    matching = ctx.argc > 2
    if matching:
        gids, domains = ctx.hdlr.domain_list(ctx.args[2].lower())
    else:
        gids, domains = ctx.hdlr.domain_list()
    _print_domain_list(gids, domains, matching)


def list_pwschemes(ctx_unused):
    """Prints all usable password schemes and password encoding suffixes."""
    keys = (_('Usable password schemes'), _('Usable encoding suffixes'))
    old_ii, old_si = txt_wrpr.initial_indent, txt_wrpr.subsequent_indent
    txt_wrpr.initial_indent = txt_wrpr.subsequent_indent = '\t'
    txt_wrpr.width = txt_wrpr.width - 8

    for key, value in zip(keys, list_schemes()):
        w_std(key, len(key) * '-')
        w_std('\n'.join(txt_wrpr.wrap(' '.join(value))), '')

    txt_wrpr.initial_indent, txt_wrpr.subsequent_indent = old_ii, old_si
    txt_wrpr.width = txt_wrpr.width + 8


def list_addresses(ctx, limit=None):
    """List all addresses / search addresses by pattern. The output can be
    limited with TYPE_ACCOUNT, TYPE_ALIAS and TYPE_RELOCATED, which can be
    bitwise ORed as a combination. Not specifying a limit is the same as
    combining all three."""
    if limit is None:
        limit = TYPE_ACCOUNT | TYPE_ALIAS | TYPE_RELOCATED
    matching = ctx.argc > 2
    if matching:
        gids, addresses = ctx.hdlr.address_list(limit, ctx.args[2].lower())
    else:
        gids, addresses = ctx.hdlr.address_list(limit)
    _print_address_list(limit, gids, addresses, matching)


def list_users(ctx):
    """list all user accounts / search user accounts by pattern"""
    return list_addresses(ctx, TYPE_ACCOUNT)


def list_aliases(ctx):
    """list all aliases / search aliases by pattern"""
    return list_addresses(ctx, TYPE_ALIAS)


def list_relocated(ctx):
    """list all relocated records / search relocated records by pattern"""
    return list_addresses(ctx, TYPE_RELOCATED)


def relocated_add(ctx):
    """create a new record for a relocated user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS,
              _('Missing relocated address and destination.'), ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing destination address.'), ctx.scmd)
    ctx.hdlr.relocated_add(ctx.args[2].lower(), ctx.args[3])


def relocated_delete(ctx):
    """delete the record of the relocated user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing relocated address.'), ctx.scmd)
    ctx.hdlr.relocated_delete(ctx.args[2].lower())


def relocated_info(ctx):
    """print information about a relocated user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing relocated address.'), ctx.scmd)
    relocated = ctx.args[2].lower()
    try:
        _print_relocated_info(addr=relocated,
                              dest=ctx.hdlr.relocated_info(relocated))
    except VMMError as err:
        if err.code is ACCOUNT_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'userinfo',
                  'object': relocated})
            ctx.scmd = ctx.args[1] = 'userinfoi'
            user_info(ctx)
        elif err.code is ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'aliasinfo',
                  'object': relocated})
            ctx.scmd = ctx.args[1] = 'aliasinfo'
            alias_info(ctx)
        else:
            raise


def user_add(ctx):
    """create a new e-mail user with the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        password = None
    else:
        password = ctx.args[3]
    gen_pass = ctx.hdlr.user_add(ctx.args[2].lower(), password)
    if ctx.argc < 4 and gen_pass:
        w_std(_("Generated password: %s") % gen_pass)


def user_delete(ctx):
    """delete the specified user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.user_delete(ctx.args[2].lower())
    elif ctx.args[3].lower() == 'force':
        ctx.hdlr.user_delete(ctx.args[2].lower(), True)
    else:
        usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % ctx.args[3],
              ctx.scmd)


def user_info(ctx):
    """display information about the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address.'), ctx.scmd)
    if ctx.argc < 4:
        details = None
    else:
        details = ctx.args[3].lower()
        if details not in ('aliases', 'du', 'full'):
            usage(INVALID_ARGUMENT, _("Invalid argument: '%s'") % details,
                  ctx.scmd)
    try:
        info = ctx.hdlr.user_info(ctx.args[2].lower(), details)
    except VMMError as err:
        if err.code is ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'aliasinfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'aliasinfo'
            alias_info(ctx)
        elif err.code is RELOCATED_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'relocatedinfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'relocatedinfo'
            relocated_info(ctx)
        else:
            raise
    else:
        if details in (None, 'du'):
            info['quota storage'] = _format_quota_usage(info['ql_bytes'],
                    info['uq_bytes'], True, info['ql_domaindefault'])
            info['quota messages'] = \
                _format_quota_usage(info['ql_messages'],
                                    info['uq_messages'],
                                    domaindefault=info['ql_domaindefault'])
            _print_info(ctx, info, _('Account'))
        else:
            info[0]['quota storage'] = _format_quota_usage(info[0]['ql_bytes'],
                    info[0]['uq_bytes'], True, info[0]['ql_domaindefault'])
            info[0]['quota messages'] = \
                _format_quota_usage(info[0]['ql_messages'],
                                    info[0]['uq_messages'],
                                    domaindefault=info[0]['ql_domaindefault'])
            _print_info(ctx, info[0], _('Account'))
            _print_list(info[1], _('alias addresses'))


def user_name(ctx):
    """set or update the real name for an address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _("Missing e-mail address and user's name."),
              ctx.scmd)
    elif ctx.argc < 4:
        name = None
    else:
        name = ctx.args[3]
    ctx.hdlr.user_name(ctx.args[2].lower(), name)


def user_password(ctx):
    """update the password for the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        password = None
    else:
        password = ctx.args[3]
    ctx.hdlr.user_password(ctx.args[2].lower(), password)


def user_note(ctx):
    """update the note of the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address.'),
              ctx.scmd)
    elif ctx.argc < 4:
        note = None
    else:
        note = ' '.join(ctx.args[3:])
    ctx.hdlr.user_note(ctx.args[2].lower(), note)


def user_quota(ctx):
    """update the quota limit for the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address and storage value.'),
              ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing storage value.'), ctx.scmd)
    if ctx.args[3] != 'domain':
        try:
            bytes_ = size_in_bytes(ctx.args[3])
        except (ValueError, TypeError):
            usage(INVALID_ARGUMENT, _("Invalid storage value: '%s'") %
                  ctx.args[3], ctx.scmd)
    else:
        bytes_ = ctx.args[3]
    if ctx.argc < 5:
        messages = 0
    else:
        try:
            messages = int(ctx.args[4])
        except ValueError:
            usage(INVALID_ARGUMENT,
                  _("Not a valid number of messages: '%s'") % ctx.args[4],
                  ctx.scmd)
    ctx.hdlr.user_quotalimit(ctx.args[2].lower(), bytes_, messages)


def user_services(ctx):
    """allow all named service and block the uncredited."""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address.'), ctx.scmd)
    services = []
    if ctx.argc >= 4:
        services.extend([service.lower() for service in ctx.args[3:]])
        unknown = [service for service in services if service not in SERVICES]
        if unknown and ctx.args[3] != 'domain':
            usage(INVALID_ARGUMENT, _('Invalid service arguments: %s') %
                  ' '.join(unknown), ctx.scmd)
    ctx.hdlr.user_services(ctx.args[2].lower(), *services)


def user_transport(ctx):
    """update the transport of the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _('Missing e-mail address and transport.'),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _('Missing transport.'), ctx.scmd)
    ctx.hdlr.user_transport(ctx.args[2].lower(), ctx.args[3])


def usage(errno, errmsg, subcommand=None):
    """print usage message for the given command or all commands.
    When errno > 0, sys,exit(errno) will interrupt the program.
    """
    if subcommand and subcommand in cmd_map:
        w_err(errno, _("Error: %s") % errmsg,
              _("usage: ") + cmd_map[subcommand].usage)

    # TP: Please adjust translated words like the original text.
    # (It's a table header.) Extract from usage text:
    # usage: vmm subcommand arguments
    #   short long
    #   subcommand                arguments
    #
    #   da    domainadd           fqdn [transport]
    #   dd    domaindelete        fqdn [force]
    u_head = _("""usage: %s subcommand arguments
  short long
  subcommand                arguments\n""") % prog
    order = sorted(list(cmd_map.keys()))
    w_err(0, u_head)
    for key in order:
        scmd = cmd_map[key]
        w_err(0, '  %-5s %-19s %s' % (scmd.alias, scmd.name, scmd.args))
    w_err(errno, '', _("Error: %s") % errmsg)


def version(ctx_unused):
    """Write version and copyright information to stdout."""
    w_std('%s, %s %s (%s %s)\nPython %s %s %s\n\n%s\n%s %s' % (prog,
    # TP: The words 'from', 'version' and 'on' are used in
    # the version information, e.g.:
    # vmm, version 0.5.2 (from 09/09/09)
    # Python 2.5.4 on FreeBSD
        _('version'), __version__, _('from'),
        strftime(locale.nl_langinfo(locale.D_FMT),
            strptime(__date__, '%Y-%m-%d')),
        os.sys.version.split()[0], _('on'), os.uname()[0],
        __copyright__, prog,
        _('is free software and comes with ABSOLUTELY NO WARRANTY.')))


def update_cmd_map():
    """Update the cmd_map, after gettext's _ was installed."""
    cmd = Command
    cmd_map.update({
    # Account commands
    'getuser': cmd('getuser', 'gu', get_user, 'uid',
                   _('get the address of the user with the given UID')),
    'useradd': cmd('useradd', 'ua', user_add, 'address [password]',
                   _('create a new e-mail user with the given address')),
    'userdelete': cmd('userdelete', 'ud', user_delete, 'address [force]',
                      _('delete the specified user')),
    'userinfo': cmd('userinfo', 'ui', user_info, 'address [details]',
                    _('display information about the given address')),
    'username': cmd('username', 'un', user_name, 'address [name]',
                    _('set, update or delete the real name for an address')),
    'userpassword': cmd('userpassword', 'up', user_password,
                        'address [password]',
                        _('update the password for the given address')),
    'userquota': cmd('userquota', 'uq', user_quota,
                     'address storage [messages] | address domain',
                     _('update the quota limit for the given address')),
    'userservices': cmd('userservices', 'us', user_services,
                        'address [service ...] | address domain',
                        _('enables the specified services and disables all '
                          'not specified services')),
    'usertransport': cmd('usertransport', 'ut', user_transport,
                         'address transport | address domain',
                         _('update the transport of the given address')),
    'usernote': cmd('usernote', 'uo', user_note, 'address [note]',
                    _('set, update or delete the note of the given address')),
    # Alias commands
    'aliasadd': cmd('aliasadd', 'aa', alias_add, 'address destination ...',
                    _('create a new alias e-mail address with one or more '
                      'destinations')),
    'aliasdelete': cmd('aliasdelete', 'ad', alias_delete,
                       'address [destination ...]',
                       _('delete the specified alias e-mail address or one '
                         'of its destinations')),
    'aliasinfo': cmd('aliasinfo', 'ai', alias_info, 'address',
                     _('show the destination(s) of the specified alias')),
    # AliasDomain commands
    'aliasdomainadd': cmd('aliasdomainadd', 'ada', aliasdomain_add,
                          'fqdn destination',
                          _('create a new alias for an existing domain')),
    'aliasdomaindelete': cmd('aliasdomaindelete', 'add', aliasdomain_delete,
                             'fqdn', _('delete the specified alias domain')),
    'aliasdomaininfo': cmd('aliasdomaininfo', 'adi', aliasdomain_info, 'fqdn',
                         _('show the destination of the given alias domain')),
    'aliasdomainswitch': cmd('aliasdomainswitch', 'ads', aliasdomain_switch,
                             'fqdn destination', _('assign the given alias '
                             'domain to an other domain')),
    # CatchallAlias commands
    'catchalladd': cmd('catchalladd', 'caa', catchall_add,
                       'fqdn destination ...',
                       _('add one or more catch-all destinations for a '
                         'domain')),
    'catchalldelete': cmd('catchalldelete', 'cad', catchall_delete,
                       'fqdn [destination ...]',
                       _('delete the specified catch-all destination or all '
                         'of a domain\'s destinations')),
    'catchallinfo': cmd('catchallinfo', 'cai', catchall_info, 'fqdn',
                        _('show the catch-all destination(s) of the '
                          'specified domain')),
    # Domain commands
    'domainadd': cmd('domainadd', 'da', domain_add, 'fqdn [transport]',
                     _('create a new domain')),
    'domaindelete': cmd('domaindelete', 'dd', domain_delete, 'fqdn [force]',
                      _('delete the given domain and all its alias domains')),
    'domaininfo': cmd('domaininfo', 'di', domain_info, 'fqdn [details]',
                      _('display information about the given domain')),
    'domainquota': cmd('domainquota', 'dq', domain_quota,
                       'fqdn storage [messages] [force]',
                       _('update the quota limit of the specified domain')),
    'domainservices': cmd('domainservices', 'ds', domain_services,
                          'fqdn [service ...] [force]',
                          _('enables the specified services and disables all '
                            'not specified services of the given domain')),
    'domaintransport': cmd('domaintransport', 'dt', domain_transport,
                           'fqdn transport [force]',
                           _('update the transport of the specified domain')),
    'domainnote': cmd('domainnote', 'do', domain_note, 'fqdn [note]',
                     _('set, update or delete the note of the given domain')),
    # List commands
    'listdomains': cmd('listdomains', 'ld', list_domains, '[pattern]',
                      _('list all domains or search for domains by pattern')),
    'listaddresses': cmd('listaddresses', 'll', list_addresses, '[pattern]',
                         _('list all addresses or search for addresses by '
                           'pattern')),
    'listusers': cmd('listusers', 'lu', list_users, '[pattern]',
                     _('list all user accounts or search for accounts by '
                       'pattern')),
    'listaliases': cmd('listaliases', 'la', list_aliases, '[pattern]',
                      _('list all aliases or search for aliases by pattern')),
    'listrelocated': cmd('listrelocated', 'lr', list_relocated, '[pattern]',
                         _('list all relocated users or search for relocated '
                           'users by pattern')),
    # Relocated commands
    'relocatedadd': cmd('relocatedadd', 'ra', relocated_add,
                        'address newaddress',
                        _('create a new record for a relocated user')),
    'relocateddelete': cmd('relocateddelete', 'rd', relocated_delete,
                           'address',
                           _('delete the record of the relocated user')),
    'relocatedinfo': cmd('relocatedinfo', 'ri', relocated_info, 'address',
                         _('print information about a relocated user')),
    # cli commands
    'configget': cmd('configget', 'cg', config_get, 'option',
                     _('show the actual value of the configuration option')),
    'configset': cmd('configset', 'cs', config_set, 'option value',
                      _('set a new value for the configuration option')),
    'configure': cmd('configure', 'cf', configure, '[section]',
                     _('start interactive configuration mode')),
    'listpwschemes': cmd('listpwschemes', 'lp', list_pwschemes, '',
                         _('lists all usable password schemes and password '
                           'encoding suffixes')),
    'help': cmd('help', 'h', help_, '[subcommand]',
                _('show a help overview or help for the given subcommand')),
    'version': cmd('version', 'v', version, '',
                   _('show version and copyright information')),
    })


def _get_order(ctx):
    """returns a tuple with (key, 1||0) tuples. Used by functions, which
    get a dict from the handler."""
    order = ()
    if ctx.scmd == 'domaininfo':
        order = (('domain name', 0), ('gid', 1), ('domain directory', 0),
                 ('quota limit/user', 0), ('active services', 0),
                 ('transport', 0), ('alias domains', 0), ('accounts', 0),
                 ('aliases', 0), ('relocated', 0), ('catch-all dests', 0))
    elif ctx.scmd == 'userinfo':
        if ctx.argc == 4 and ctx.args[3] != 'aliases' or \
           ctx.cget('account.disk_usage'):
            order = (('address', 0), ('name', 0), ('uid', 1), ('gid', 1),
                     ('home', 0), ('mail_location', 0),
                     ('quota storage', 0), ('quota messages', 0),
                     ('disk usage', 0), ('transport', 0), ('smtp', 1),
                     ('pop3', 1), ('imap', 1), ('sieve', 1))
        else:
            order = (('address', 0), ('name', 0), ('uid', 1), ('gid', 1),
                     ('home', 0), ('mail_location', 0),
                     ('quota storage', 0), ('quota messages', 0),
                     ('transport', 0), ('smtp', 1), ('pop3', 1),
                     ('imap', 1), ('sieve', 1))
    elif ctx.scmd == 'getuser':
        order = (('uid', 1), ('gid', 1), ('address', 0))
    return order


def _format_quota_usage(limit, used, human=False, domaindefault=False):
    """Put quota's limit / usage / percentage in a formatted string."""
    if human:
        q_usage = {
            'used': human_size(used),
            'limit': human_size(limit),
        }
    else:
        q_usage = {
            'used': locale.format('%d', used, True),
            'limit': locale.format('%d', limit, True),
        }
    if limit:
        q_usage['percent'] = locale.format('%6.2f', 100. / limit * used, True)
    else:
        q_usage['percent'] = locale.format('%6.2f', 0, True)
    fmt = format_domain_default if domaindefault else lambda s: s
    # TP: e.g.: [  0.00%] 21.09 KiB/1.00 GiB
    return fmt(_('[%(percent)s%%] %(used)s/%(limit)s') % q_usage)


def _print_info(ctx, info, title):
    """Print info dicts."""
    # TP: used in e.g. 'Domain information' or 'Account information'
    msg = '%s %s' % (title, _('information'))
    w_std(msg, '-' * len(msg))
    for key, upper in _get_order(ctx):
        if upper:
            w_std('\t%s: %s' % (key.upper().ljust(17, '.'), info[key]))
        else:
            w_std('\t%s: %s' % (key.title().ljust(17, '.'), info[key]))
    print()
    note = info.get('note')
    if note:
        _print_note(note + '\n')


def _print_note(note):
    msg = _('Note')
    w_std(msg, '-' * len(msg))
    old_ii = txt_wrpr.initial_indent
    old_si = txt_wrpr.subsequent_indent
    txt_wrpr.initial_indent = txt_wrpr.subsequent_indent = '\t'
    txt_wrpr.width -= 8
    for para in note.split('\n'):
        w_std(txt_wrpr.fill(para))
    txt_wrpr.width += 8
    txt_wrpr.subsequent_indent = old_si
    txt_wrpr.initial_indent = old_ii


def _print_list(alist, title):
    """Print a list."""
    # TP: used in e.g. 'Existing alias addresses' or 'Existing accounts'
    msg = '%s %s' % (_('Existing'), title)
    w_std(msg, '-' * len(msg))
    if alist:
        if title != _('alias domains'):
            w_std(*('\t%s' % item for item in alist))
        else:
            for domain in alist:
                if not domain.startswith('xn--'):
                    w_std('\t%s' % domain)
                else:
                    w_std('\t%s (%s)' % (domain, domain.decode('idna')))
        print()
    else:
        w_std(_('\tNone'), '')


def _print_aliase_info(alias, destinations):
    """Print the alias address and all its destinations"""
    title = _('Alias information')
    w_std(title, '-' * len(title))
    w_std(_('\tMail for %s will be redirected to:') % alias)
    w_std(*('\t     * %s' % dest for dest in destinations))
    print()


def _print_catchall_info(domain, destinations):
    """Print the catchall destinations of a domain"""
    title = _('Catch-all information')
    w_std(title, '-' * len(title))
    w_std(_('\tMail to unknown local-parts in domain %s will be sent to:')
          % domain)
    w_std(*('\t     * %s' % dest for dest in destinations))
    print()


def _print_relocated_info(**kwargs):
    """Print the old and new addresses of a relocated user."""
    title = _('Relocated information')
    w_std(title, '-' * len(title))
    w_std(_("\tUser '%(addr)s' has moved to '%(dest)s'") % kwargs, '')


def _format_domain(domain, main=True):
    """format (prefix/convert) the domain name."""
    if domain.startswith('xn--'):
        domain = '%s (%s)' % (domain, domain.decode('idna'))
    if main:
        return '\t[+] %s' % domain
    return '\t[-]     %s' % domain


def _print_domain_list(dids, domains, matching):
    """Print a list of (matching) domains/alias domains."""
    title = _('Matching domains') if matching else _('Existing domains')
    w_std(title, '-' * len(title))
    if domains:
        for did in dids:
            if domains[did][0] is not None:
                w_std(_format_domain(domains[did][0]))
            if len(domains[did]) > 1:
                w_std(*(_format_domain(a, False) for a in domains[did][1:]))
    else:
        w_std(_('\tNone'))
    print()


def _print_address_list(which, dids, addresses, matching):
    """Print a list of (matching) addresses."""
    _trans = {
        TYPE_ACCOUNT: _('user accounts'),
        TYPE_ALIAS: _('aliases'),
        TYPE_RELOCATED: _('relocated users'),
        TYPE_ACCOUNT | TYPE_ALIAS: _('user accounts and aliases'),
        TYPE_ACCOUNT | TYPE_RELOCATED: _('user accounts and relocated users'),
        TYPE_ALIAS | TYPE_RELOCATED: _('aliases and relocated users'),
        TYPE_ACCOUNT | TYPE_ALIAS | TYPE_RELOCATED: _('addresses'),
    }
    try:
        if matching:
            title = _('Matching %s') % _trans[which]
        else:
            title = _('Existing %s') % _trans[which]
        w_std(title, '-' * len(title))
    except KeyError:
        raise VMMError(_("Invalid address type for list: '%s'") % which,
                       INVALID_ARGUMENT)
    if addresses:
        if which & (which - 1) == 0:
            # only one type is requested, so no type indicator
            _trans = {TYPE_ACCOUNT: '', TYPE_ALIAS: '', TYPE_RELOCATED: ''}
        else:
            # TP: the letters 'u', 'a' and 'r' are abbreviations of user,
            # alias and relocated user
            _trans = {
                TYPE_ACCOUNT: _('u'),
                TYPE_ALIAS: _('a'),
                TYPE_RELOCATED: _('r'),
            }
        for did in dids:
            for addr, atype, aliasdomain in addresses[did]:
                if aliasdomain:
                    leader = '[%s-]' % _trans[atype]
                else:
                    leader = '[%s+]' % _trans[atype]
                w_std('\t%s %s' % (leader, addr))
    else:
        w_std(_('\tNone'))
    print()


def _print_aliasdomain_info(info):
    """Print alias domain information."""
    title = _('Alias domain information')
    for key in ('alias', 'domain'):
        if info[key].startswith('xn--'):
            info[key] = '%s (%s)' % (info[key], info[key].decode('idna'))
    w_std(title, '-' * len(title),
          _('\tThe alias domain %(alias)s belongs to:\n\t    * %(domain)s') %
          info, '')

del _
