# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2013, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.cli.subcommands
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    VirtualMailManager's cli subcommands.
"""

import locale
import platform

from argparse import Action, ArgumentParser, ArgumentTypeError, \
     RawDescriptionHelpFormatter
from textwrap import TextWrapper
from time import strftime, strptime

from VirtualMailManager import ENCODING
from VirtualMailManager.cli import get_winsize, w_err, w_std
from VirtualMailManager.common import human_size, size_in_bytes, \
     version_str, format_domain_default
from VirtualMailManager.constants import __copyright__, __date__, \
     __version__, ACCOUNT_EXISTS, ALIAS_EXISTS, ALIASDOMAIN_ISDOMAIN, \
     DOMAIN_ALIAS_EXISTS, INVALID_ARGUMENT, RELOCATED_EXISTS, TYPE_ACCOUNT, \
     TYPE_ALIAS, TYPE_RELOCATED
from VirtualMailManager.errors import VMMError
from VirtualMailManager.password import list_schemes
from VirtualMailManager.serviceset import SERVICES

__all__ = (
    'RunContext', 'alias_add', 'alias_delete', 'alias_info', 'aliasdomain_add',
    'aliasdomain_delete', 'aliasdomain_info', 'aliasdomain_switch',
    'catchall_add', 'catchall_delete', 'catchall_info', 'config_get',
    'config_set', 'configure', 'domain_add', 'domain_delete', 'domain_info',
    'domain_note', 'domain_quota', 'domain_services', 'domain_transport',
    'get_user', 'list_addresses', 'list_aliases', 'list_domains',
    'list_pwschemes', 'list_relocated', 'list_users', 'relocated_add',
    'relocated_delete', 'relocated_info', 'setup_parser', 'user_add',
    'user_delete', 'user_info', 'user_name', 'user_note', 'user_password',
    'user_quota', 'user_services', 'user_transport',
)

WS_ROWS = get_winsize()[1] - 2

_ = lambda msg: msg
txt_wrpr = TextWrapper(width=WS_ROWS)


class RunContext(object):
    """Contains all information necessary to run a subcommand."""
    __slots__ = ('args', 'cget', 'hdlr')
    plan_a_b = _('Plan A failed ... trying Plan B: %(subcommand)s %(object)s')

    def __init__(self, args, handler):
        """Create a new RunContext"""
        self.args = args
        self.cget = handler.cfg_dget
        self.hdlr = handler


def alias_add(ctx):
    """create a new alias e-mail address"""
    ctx.hdlr.alias_add(ctx.args.address.lower(), *ctx.args.destination)


def alias_delete(ctx):
    """delete the specified alias e-mail address or one of its destinations"""
    destination = ctx.args.destination if ctx.args.destination else None
    ctx.hdlr.alias_delete(ctx.args.address.lower(), destination)


def alias_info(ctx):
    """show the destination(s) of the specified alias"""
    address = ctx.args.address.lower()
    try:
        _print_aliase_info(address, ctx.hdlr.alias_info(address))
    except VMMError as err:
        if err.code is ACCOUNT_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'userinfo',
                  'object': address})
            ctx.args.scmd = 'userinfo'
            ctx.args.details = None
            user_info(ctx)
        elif err.code is RELOCATED_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'relocatedinfo',
                  'object': address})
            ctx.args.scmd = 'relocatedinfo'
            relocated_info(ctx)
        else:
            raise


def aliasdomain_add(ctx):
    """create a new alias for an existing domain"""
    ctx.hdlr.aliasdomain_add(ctx.args.fqdn.lower(),
                             ctx.args.destination.lower())


def aliasdomain_delete(ctx):
    """delete the specified alias domain"""
    ctx.hdlr.aliasdomain_delete(ctx.args.fqdn.lower())


def aliasdomain_info(ctx):
    """show the destination of the given alias domain"""
    fqdn = ctx.args.fqdn.lower()
    try:
        _print_aliasdomain_info(ctx.hdlr.aliasdomain_info(fqdn))
    except VMMError as err:
        if err.code is ALIASDOMAIN_ISDOMAIN:
            w_err(0, ctx.plan_a_b % {'subcommand': 'domaininfo',
                                     'object': fqdn})
            ctx.args.scmd = 'domaininfo'
            domain_info(ctx)
        else:
            raise


def aliasdomain_switch(ctx):
    """assign the given alias domain to an other domain"""
    ctx.hdlr.aliasdomain_switch(ctx.args.fqdn.lower(),
                                ctx.args.destination.lower())


def catchall_add(ctx):
    """create a new catchall alias e-mail address"""
    ctx.hdlr.catchall_add(ctx.args.fqdn.lower(), *ctx.args.destination)


def catchall_delete(ctx):
    """delete the specified destination or all of the catchall destination"""
    destination = ctx.args.destination if ctx.args.destination else None
    ctx.hdlr.catchall_delete(ctx.args.fqdn.lower(), destination)


def catchall_info(ctx):
    """show the catchall destination(s) of the specified domain"""
    address = ctx.args.fqdn.lower()
    _print_catchall_info(address, ctx.hdlr.catchall_info(address))


def config_get(ctx):
    """show the actual value of the configuration option"""
    noop = lambda option: option
    opt_formater = {
        'misc.dovecot_version': version_str,
        'domain.quota_bytes': human_size,
    }

    option = ctx.args.option.lower()
    w_std('%s = %s' % (option, opt_formater.get(option,
                       noop)(ctx.cget(option))))


def config_set(ctx):
    """set a new value for the configuration option"""
    ctx.hdlr.cfg_set(ctx.args.option.lower(), ctx.args.value)


def configure(ctx):
    """start interactive configuration mode"""
    ctx.hdlr.configure(ctx.args.section)


def domain_add(ctx):
    """create a new domain"""
    fqdn = ctx.args.fqdn.lower()
    transport = ctx.args.transport.lower() if ctx.args.transport else None
    ctx.hdlr.domain_add(fqdn, transport)
    if ctx.cget('domain.auto_postmaster'):
        w_std(_('Creating account for postmaster@%s') % fqdn)
        ctx.args.scmd = 'useradd'
        ctx.args.address = 'postmaster@%s' % fqdn
        ctx.args.password = None
        user_add(ctx)


def domain_delete(ctx):
    """delete the given domain and all its alias domains"""
    ctx.hdlr.domain_delete(ctx.args.fqdn.lower(), ctx.args.force)


def domain_info(ctx):
    """display information about the given domain"""
    fqdn = ctx.args.fqdn.lower()
    details = ctx.args.details
    try:
        info = ctx.hdlr.domain_info(fqdn, details)
    except VMMError as err:
        if err.code is DOMAIN_ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'aliasdomaininfo',
                                     'object': fqdn})
            ctx.args.scmd = 'aliasdomaininfo'
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
                                                True)
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
    ctx.hdlr.domain_quotalimit(ctx.args.fqdn.lower(), ctx.args.storage,
                               ctx.args.messages, ctx.args.force)


def domain_services(ctx):
    """allow all named service and block the uncredited."""
    services = ctx.args.services if ctx.args.services else []
    ctx.hdlr.domain_services(ctx.args.fqdn.lower(), ctx.args.force, *services)


def domain_transport(ctx):
    """update the transport of the specified domain"""
    ctx.hdlr.domain_transport(ctx.args.fqdn.lower(),
                              ctx.args.transport.lower(), ctx.args.force)


def domain_note(ctx):
    """update the note of the given domain"""
    ctx.hdlr.domain_note(ctx.args.fqdn.lower(), ctx.args.note)


def get_user(ctx):
    """get the address of the user with the given UID"""
    _print_info(ctx, ctx.hdlr.user_by_uid(ctx.args.uid), _('Account'))


def list_domains(ctx):
    """list all domains / search domains by pattern"""
    matching = True if ctx.args.pattern else False
    pattern = ctx.args.pattern.lower() if matching else None
    gids, domains = ctx.hdlr.domain_list(pattern)
    _print_domain_list(gids, domains, matching)


def list_pwschemes(ctx_unused):
    """Prints all usable password schemes and password encoding suffixes."""
    keys = (_('Usable password schemes'), _('Usable encoding suffixes'))
    old_ii, old_si = txt_wrpr.initial_indent, txt_wrpr.subsequent_indent
    txt_wrpr.initial_indent = txt_wrpr.subsequent_indent = '\t'
    txt_wrpr.width = txt_wrpr.width - 8

    for key, value in zip(keys, list_schemes()):
        w_std(key, len(key) * '-')
        w_std('\n'.join(txt_wrpr.wrap(' '.join(sorted(value)))), '')

    txt_wrpr.initial_indent, txt_wrpr.subsequent_indent = old_ii, old_si
    txt_wrpr.width = txt_wrpr.width + 8


def list_addresses(ctx, limit=None):
    """List all addresses / search addresses by pattern. The output can be
    limited with TYPE_ACCOUNT, TYPE_ALIAS and TYPE_RELOCATED, which can be
    bitwise ORed as a combination. Not specifying a limit is the same as
    combining all three."""
    if limit is None:
        limit = TYPE_ACCOUNT | TYPE_ALIAS | TYPE_RELOCATED
    matching = True if ctx.args.pattern else False
    pattern = ctx.args.pattern.lower() if matching else None
    gids, addresses = ctx.hdlr.address_list(limit, pattern)
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
    ctx.hdlr.relocated_add(ctx.args.address.lower(), ctx.args.newaddress)


def relocated_delete(ctx):
    """delete the record of the relocated user"""
    ctx.hdlr.relocated_delete(ctx.args.address.lower())


def relocated_info(ctx):
    """print information about a relocated user"""
    relocated = ctx.args.address.lower()
    try:
        _print_relocated_info(addr=relocated,
                              dest=ctx.hdlr.relocated_info(relocated))
    except VMMError as err:
        if err.code is ACCOUNT_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'userinfo',
                  'object': relocated})
            ctx.args.scmd = 'userinfo'
            ctx.args.details = None
            user_info(ctx)
        elif err.code is ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'aliasinfo',
                  'object': relocated})
            ctx.args.scmd = 'aliasinfo'
            alias_info(ctx)
        else:
            raise


def user_add(ctx):
    """create a new e-mail user with the given address"""
    gen_pass = ctx.hdlr.user_add(ctx.args.address.lower(), ctx.args.password)
    if not ctx.args.password and gen_pass:
        w_std(_("Generated password: %s") % gen_pass)


def user_delete(ctx):
    """delete the specified user"""
    ctx.hdlr.user_delete(ctx.args.address.lower(), ctx.args.force)


def user_info(ctx):
    """display information about the given address"""
    address = ctx.args.address.lower()
    try:
        info = ctx.hdlr.user_info(address, ctx.args.details)
    except VMMError as err:
        if err.code is ALIAS_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'aliasinfo',
                  'object': address})
            ctx.args.scmd = 'aliasinfo'
            alias_info(ctx)
        elif err.code is RELOCATED_EXISTS:
            w_err(0, ctx.plan_a_b % {'subcommand': 'relocatedinfo',
                  'object': address})
            ctx.args.scmd = 'relocatedinfo'
            relocated_info(ctx)
        else:
            raise
    else:
        if ctx.args.details in (None, 'du'):
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
    ctx.hdlr.user_name(ctx.args.address.lower(), ctx.args.name)


def user_password(ctx):
    """update the password for the given address"""
    ctx.hdlr.user_password(ctx.args.address.lower(), ctx.args.password)


def user_note(ctx):
    """update the note of the given address"""
    ctx.hdlr.user_note(ctx.args.address.lower(), ctx.args.note)


def user_quota(ctx):
    """update the quota limit for the given address"""
    ctx.hdlr.user_quotalimit(ctx.args.address.lower(), ctx.args.storage,
                             ctx.args.messages)


def user_services(ctx):
    """allow all named service and block the uncredited."""
    if 'domain' in ctx.args.services:
        services = ['domain']
    else:
        services = ctx.args.services
    ctx.hdlr.user_services(ctx.args.address.lower(), *services)


def user_transport(ctx):
    """update the transport of the given address"""
    ctx.hdlr.user_transport(ctx.args.address.lower(), ctx.args.transport)


def setup_parser():
    """Create the argument parser, add all the subcommands and return it."""
    class ArgParser(ArgumentParser):
        """This class fixes the 'width detection'."""
        def _get_formatter(self):
            return self.formatter_class(prog=self.prog, width=WS_ROWS,
                                        max_help_position=26)

    class VersionAction(Action):
        """Show version and copyright information."""
        def __call__(self, parser, namespace, values, option_string=None):
            """implements the Action API."""
            vers_info = _('{program}, version {version} (from {rel_date})\n'
                          'Python {py_vers} on {sysname}'.format(
                              program=parser.prog, version=__version__,
                              rel_date=strftime(
                                            locale.nl_langinfo(locale.D_FMT),
                                            strptime(__date__, '%Y-%m-%d')),
                              py_vers=platform.python_version(),
                              sysname=platform.system()))
            copy_info = _('{copyright}\n{program} is free software and comes '
                          'with ABSOLUTELY NO WARRANTY.'.format(
                              copyright=__copyright__, program=parser.prog))
            parser.exit(message='\n\n'.join((vers_info, copy_info)) + '\n')

    def quota_storage(string):
        if string == 'domain':
            return string
        try:
            storage = size_in_bytes(string)
        except (TypeError, ValueError) as error:
            raise ArgumentTypeError(str(error))
        return storage

    old_rw = txt_wrpr.replace_whitespace
    txt_wrpr.replace_whitespace = False
    fill = lambda t: '\n'.join(txt_wrpr.fill(l) for l in t.splitlines(True))
    mklst = lambda iterable: '\n\t - ' + '\n\t - '.join(iterable)

    description = _('%(prog)s - command line tool to manage email '
                    'domains/accounts/aliases/...')
    epilog = _('use "%(prog)s <subcommand> -h" for information about the '
               'given subcommand')
    parser = ArgParser(description=description, epilog=epilog)
    parser.add_argument('-v', '--version', action=VersionAction, nargs=0,
                        help=_("show %(prog)s's version and copyright "
                               "information and exit"))
    subparsers = parser.add_subparsers(metavar=_('<subcommand>'),
                                     title=_('list of available subcommands'))
    a = subparsers.add_parser

    ###
    # general subcommands
    ###
    cg = a('configget', aliases=('cg',),
           help=_('show the actual value of the configuration option'),
           epilog=_("This subcommand is used to display the actual value of "
           "the given configuration option."))
    cg.add_argument('option', help=_('the name of a configuration option'))
    cg.set_defaults(func=config_get, scmd='configget')

    cs = a('configset', aliases=('cs',),
           help=_('set a new value for the configuration option'),
           epilog=fill(_("Use this subcommand to set or update a single "
               "configuration option's value. option is the configuration "
               "option, value is the option's new value.\n\nNote: This "
               "subcommand will create a new vmm.cfg without any comments. "
               "Your current configuration file will be backed as "
               "vmm.cfg.bak.")),
           formatter_class=RawDescriptionHelpFormatter)
    cs.add_argument('option', help=_('the name of a configuration option'))
    cs.add_argument('value', help=_("the option's new value"))
    cs.set_defaults(func=config_set, scmd='configset')

    sections = ('account', 'bin', 'database', 'domain', 'mailbox', 'misc')
    cf = a('configure', aliases=('cf',),
           help=_('start interactive configuration mode'),
           epilog=fill(_("Starts the interactive configuration for all "
               "configuration sections.\n\nIn this process the currently set "
               "value of each option will be displayed in square brackets. "
               "If no value is configured, the default value of each option "
               "will be displayed in square brackets. Press the return key, "
               "to accept the displayed value.\n\n"
               "If the optional argument section is given, only the "
               "configuration options from the given section will be "
               "displayed and will be configurable. The following sections "
               "are available:\n") + mklst(sections)),
           formatter_class=RawDescriptionHelpFormatter)
    cf.add_argument('-s', choices=sections, metavar='SECTION', dest='section',
                    help=_("configure only options of the given section"))
    cf.set_defaults(func=configure, scmd='configure')

    gu = a('getuser', aliases=('gu',),
           help=_('get the address of the user with the given UID'),
           epilog=_("If only the uid is available, for example from process "
                    "list, the subcommand getuser will show the user's "
                    "address."))
    gu.add_argument('uid', type=int, help=_("a user's unique identifier"))
    gu.set_defaults(func=get_user, scmd='getuser')

    ll = a('listaddresses', aliases=('ll',),
           help=_('list all addresses or search for addresses by pattern'),
           epilog=fill(_("This command lists all defined addresses. "
               "Addresses belonging to alias-domains are prefixed with a '-', "
               "addresses of regular domains with a '+'. Additionally, the "
               "letters 'u', 'a', and 'r' indicate the type of each address: "
               "user, alias and relocated respectively. The output can be "
               "limited with an optional pattern.\n\nTo perform a wild card "
               "search, the % character can be used at the start and/or the "
               "end of the pattern.")),
           formatter_class=RawDescriptionHelpFormatter)
    ll.add_argument('-p', help=_("the pattern to search for"),
                    metavar='PATTERN', dest='pattern')
    ll.set_defaults(func=list_addresses, scmd='listaddresses')

    la = a('listaliases', aliases=('la',),
           help=_('list all aliases or search for aliases by pattern'),
           epilog=fill(_("This command lists all defined aliases. Aliases "
               "belonging to alias-domains are prefixed with a '-', addresses "
               "of regular domains with a '+'. The output can be limited "
               "with an optional pattern.\n\nTo perform a wild card search, "
               "the % character can be used at the start and/or the end of "
               "the pattern.")),
           formatter_class=RawDescriptionHelpFormatter)
    la.add_argument('-p', help=_("the pattern to search for"),
                    metavar='PATTERN', dest='pattern')
    la.set_defaults(func=list_aliases, scmd='listaliases')

    ld = a('listdomains', aliases=('ld',),
           help=_('list all domains or search for domains by pattern'),
           epilog=fill(_("This subcommand lists all available domains. All "
               "domain names will be prefixed either with `[+]', if the "
               "domain is a primary domain, or with `[-]', if it is an alias "
               "domain name. The output can be limited with an optional "
               "pattern.\n\nTo perform a wild card search, the % character "
               "can be used at the start and/or the end of the pattern.")),
           formatter_class=RawDescriptionHelpFormatter)
    ld.add_argument('-p', help=_("the pattern to search for"),
                    metavar='PATTERN', dest='pattern')
    ld.set_defaults(func=list_domains, scmd='listdomains')

    lr = a('listrelocated', aliases=('lr',),
           help=_('list all relocated users or search for relocated users by '
                  'pattern'),
           epilog=fill(_("This command lists all defined relocated addresses. "
               "Relocated entries belonging to alias-domains are prefixed "
               "with a '-', addresses of regular domains with a '+'. The "
               "output can be limited with an optional pattern.\n\nTo "
               "perform a wild card search, the % character can be used at "
               "the start and/or the end of the pattern.")),
           formatter_class=RawDescriptionHelpFormatter)
    lr.add_argument('-p', help=_("the pattern to search for"),
                    metavar='PATTERN', dest='pattern')
    lr.set_defaults(func=list_relocated, scmd='listrelocated')

    lu = a('listusers', aliases=('lu',),
           help=_('list all user accounts or search for accounts by pattern'),
           epilog=fill(_("This command lists all user accounts. User accounts "
               "belonging to alias-domains are prefixed with a '-', "
               "addresses of regular domains with a '+'. The output can be "
               "limited with an optional pattern.\n\nTo perform a wild card "
               "search, the % character can be used at the start and/or the "
               "end of the pattern.")),
           formatter_class=RawDescriptionHelpFormatter)
    lu.add_argument('-p', help=_("the pattern to search for"),
                    metavar='PATTERN', dest='pattern')
    lu.set_defaults(func=list_users, scmd='listusers')

    lp = a('listpwschemes', aliases=('lp',),
           help=_('lists all usable password schemes and password encoding '
                  'suffixes'),
           epilog=fill(_("This subcommand lists all password schemes which "
               "could be used in the vmm.cfg as value of the "
               "misc.password_scheme option. The output varies, depending "
               "on the used Dovecot version and the system's libc.\nWhen "
               "your Dovecot installation isn't too old, you will see "
               "additionally a few usable encoding suffixes. One of them can "
               "be appended to the password scheme.")),
           formatter_class=RawDescriptionHelpFormatter)
    lp.set_defaults(func=list_pwschemes, scmd='listpwschemes')

    ###
    # domain subcommands
    ###
    da = a('domainadd', aliases=('da',), help=_('create a new domain'),
           epilog=fill(_("Adds the new domain into the database and creates "
               "the domain directory.\n\nIf the optional argument transport "
               "is given, it will override the default transport "
               "(domain.transport) from vmm.cfg. The specified transport "
               "will be the default transport for all new accounts in this "
               "domain.")),
           formatter_class=RawDescriptionHelpFormatter)
    da.add_argument('fqdn', help=_('a fully qualified domain name'))
    da.add_argument('-t', metavar='TRANSPORT', dest='transport',
                    help=_('a Postfix transport (transport: or '
                           'transport:nexthop)'))
    da.set_defaults(func=domain_add, scmd='domainadd')

    details = ('accounts', 'aliasdomains', 'aliases', 'catchall', 'relocated',
               'full')
    di = a('domaininfo', aliases=('di',),
           help=_('display information about the given domain'),
           epilog=fill(_("This subcommand shows some information about the "
               "given domain.\n\nFor a more detailed information about the "
               "domain the optional argument details can be specified. A "
               "possible details value can be one of the following six "
               "keywords:\n") + mklst(details)),
           formatter_class=RawDescriptionHelpFormatter)
    di.add_argument('fqdn', help=_('a fully qualified domain name'))
    di.add_argument('-d', choices=details, dest='details', metavar='DETAILS',
                    help=_('additionally details to display'))
    di.set_defaults(func=domain_info, scmd='domaininfo')

    do = a('domainnote', aliases=('do',),
           help=_('set, update or delete the note of the given domain'),
           epilog=_('With this subcommand, it is possible to attach a note to '
                    'the specified domain. Without an argument, an existing '
                    'note is removed.'))
    do.add_argument('fqdn', help=_('a fully qualified domain name'))
    do.add_argument('-n', metavar='NOTE', dest='note',
                    help=_('the note that should be set'))
    do.set_defaults(func=domain_note, scmd='domainnote')

    dq = a('domainquota', aliases=('dq',),
           help=_('update the quota limit of the specified domain'),
           epilog=fill(_("This subcommand is used to configure a new quota "
               "limit for the accounts of the domain - not for the domain "
               "itself.\n\nThe default quota limit for accounts is defined "
               "in the vmm.cfg (domain.quota_bytes and "
               "domain.quota_messages).\n\nThe new quota limit will affect "
               "only those accounts for which the limit has not been "
               "overridden. If you want to restore the default to all "
               "accounts, you may pass the optional argument --force. When "
               "the argument messages was omitted the default number of "
               "messages 0 (zero) will be applied.")),
           formatter_class=RawDescriptionHelpFormatter)
    dq.add_argument('fqdn', help=_('a fully qualified domain name'))
    dq.add_argument('storage', type=quota_storage,
                    help=_('quota limit in {kilo,mega,giga}bytes e.g. 2G '
                           'or 2048M',))
    dq.add_argument('-m', default=0, type=int, metavar='MESSAGES',
                    dest='messages',
                    help=_('quota limit in number of messages (default: 0)'))
    dq.add_argument('--force', action='store_true',
                    help=_('enforce the limit for all accounts'))
    dq.set_defaults(func=domain_quota, scmd='domainquota')

    ds = a('domainservices', aliases=('ds',),
           help=_('enables the specified services and disables all not '
                  'specified services of the given domain'),
           epilog=fill(_("To define which services could be used by the users "
               "of the domain — with the given fqdn — use this "
               "subcommand.\n\nEach specified service will be enabled/"
               "usable. All other services will be deactivated/unusable. "
               "Possible service names are: imap, pop3, sieve and smtp.\nThe "
               "new service set will affect only those accounts for which "
               "the set has not been overridden. If you want to restore the "
               "default to all accounts, you may pass the option--force.")),
           formatter_class=RawDescriptionHelpFormatter)
    ds.add_argument('fqdn', help=_('a fully qualified domain name'))
    ds.add_argument('-s', choices=SERVICES,
                    help=_('services which should be usable'),
                    metavar='SERVICE', nargs='+', dest='services')
    ds.add_argument('--force', action='store_true',
                    help=_('enforce the service set for all accounts'))
    ds.set_defaults(func=domain_services, scmd='domainservices')

    dt = a('domaintransport', aliases=('dt',),
           help=_('update the transport of the specified domain'),
           epilog=fill(_("A new transport for the indicated domain can be set "
               "with this subcommand.\n\nThe new transport will affect only "
               "those accounts for which the transport has not been "
               "overridden. If you want to restore the default to all "
               "accounts, you may give the option --force.")),
           formatter_class=RawDescriptionHelpFormatter)
    dt.add_argument('fqdn', help=_('a fully qualified domain name'))
    dt.add_argument('transport', help=_('a Postfix transport (transport: or '
                                        'transport:nexthop)'))
    dt.add_argument('--force', action='store_true',
                    help=_('enforce the transport for all accounts'))
    dt.set_defaults(func=domain_transport, scmd='domaintransport')

    dd = a('domaindelete', aliases=('dd',),
           help=_('delete the given domain and all its alias domains'),
           epilog=fill(_("This subcommand deletes the domain specified by "
               "fqdn.\n\nIf there are accounts, aliases and/or relocated "
               "users assigned to the given domain, vmm will abort the "
               "requested operation and show an error message. If you know, "
               "what you are doing, you can specify the optional argument "
               "--force.\n\nIf you really always know what you are doing, "
               "edit your vmm.cfg and set the option domain.force_deletion "
               "to true.")),
           formatter_class=RawDescriptionHelpFormatter)
    dd.add_argument('fqdn', help=_('a fully qualified domain name'))
    dd.add_argument('--force', action='store_true',
                    help=_('also delete all accounts, aliases and/or '
                           'relocated users'))
    dd.set_defaults(func=domain_delete, scmd='domaindelete')

    ###
    # alias domain subcommands
    ###
    ada = a('aliasdomainadd', aliases=('ada',),
            help=_('create a new alias for an existing domain'),
            epilog=_('This subcommand adds the new alias domain (fqdn) to '
                     'the destination domain that should be aliased.'))
    ada.add_argument('fqdn', help=_('a fully qualified domain name'))
    ada.add_argument('destination',
                     help=_('the fqdn of the destination domain'))
    ada.set_defaults(func=aliasdomain_add, scmd='aliasdomainadd')

    adi = a('aliasdomaininfo', aliases=('adi',),
            help=_('show the destination of the given alias domain'),
            epilog=_('This subcommand shows to which domain the alias domain '
                     'fqdn is assigned to.'))
    adi.add_argument('fqdn', help=_('a fully qualified domain name'))
    adi.set_defaults(func=aliasdomain_info, scmd='aliasdomaininfo')

    ads = a('aliasdomainswitch', aliases=('ads',),
            help=_('assign the given alias domain to an other domain'),
            epilog=_('If the destination of the existing alias domain fqdn '
                     'should be switched to another destination use this '
                     'subcommand.'))
    ads.add_argument('fqdn', help=_('a fully qualified domain name'))
    ads.add_argument('destination',
                     help=_('the fqdn of the destination domain'))
    ads.set_defaults(func=aliasdomain_switch, scmd='aliasdomainswitch')

    add = a('aliasdomaindelete', aliases=('add',),
            help=_('delete the specified alias domain'),
            epilog=_('Use this subcommand if the alias domain fqdn should be '
                     'removed.'))
    add.add_argument('fqdn', help=_('a fully qualified domain name'))
    add.set_defaults(func=aliasdomain_delete, scmd='aliasdomaindelete')

    ###
    # account subcommands
    ###
    ua = a('useradd', aliases=('ua',),
           help=_('create a new e-mail user with the given address'),
           epilog=fill(_('Use this subcommand to create a new e-mail account '
               'for the given address.\n\nIf the password is not provided, '
               'vmm will prompt for it interactively. When no password is '
               'provided and account.random_password is set to true, vmm '
               'will generate a random password and print it to stdout '
               'after the account has been created.')),
           formatter_class=RawDescriptionHelpFormatter)
    ua.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    ua.add_argument('-p', metavar='PASSWORD', dest='password',
                    help=_("the new user's password"))
    ua.set_defaults(func=user_add, scmd='useradd')

    details = ('aliases', 'du', 'full')
    ui = a('userinfo', aliases=('ui',),
           help=_('display information about the given address'),
           epilog=fill(_('This subcommand displays some information about '
               'the account specified by the given address.\n\nIf the '
               'optional argument details is given some more information '
               'will be displayed.\nPossible values for details are:\n') +
               mklst(details)),
           formatter_class=RawDescriptionHelpFormatter)
    ui.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    ui.add_argument('-d', choices=details, metavar='DETAILS', dest='details',
                    help=_('additionally details to display'))
    ui.set_defaults(func=user_info, scmd='userinfo')

    un = a('username', aliases=('un',),
           help=_('set, update or delete the real name for an address'),
           epilog=fill(_("The user's real name can be set/updated with this "
               "subcommand.\n\nIf no name is given, the value stored for the "
               "account is erased.")),
           formatter_class=RawDescriptionHelpFormatter)
    un.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    un.add_argument('-n', help=_("a user's real name"), metavar='NAME',
                    dest='name')
    un.set_defaults(func=user_name, scmd='username')

    uo = a('usernote', aliases=('uo',),
           help=_('set, update or delete the note of the given address'),
           epilog=_('With this subcommand, it is possible to attach a note to '
               'the specified account. Without the note argument, an '
               'existing note is removed.'))
    uo.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    uo.add_argument('-n', metavar='NOTE', dest='note',
                    help=_('the note that should be set'))
    uo.set_defaults(func=user_note, scmd='usernote')

    up = a('userpassword', aliases=('up',),
           help=_('update the password for the given address'),
           epilog=fill(_("The password of an account can be updated with this "
               "subcommand.\n\nIf no password was provided, vmm will prompt "
               "for it interactively.")),
           formatter_class=RawDescriptionHelpFormatter)
    up.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    up.add_argument('-p', metavar='PASSWORD', dest='password',
                    help=_("the user's new password"))
    up.set_defaults(func=user_password, scmd='userpassword')

    uq = a('userquota', aliases=('uq',),
           help=_('update the quota limit for the given address'),
           epilog=fill(_("This subcommand is used to set a new quota limit "
               "for the given account.\n\nWhen the argument messages was "
               "omitted the default number of messages 0 (zero) will be "
               "applied.\n\nInstead of a storage limit pass the keyword "
               "'domain' to remove the account-specific override, causing "
               "the domain's value to be in effect.")),
           formatter_class=RawDescriptionHelpFormatter)
    uq.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    uq.add_argument('storage', type=quota_storage,
                    help=_('quota limit in {kilo,mega,giga}bytes e.g. 2G '
                           'or 2048M'))
    uq.add_argument('-m', default=0, type=int, metavar='MESSAGES',
                    dest='messages',
                    help=_('quota limit in number of messages (default: 0)'))
    uq.set_defaults(func=user_quota, scmd='userquota')

    us = a('userservices', aliases=('us',),
           help=_('enable the specified services and disables all not '
                  'specified services'),
           epilog=fill(_("To grant a user access to the specified service(s), "
               "use this command.\n\nAll omitted services will be "
               "deactivated/unusable for the user with the given "
               "address.\n\nInstead of any service pass the keyword "
               "'domain' to remove the account-specific override, causing "
               "the domain's value to be in effect.")),
           formatter_class=RawDescriptionHelpFormatter)
    us.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    us.add_argument('-s', choices=SERVICES + ('domain',),
                    help=_('services which should be usable'),
                    metavar='SERVICE', nargs='+', dest='services')
    us.set_defaults(func=user_services, scmd='userservices')

    ut = a('usertransport', aliases=('ut',),
           help=_('update the transport of the given address'),
           epilog=fill(_("A different transport for an account can be "
               "specified with this subcommand.\n\nInstead of a transport "
               "pass the keyword 'domain' to remove the account-specific "
               "override, causing the domain's value to be in effect.")),
           formatter_class=RawDescriptionHelpFormatter)
    ut.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    ut.add_argument('transport', help=_('a Postfix transport (transport: or '
                                        'transport:nexthop)'))
    ut.set_defaults(func=user_transport, scmd='usertransport')

    ud = a('userdelete', aliases=('ud',),
           help=_('delete the specified user'),
           epilog=fill(_('Use this subcommand to delete the account with the '
               'given address.\n\nIf there are one or more aliases with an '
               'identical destination address, vmm will abort the requested '
               'operation and show an error message. To prevent this, '
               'give the optional argument --force.')),
           formatter_class=RawDescriptionHelpFormatter)
    ud.add_argument('address',
                    help=_("an account's e-mail address (local-part@fqdn)"))
    ud.add_argument('--force', action='store_true',
                    help=_('also delete assigned alias addresses'))
    ud.set_defaults(func=user_delete, scmd='userdelete')

    ###
    # alias subcommands
    ###
    aa = a('aliasadd', aliases=('aa',),
           help=_('create a new alias e-mail address with one or more '
                  'destinations'),
           epilog=fill(_("This subcommand is used to create a new alias "
               "address with one or more destination addresses.\n\nWithin "
               "the destination address, the placeholders %n, %d, and %= "
               "will be replaced by the local part, the domain, or the "
               "email address with '@' replaced by '=' respectively. In "
               "combination with alias domains, this enables "
               "domain-specific destinations.")),
           formatter_class=RawDescriptionHelpFormatter)
    aa.add_argument('address',
                    help=_("an alias' e-mail address (local-part@fqdn)"))
    aa.add_argument('destination', nargs='+',
                    help=_("a destination's e-mail address (local-part@fqdn)"))
    aa.set_defaults(func=alias_add, scmd='aliasadd')

    ai = a('aliasinfo', aliases=('ai',),
           help=_('show the destination(s) of the specified alias'),
           epilog=_('Information about the alias with the given address can '
                    'be displayed with this subcommand.'))
    ai.add_argument('address',
                    help=_("an alias' e-mail address (local-part@fqdn)"))
    ai.set_defaults(func=alias_info, scmd='aliasinfo')

    ad = a('aliasdelete', aliases=('ad',),
           help=_('delete the specified alias e-mail address or one of its '
                  'destinations'),
           epilog=fill(_("This subcommand is used to delete one or multiple "
               "destinations from the alias with the given address.\n\nWhen "
               "no destination address was specified the alias with all its "
               "destinations will be deleted.")),
           formatter_class=RawDescriptionHelpFormatter)
    ad.add_argument('address',
                    help=_("an alias' e-mail address (local-part@fqdn)"))
    ad.add_argument('destination', nargs='*',
                    help=_("a destination's e-mail address (local-part@fqdn)"))
    ad.set_defaults(func=alias_delete, scmd='aliasdelete')

    ###
    # catch-all subcommands
    ###
    caa = a('catchalladd', aliases=('caa',),
            help=_('add one or more catch-all destinations for a domain'),
            epilog=fill(_('This subcommand allows to specify destination '
                'addresses for a domain, which shall receive mail addressed '
                'to unknown local parts within that domain. Those catch-all '
                'aliases hence "catch all" mail to any address in the domain '
                '(unless a more specific alias, mailbox or relocated entry '
                'exists).\n\nWARNING: Catch-all addresses can cause mail '
                'server flooding because spammers like to deliver mail to '
                'all possible combinations of names, e.g. to all addresses '
                'between abba@example.org and zztop@example.org.')),
           formatter_class=RawDescriptionHelpFormatter)
    caa.add_argument('fqdn', help=_('a fully qualified domain name'))
    caa.add_argument('destination', nargs='+',
                    help=_("a destination's e-mail address (local-part@fqdn)"))
    caa.set_defaults(func=catchall_add, scmd='catchalladd')

    cai = a('catchallinfo', aliases=('cai',),
            help=_('show the catch-all destination(s) of the specified '
                   'domain'),
            epilog=_('This subcommand displays information about catch-all '
                     'aliases defined for a domain.'))
    cai.add_argument('fqdn', help=_('a fully qualified domain name'))
    cai.set_defaults(func=catchall_info, scmd='catchallinfo')

    cad = a('catchalldelete', aliases=('cad',),
            help=_("delete the specified catch-all destination or all of a "
                   "domain's destinations"),
            epilog=_('With this subcommand, catch-all aliases defined for a '
                     'domain can be removed, either all of them, or those '
                     'destinations which were specified explicitly.'))
    cad.add_argument('fqdn', help=_('a fully qualified domain name'))
    cad.add_argument('destination', nargs='*',
                    help=_("a destination's e-mail address (local-part@fqdn)"))
    cad.set_defaults(func=catchall_delete, scmd='catchalldelete')

    ###
    # relocated subcommands
    ###
    ra = a('relocatedadd', aliases=('ra',),
           help=_('create a new record for a relocated user'),
           epilog=_("A new relocated user can be created with this "
                    "subcommand."))
    ra.add_argument('address', help=_("a relocated user's e-mail address "
                                      "(local-part@fqdn)"))
    ra.add_argument('newaddress',
                   help=_('e-mail address where the user can be reached now'))
    ra.set_defaults(func=relocated_add, scmd='relocatedadd')

    ri = a('relocatedinfo', aliases=('ri',),
           help=_('print information about a relocated user'),
           epilog=_('This subcommand shows the new address of the relocated '
                    'user with the given address.'))
    ri.add_argument('address', help=_("a relocated user's e-mail address "
                                      "(local-part@fqdn)"))
    ri.set_defaults(func=relocated_info, scmd='relocatedinfo')

    rd = a('relocateddelete', aliases=('rd',),
           help=_('delete the record of the relocated user'),
           epilog=_('Use this subcommand in order to delete the relocated '
                    'user with the given address.'))
    rd.add_argument('address', help=_("a relocated user's e-mail address "
                                      "(local-part@fqdn)"))
    rd.set_defaults(func=relocated_delete, scmd='relocateddelete')

    txt_wrpr.replace_whitespace = old_rw
    return parser


def _get_order(ctx):
    """returns a tuple with (key, 1||0) tuples. Used by functions, which
    get a dict from the handler."""
    order = ()
    if ctx.args.scmd == 'domaininfo':
        order = (('domain name', 0), ('gid', 1), ('domain directory', 0),
                 ('quota limit/user', 0), ('active services', 0),
                 ('transport', 0), ('alias domains', 0), ('accounts', 0),
                 ('aliases', 0), ('relocated', 0), ('catch-all dests', 0))
    elif ctx.args.scmd == 'userinfo':
        if ctx.args.details in ('du', 'full') or \
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
    elif ctx.args.scmd == 'getuser':
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
                    w_std('\t%s (%s)' % (domain,
                                        domain.encode('utf-8').decode('idna')))
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
        domain = '%s (%s)' % (domain, domain.encode('utf-8').decode('idna'))
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
            info[key] = '%s (%s)' % (info[key],
                                     info[key].encode(ENCODING).decode('idna'))
    w_std(title, '-' * len(title),
          _('\tThe alias domain %(alias)s belongs to:\n\t    * %(domain)s') %
          info, '')

del _
