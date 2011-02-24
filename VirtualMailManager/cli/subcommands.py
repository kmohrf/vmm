# -*- coding: UTF-8 -*-
# Copyright 2007 - 2011, Pascal Volk
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
from VirtualMailManager.account import SERVICES
from VirtualMailManager.cli import get_winsize, prog, w_err, w_std
from VirtualMailManager.common import human_size, size_in_bytes, version_str
from VirtualMailManager.constants import __copyright__, __date__, \
     __version__, ACCOUNT_EXISTS, ALIAS_EXISTS, ALIASDOMAIN_ISDOMAIN, \
     DOMAIN_ALIAS_EXISTS, INVALID_ARGUMENT, EX_MISSING_ARGS, RELOCATED_EXISTS
from VirtualMailManager.errors import VMMError

__all__ = (
    'Command', 'RunContext', 'cmd_map', 'usage', 'alias_add', 'alias_delete',
    'alias_info', 'aliasdomain_add', 'aliasdomain_delete', 'aliasdomain_info',
    'aliasdomain_switch', 'config_get', 'config_set', 'configure',
    'domain_add', 'domain_delete',  'domain_info', 'domain_quota',
    'domain_transport', 'get_user', 'help_', 'list_domains', 'relocated_add',
    'relocated_delete', 'relocated_info', 'user_add', 'user_delete',
    'user_disable', 'user_enable', 'user_info', 'user_name', 'user_password',
    'user_quota', 'user_transport', 'version',
)

_ = lambda msg: msg
txt_wrpr = TextWrapper(width=get_winsize()[1] - 1)


class Command(object):
    """Container class for command information."""
    __slots__ = ('name', 'alias', 'func', 'args', 'descr')

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
        return u'%s %s %s' % (prog, self.name, self.args)


class RunContext(object):
    """Contains all information necessary to run a subcommand."""
    __slots__ = ('argc', 'args', 'cget', 'hdlr', 'scmd')
    plan_a_b = _(u'Plan A failed ... trying Plan B: %(subcommand)s %(object)s')

    def __init__(self, argv, handler, command):
        """Create a new RunContext"""
        self.argc = len(argv)
        self.args = [unicode(arg, ENCODING) for arg in argv]
        self.cget = handler.cfg_dget
        self.hdlr = handler
        self.scmd = command


def alias_add(ctx):
    """create a new alias e-mail address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias address and destination.'),
              ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing destination address.'), ctx.scmd)
    ctx.hdlr.alias_add(ctx.args[2].lower(), *ctx.args[3:])


def alias_delete(ctx):
    """delete the specified alias e-mail address or one of its destinations"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias address.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.alias_delete(ctx.args[2].lower())
    else:
        ctx.hdlr.alias_delete(ctx.args[2].lower(), ctx.args[3])


def alias_info(ctx):
    """show the destination(s) of the specified alias"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias address.'), ctx.scmd)
    address = ctx.args[2].lower()
    try:
        _print_aliase_info(address, ctx.hdlr.alias_info(address))
    except VMMError, err:
        if err.code is ACCOUNT_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': u'userinfo',
                  'object': address})
            ctx.scmd = ctx.args[1] = 'userinfo'
            user_info(ctx)
        elif err.code is RELOCATED_EXISTS:
            w_std(0, ctx.plan_a_b % {'subcommand': u'relocatedinfo',
                  'object': address})
            ctx.scmd = ctx.args[1] = 'relocatedinfo'
            relocated_info(ctx)
        else:
            raise


def aliasdomain_add(ctx):
    """create a new alias for an existing domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias domain name and destination '
                                 u'domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing destination domain name.'),
              ctx.scmd)
    ctx.hdlr.aliasdomain_add(ctx.args[2].lower(), ctx.args[3].lower())


def aliasdomain_delete(ctx):
    """delete the specified alias domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias domain name.'), ctx.scmd)
    ctx.hdlr.aliasdomain_delete(ctx.args[2].lower())


def aliasdomain_info(ctx):
    """show the destination of the given alias domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias domain name.'), ctx.scmd)
    try:
        _print_aliasdomain_info(ctx.hdlr.aliasdomain_info(ctx.args[2].lower()))
    except VMMError, err:
        if err.code is ALIASDOMAIN_ISDOMAIN:
            w_err(0, ctx.plan_a_b % {'subcommand': u'domaininfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'domaininfo'
            domain_info(ctx)
        else:
            raise


def aliasdomain_switch(ctx):
    """assign the given alias domain to an other domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing alias domain name and destination '
                                 u'domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing destination domain name.'),
              ctx.scmd)
    ctx.hdlr.aliasdomain_switch(ctx.args[2].lower(), ctx.args[3].lower())


def config_get(ctx):
    """show the actual value of the configuration option"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u"Missing option name."), ctx.scmd)

    noop = lambda option: option
    opt_formater = {
        'misc.dovecot_version': version_str,
        'misc.quota_bytes': human_size,
    }

    option = ctx.args[2].lower()
    w_std('%s = %s' % (option, opt_formater.get(option,
                       noop)(ctx.cget(option))))


def config_set(ctx):
    """set a new value for the configuration option"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing option and new value.'), ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing new configuration value.'),
              ctx.scmd)
    ctx.hdlr.cfg_set(ctx.args[2].lower(), ctx.args[3])


def configure(ctx):
    """start interactive configuration modus"""
    if ctx.argc < 3:
        ctx.hdlr.configure()
    else:
        ctx.hdlr.configure(ctx.args[2].lower())


def domain_add(ctx):
    """create a new domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.domain_add(ctx.args[2].lower())
    else:
        ctx.hdlr.domain_add(ctx.args[2].lower(), ctx.args[3])
    if not ctx.cget('domain.auto_postmaster'):
        return
    ctx.scmd = 'useradd'
    ctx.args = [prog, ctx.scmd, u'postmaster@' + ctx.args[2].lower()]
    ctx.argc = 3
    user_add(ctx)


def domain_delete(ctx):
    """delete the given domain and all its alias domains"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing domain name.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.domain_delete(ctx.args[2].lower())
    elif ctx.args[3].lower() == 'force':
        ctx.hdlr.domain_delete(ctx.args[2].lower(), True)
    else:
        usage(INVALID_ARGUMENT, _(u"Invalid argument: '%s'") % ctx.args[3],
              ctx.scmd)


def domain_info(ctx):
    """display information about the given domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing domain name.'), ctx.scmd)
    if ctx.argc < 4:
        details = None
    else:
        details = ctx.args[3].lower()
        if details not in ('accounts', 'aliasdomains', 'aliases', 'full',
                           'relocated'):
            usage(INVALID_ARGUMENT, _(u"Invalid argument: '%s'") % details,
                  ctx.scmd)
    try:
        info = ctx.hdlr.domain_info(ctx.args[2].lower(), details)
    except VMMError, err:
        if err.code is DOMAIN_ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': u'aliasdomaininfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'aliasdomaininfo'
            aliasdomain_info(ctx)
        else:
            raise
    else:
        q_limit = u'Storage: %(bytes)s; Messages: %(messages)s'
        if not details:
            info['bytes'] = human_size(info['bytes'])
            info['messages'] = locale.format('%d', info['messages'], True)
            info['quota limit'] = q_limit % info
            _print_info(ctx, info, _(u'Domain'))
        else:
            info[0]['bytes'] = human_size(info[0]['bytes'])
            info[0]['messages'] = locale.format('%d', info[0]['messages'],
                                                True)
            info[0]['quota limit'] = q_limit % info[0]
            _print_info(ctx, info[0], _(u'Domain'))
            if details == u'accounts':
                _print_list(info[1], _(u'accounts'))
            elif details == u'aliasdomains':
                _print_list(info[1], _(u'alias domains'))
            elif details == u'aliases':
                _print_list(info[1], _(u'aliases'))
            elif details == u'relocated':
                _print_list(info[1], _(u'relocated users'))
            else:
                _print_list(info[1], _(u'alias domains'))
                _print_list(info[2], _(u'accounts'))
                _print_list(info[3], _(u'aliases'))
                _print_list(info[4], _(u'relocated users'))


def domain_quota(ctx):
    """update the quota limit of the specified domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing domain name and storage value.'),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing storage value.'), ctx.scmd)
    messages = 0
    force = None
    try:
        bytes_ = size_in_bytes(ctx.args[3])
    except (ValueError, TypeError):
        usage(INVALID_ARGUMENT, _(u"Invalid storage value: '%s'") %
              ctx.args[3], ctx.scmd)
    if ctx.argc < 5:
        pass
    elif ctx.argc < 6:
        try:
            messages = int(ctx.args[4])
        except ValueError:
            if ctx.args[4].lower() != 'force':
                usage(INVALID_ARGUMENT,
                      _(u"Neither a valid number of messages nor the keyword "
                        u"'force': '%s'") % ctx.args[4], ctx.scmd)
            force = 'force'
    else:
        try:
            messages = int(ctx.args[4])
        except ValueError:
            usage(INVALID_ARGUMENT,
                  _(u"Not a valid number of messages: '%s'") % ctx.args[4],
                  ctx.scmd)
        if ctx.args[5].lower() != 'force':
            usage(INVALID_ARGUMENT, _(u"Invalid argument: '%s'") % ctx.args[5],
                  ctx.scmd)
        force = 'force'
    ctx.hdlr.domain_quotalimit(ctx.args[2].lower(), bytes_, messages, force)


def domain_transport(ctx):
    """update the transport of the specified domain"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing domain name and new transport.'),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing new transport.'), ctx.scmd)
    if ctx.argc < 5:
        ctx.hdlr.domain_transport(ctx.args[2].lower(), ctx.args[3])
    else:
        force = ctx.args[4].lower()
        if force != 'force':
            usage(INVALID_ARGUMENT, _(u"Invalid argument: '%s'") % force,
                  ctx.scmd)
        ctx.hdlr.domain_transport(ctx.args[2].lower(), ctx.args[3], force)


def get_user(ctx):
    """get the address of the user with the given UID"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing UID.'), ctx.scmd)
    _print_info(ctx, ctx.hdlr.user_by_uid(ctx.args[2]), _(u'Account'))


def help_(ctx):
    """print help messages."""
    if ctx.argc > 2:
        hlptpc = ctx.args[2].lower()
        if hlptpc in cmd_map:
            topic = hlptpc
        else:
            for scmd in cmd_map.itervalues():
                if scmd.alias == hlptpc:
                    topic = scmd.name
                    break
            else:
                usage(INVALID_ARGUMENT, _(u"Unknown help topic: '%s'") %
                      ctx.args[2], ctx.scmd)
        # FIXME
        w_err(1, "'help %s' not yet implemented." % topic, 'see also: vmm(1)')

    old_ii = txt_wrpr.initial_indent
    old_si = txt_wrpr.subsequent_indent
    txt_wrpr.initial_indent = ' '
    # len(max(_overview.iterkeys(), key=len)) #Py25
    txt_wrpr.subsequent_indent = 20 * ' '
    order = cmd_map.keys()
    order.sort()

    w_std(_(u'List of available subcommands:') + '\n')
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


def relocated_add(ctx):
    """create a new record for a relocated user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS,
              _(u'Missing relocated address and destination.'), ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing destination address.'), ctx.scmd)
    ctx.hdlr.relocated_add(ctx.args[2].lower(), ctx.args[3])


def relocated_delete(ctx):
    """delete the record of the relocated user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing relocated address.'), ctx.scmd)
    ctx.hdlr.relocated_delete(ctx.args[2].lower())


def relocated_info(ctx):
    """print information about a relocated user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing relocated address.'), ctx.scmd)
    relocated = ctx.args[2].lower()
    try:
        _print_relocated_info(addr=relocated,
                              dest=ctx.hdlr.relocated_info(relocated))
    except VMMError, err:
        if err.code is ACCOUNT_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': u'userinfo',
                  'object': relocated})
            ctx.scmd = ctx.args[1] = 'userinfoi'
            user_info(ctx)
        elif err.code is ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': u'aliasinfo',
                  'object': relocated})
            ctx.scmd = ctx.args[1] = 'aliasinfo'
            alias_info(ctx)
        else:
            raise


def user_add(ctx):
    """create a new e-mail user with the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        password = None
    else:
        password = ctx.args[3]
    gen_pass = ctx.hdlr.user_add(ctx.args[2].lower(), password)
    if gen_pass:
        w_std(_(u"Generated password: %s") % gen_pass)


def user_delete(ctx):
    """delete the specified user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.user_delete(ctx.args[2].lower())
    elif ctx.args[3].lower() == 'force':
        ctx.hdlr.user_delete(ctx.args[2].lower(), True)
    else:
        usage(INVALID_ARGUMENT, _(u"Invalid argument: '%s'") % ctx.args[3],
              ctx.scmd)


def user_disable(ctx):
    """deactivate all/the given service(s) for a user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.user_disable(ctx.args[2].lower())
    else:
        services = [service.lower() for service in ctx.args[3:]]
        unknown = [service for service in services if service not in SERVICES]
        if unknown:
            usage(INVALID_ARGUMENT, _(u"Invalid service arguments: %s") %
                  ' '.join(unknown), ctx.scmd)
        ctx.hdlr.user_disable(ctx.args[2].lower(), services)


def user_enable(ctx):
    """activate all or the given service(s) for a user"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        ctx.hdlr.user_enable(ctx.args[2].lower())
    else:
        services = [service.lower() for service in ctx.args[3:]]
        unknown = [service for service in services if service not in SERVICES]
        if unknown:
            usage(INVALID_ARGUMENT, _(u"Invalid service arguments: %s") %
                  ' '.join(unknown), ctx.scmd)
        ctx.hdlr.user_enable(ctx.args[2].lower(), services)


def user_info(ctx):
    """display information about the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address.'), ctx.scmd)
    if ctx.argc < 4:
        details = None
    else:
        details = ctx.args[3].lower()
        if details not in ('aliases', 'du', 'full'):
            usage(INVALID_ARGUMENT, _(u"Invalid argument: '%s'") % details,
                  ctx.scmd)
    try:
        info = ctx.hdlr.user_info(ctx.args[2].lower(), details)
    except VMMError, err:
        if err.code is ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': u'aliasinfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'aliasinfo'
            alias_info(ctx)
        elif err.code is RELOCATED_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': u'relocatedinfo',
                  'object': ctx.args[2].lower()})
            ctx.scmd = ctx.args[1] = 'relocatedinfo'
            relocated_info(ctx)
        else:
            raise
    else:
        if details in (None, 'du'):
            info['quota storage'] = _format_quota_usage(info['ql_bytes'],
                    info['uq_bytes'], True)
            info['quota messages'] = _format_quota_usage(info['ql_messages'],
                    info['uq_messages'])
            _print_info(ctx, info, _(u'Account'))
        else:
            info[0]['quota storage'] = _format_quota_usage(info[0]['ql_bytes'],
                    info['uq_bytes'], True)
            info[0]['quota messages'] = _format_quota_usage(
                    info[0]['ql_messages'], info[0]['uq_messages'])
            _print_info(ctx, info[0], _(u'Account'))
            _print_list(info[1], _(u'alias addresses'))


def user_name(ctx):
    """set or update the real name for an address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u"Missing e-mail address and user's name."),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u"Missing user's name."), ctx.scmd)
    ctx.hdlr.user_name(ctx.args[2].lower(), ctx.args[3])


def user_password(ctx):
    """update the password for the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address.'), ctx.scmd)
    elif ctx.argc < 4:
        password = None
    else:
        password = ctx.args[3]
    ctx.hdlr.user_password(ctx.args[2].lower(), password)


def user_quota(ctx):
    """update the quota limit for the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address and storage value.'),
              ctx.scmd)
    elif ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing storage value.'), ctx.scmd)
    try:
        bytes_ = size_in_bytes(ctx.args[3])
    except (ValueError, TypeError):
        usage(INVALID_ARGUMENT, _(u"Invalid storage value: '%s'") %
              ctx.args[3], ctx.scmd)
    if ctx.argc < 5:
        messages = 0
    else:
        try:
            messages = int(ctx.args[4])
        except ValueError:
            usage(INVALID_ARGUMENT,
                  _(u"Not a valid number of messages: '%s'") % ctx.args[4],
                  ctx.scmd)
    ctx.hdlr.user_quotalimit(ctx.args[2].lower(), bytes_, messages)


def user_transport(ctx):
    """update the transport of the given address"""
    if ctx.argc < 3:
        usage(EX_MISSING_ARGS, _(u'Missing e-mail address and transport.'),
              ctx.scmd)
    if ctx.argc < 4:
        usage(EX_MISSING_ARGS, _(u'Missing transport.'), ctx.scmd)
    ctx.hdlr.user_transport(ctx.args[2].lower(), ctx.args[3])


def usage(errno, errmsg, subcommand=None):
    """print usage message for the given command or all commands.
    When errno > 0, sys,exit(errno) will interrupt the program.
    """
    if subcommand and subcommand in cmd_map:
        w_err(errno, _(u"Error: %s") % errmsg,
              _(u"usage: ") + cmd_map[subcommand].usage)

    # TP: Please adjust translated words like the original text.
    # (It's a table header.) Extract from usage text:
    # usage: vmm subcommand arguments
    #   short long
    #   subcommand                arguments
    #
    #   da    domainadd           fqdn [transport]
    #   dd    domaindelete        fqdn [force]
    u_head = _(u"""usage: %s subcommand arguments
  short long
  subcommand                arguments\n""") % prog
    order = cmd_map.keys()
    order.sort()
    w_err(0, u_head)
    for key in order:
        scmd = cmd_map[key]
        w_err(0, '  %-5s %-19s %s' % (scmd.alias, scmd.name, scmd.args))
    w_err(errno, '', _(u"Error: %s") % errmsg)


def version(ctx):
    """Write version and copyright information to stdout."""
    w_std('%s, %s %s (%s %s)\nPython %s %s %s\n\n%s\n%s %s' % (prog,
    # TP: The words 'from', 'version' and 'on' are used in
    # the version information, e.g.:
    # vmm, version 0.5.2 (from 09/09/09)
    # Python 2.5.4 on FreeBSD
        _(u'version'), __version__, _(u'from'),
        strftime(locale.nl_langinfo(locale.D_FMT),
            strptime(__date__, '%Y-%m-%d')).decode(ENCODING, 'replace'),
        os.sys.version.split()[0], _(u'on'), os.uname()[0],
        __copyright__, prog,
        _(u'is free software and comes with ABSOLUTELY NO WARRANTY.')))

cmd = Command
cmd_map = {  # {{{
    # Account commands
    'getuser': cmd('getuser', 'gu', get_user, _(u'uid'),
                   _(u'get the address of the user with the given UID')),
    'useradd': cmd('useradd', 'ua', user_add, _(u'address [password]'),
                   _(u'create a new e-mail user with the given address')),
    'userdelete': cmd('userdelete', 'ud', user_delete, _(u'address [force]'),
                      _(u'delete the specified user')),
    'userdisable': cmd('userdisable', 'u0', user_disable,
                       _(u'address [service ...]'),
                       _(u'deactivate all/the given service(s) for a user')),
    'userenable': cmd('userenable', 'u1', user_enable,
                      _(u'address [service ...]'),
                      _(u'activate all or the given service(s) for a user')),
    'userinfo': cmd('userinfo', 'ui', user_info, _(u'address [details]'),
                    _(u'display information about the given address')),
    'username': cmd('username', 'un', user_name, _(u'address name'),
                    _(u'set or update the real name for an address')),
    'userpassword': cmd('userpassword', 'up', user_password,
                        _(u'address [password]'),
                        _(u'update the password for the given address')),
    'userquota': cmd('userquota', 'uq', user_quota,
                     _(u'address storage [messages]'),
                     _(u'update the quota limit for the given address')),
    'usertransport': cmd('usertransport', 'ut', user_transport,
                         _(u'address transport'),
                         _(u'update the transport of the given address')),
    # Alias commands
    'aliasadd': cmd('aliasadd', 'aa', alias_add, _(u'address destination ...'),
                    _(u'create a new alias e-mail address with one or more '
                      u'destinations')),
    'aliasdelete': cmd('aliasdelete', 'ad', alias_delete,
                       _(u'address [destination]'),
                       _(u'delete the specified alias e-mail address or one '
                         u'of its destinations')),
    'aliasinfo': cmd('aliasinfo', 'ai', alias_info, _(u'address'),
                     _(u'show the destination(s) of the specified alias')),
    # AliasDomain commands
    'aliasdomainadd': cmd('aliasdomainadd', 'ada', aliasdomain_add,
                          _(u'fqdn destination'),
                          _(u'create a new alias for an existing domain')),
    'aliasdomaindelete': cmd('aliasdomaindelete', 'add', aliasdomain_delete,
                             _(u'fqdn'),
                             _(u'delete the specified alias domain')),
    'aliasdomaininfo': cmd('aliasdomaininfo', 'adi', aliasdomain_info,
                         _(u'fqdn'),
                         _(u'show the destination of the given alias domain')),
    'aliasdomainswitch': cmd('aliasdomainswitch', 'ads', aliasdomain_switch,
                       _(u'fqdn destination'),
                       _(u'assign the given alias domain to an other domain')),
    # Domain commands
    'domainadd': cmd('domainadd', 'da', domain_add, _(u'fqdn [transport]'),
                     _(u'create a new domain')),
    'domaindelete': cmd('domaindelete', 'dd', domain_delete,
                      _(u'fqdn [force]'),
                      _(u'delete the given domain and all its alias domains')),
    'domaininfo': cmd('domaininfo', 'di', domain_info, _(u'fqdn [details]'),
                      _(u'display information about the given domain')),
    'domainquota': cmd('domainquota', 'dq', domain_quota,
                       _(u'fqdn storage [messages] [force]'),
                       _(u'update the quota limit of the specified domain')),
    'domaintransport': cmd('domaintransport', 'dt', domain_transport,
                           _(u'fqdn transport [force]'),
                           _(u'update the transport of the specified domain')),
    'listdomains': cmd('listdomains', 'ld', list_domains, _(u'[pattern]'),
                       _(u'list all domains / search domains by pattern')),
    # Relocated commands
    'relocatedadd': cmd('relocatedadd', 'ra', relocated_add,
                        _(u'address newaddress'),
                        _(u'create a new record for a relocated user')),
    'relocateddelete': cmd('relocateddelete', 'rd', relocated_delete,
                           _(u'address'),
                           _(u'delete the record of the relocated user')),
    'relocatedinfo': cmd('relocatedinfo', 'ri', relocated_info, _('address'),
                         _(u'print information about a relocated user')),
    # cli commands
    'configget': cmd('configget', 'cg', config_get, _(u'option'),
                     _('show the actual value of the configuration option')),
    'configset': cmd('configset', 'cs', config_set, _('option value'),
                      _('set a new value for the configuration option')),
    'configure': cmd('configure', 'cf', configure, _(u'[section]'),
                     _(u'start interactive configuration modus')),
    'help': cmd('help', 'h', help_, _(u'[subcommand]'),
                _(u'show a help overview or help for the given subcommand')),
    'version': cmd('version', 'v', version, '',
                   _(u'show version and copyright information')),
}  # }}}


def _get_order(ctx):
    """returns a tuple with (key, 1||0) tuples. Used by functions, which
    get a dict from the handler."""
    order = ()
    if ctx.scmd == 'domaininfo':
        order = ((u'domainname', 0), (u'gid', 1), (u'transport', 0),
                 (u'domaindir', 0), (u'quota limit', 0), (u'aliasdomains', 0),
                 (u'accounts', 0), (u'aliases', 0), (u'relocated', 0))
    elif ctx.scmd == 'userinfo':
        dc12 = ctx.cget('misc.dovecot_version') >= 0x10200b02
        sieve = (u'managesieve', u'sieve')[dc12]
        if ctx.argc == 4 and ctx.args[3] != u'aliases' or \
           ctx.cget('account.disk_usage'):
            order = ((u'address', 0), (u'name', 0), (u'uid', 1), (u'gid', 1),
                     (u'home', 0), (u'mail_location', 0),
                     (u'quota storage', 0), (u'quota messages', 0),
                     (u'disk usage', 0), (u'transport', 0), (u'smtp', 1),
                     (u'pop3', 1), (u'imap', 1), (sieve, 1))
        else:
            order = ((u'address', 0), (u'name', 0), (u'uid', 1), (u'gid', 1),
                     (u'home', 0), (u'mail_location', 0),
                     (u'quota storage', 0), (u'quota messages', 0),
                     (u'transport', 0), (u'smtp', 1), (u'pop3', 1),
                     (u'imap', 1), (sieve, 1))
    elif ctx.scmd == 'getuser':
        order = ((u'uid', 1), (u'gid', 1), (u'address', 0))
    return order


def _format_quota_usage(limit, used, human=False):
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
    return _(u'[%(percent)s%%] %(used)s/%(limit)s') % q_usage


def _print_info(ctx, info, title):
    """Print info dicts."""
    # TP: used in e.g. 'Domain information' or 'Account information'
    msg = u'%s %s' % (title, _(u'information'))
    w_std(msg, u'-' * len(msg))
    for key, upper in _get_order(ctx):
        if upper:
            w_std(u'\t%s: %s' % (key.upper().ljust(15, u'.'), info[key]))
        else:
            w_std(u'\t%s: %s' % (key.title().ljust(15, u'.'), info[key]))
    print


def _print_list(alist, title):
    """Print a list."""
    # TP: used in e.g. 'Available alias addresses' or 'Available accounts'
    msg = u'%s %s' % (_(u'Available'), title)
    w_std(msg, u'-' * len(msg))
    if alist:
        if title != _(u'alias domains'):
            w_std(*(u'\t%s' % item for item in alist))
        else:
            for domain in alist:
                if not domain.startswith('xn--'):
                    w_std(u'\t%s' % domain)
                else:
                    w_std(u'\t%s (%s)' % (domain, domain.decode('idna')))
        print
    else:
        w_std(_(u'\tNone'), '')


def _print_aliase_info(alias, destinations):
    """Print the alias address and all its destinations"""
    title = _(u'Alias information')
    w_std(title, u'-' * len(title))
    w_std(_(u'\tMail for %s will be redirected to:') % alias)
    w_std(*(u'\t     * %s' % dest for dest in destinations))
    print


def _print_relocated_info(**kwargs):
    """Print the old and new addresses of a relocated user."""
    title = _(u'Relocated information')
    w_std(title, u'-' * len(title))
    w_std(_(u"\tUser '%(addr)s' has moved to '%(dest)s'") % kwargs, '')


def _format_domain(domain, main=True):
    """format (prefix/convert) the domain name."""
    if domain.startswith('xn--'):
        domain = u'%s (%s)' % (domain, domain.decode('idna'))
    if main:
        return u'\t[+] %s' % domain
    return u'\t[-]     %s' % domain


def _print_domain_list(dids, domains, matching):
    """Print a list of (matching) domains/alias domains."""
    if matching:
        title = _(u'Matching domains')
    else:
        title = _(u'Available domains')
    w_std(title, '-' * len(title))
    if domains:
        for did in dids:
            if domains[did][0] is not None:
                w_std(_format_domain(domains[did][0]))
            if len(domains[did]) > 1:
                w_std(*(_format_domain(a, False) for a in domains[did][1:]))
    else:
        w_std(_('\tNone'))
    print


def _print_aliasdomain_info(info):
    """Print alias domain information."""
    title = _(u'Alias domain information')
    for key in ('alias', 'domain'):
        if info[key].startswith('xn--'):
            info[key] = u'%s (%s)' % (info[key], info[key].decode('idna'))
    w_std(title, '-' * len(title),
          _('\tThe alias domain %(alias)s belongs to:\n\t    * %(domain)s') %
          info, '')

del _
