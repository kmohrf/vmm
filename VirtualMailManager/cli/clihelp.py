# -*- coding: UTF-8 -*-
# Copyright (c) 2012, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.cli.vmmhelp
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's command line help.
"""

_ = lambda msg: msg

help_msgs = {
# TP: There are some words enclosed within angle brackets '<'word'>'. They
# are used to indicate replaceable arguments. Please do not translate them.
#
# The descriptions of subcommands may contain the both keywords 'domain'
# and 'force', enclosed within single quotes. Please keep them as they are.
#
    # TP: description of subcommand configget
    'configget': (_(u"""This subcommand is used to display the actual value
of the given configuration <option>."""),),
    # TP: description of subcommand configset
    'configset': (_(u"""Use this subcommand to set or update a single
configuration option's value. <option> is the configuration option, <value>
is the <option>'s new value."""),
_(u"""Note: This subcommand will create a new vmm.cfg without any comments.
Your current configuration file will be backed as vmm.cfg.bak."""),),
    # TP: description of subcommand configure
    'configure': (_(u"""Starts the interactive configuration for all
configuration sections."""),
_(u"""In this process the currently set value of each option will be displayed
in square brackets. If no value is configured, the default value of each
option will be displayed in square brackets. Press the return key, to accept
the displayed value."""),
_(u"""If the optional argument <section> is given, only the configuration
options from the given section will be displayed and will be configurable.
The following sections are available:
"""),
"""    account, bin, database, domain, mailbox, misc""",
_(u"""All configuration options are described in vmm.cfg(5)."""),
_(u"""Note: This subcommand will create a new vmm.cfg without any comments.
Your current configuration file will be backed as vmm.cfg.bak."""),),
    # TP: description of subcommand getuser
    'getuser': (_(u"""If only the <uid> is available, for example from process
list, the subcommand getuser will show the user's address."""),),
    # TP: description of subcommand listdomains
    'listdomains': (_(u"""This subcommand lists all available domains. All
domain names will be prefixed either with `[+]', if the domain is a primary
domain, or with `[-]', if it is an alias domain name. The output can be
limited with an optional <pattern>."""),
_(u"""To perform a wild card search, the % character can be used at the start
and/or the end of the <pattern>."""),),
    # TP: description of subcommand listpwschemes
    'listpwschemes': (_(u"""This subcommand lists all password schemes which
could be used in the vmm.cfg as value of the misc.password_scheme option.
The output varies, depending on the used Dovecot version and the system's
libc."""),
_(u"""When your Dovecot installation isn't too old, you will see additionally
a few usable encoding suffixes. One of them can be appended to the password
scheme."""),),
    # TP: description of subcommand version
    'version': (_(u"""Prints vmm's version and copyright information to stdout.
After this vmm exits."""),),
    # TP: description of subcommand domainadd
    'domainadd': (_(u"""Adds the new domain into the database and creates the
domain directory."""),
_(u"""If the optional argument <transport> is given, it will override the
default transport (domain.transport) from vmm.cfg. The specified <transport>
will be the default transport for all new accounts in this domain."""),
_(u"""Configuration-related behavior:"""),
u""" * domain.auto_postmaster""",
_(u"""When that option is set to true (default) vmm will automatically create
the postmaster account for the new domain and prompt for postmaster@<fqdn>'s
password."""),
u""" * account.random_password""",
_(u"""When the value of that option is also set to true, vmm will automatically
create the postmaster account for the new domain and print the generated
postmaster password to stdout."""),),
    # TP: description of subcommand domaindelete
    'domaindelete': (_(u"""This subcommand deletes the domain specified by
<fqdn>."""),
_(u"""If there are accounts, aliases and/or relocated users assigned to the
given domain, vmm will abort the requested operation and show an error
message. If you know, what you are doing, you can specify the optional keyword
'force'."""),
_(u"""If you really always know what you are doing, edit your vmm.cfg and set
the option domain.force_deletion to true."""),),
    # TP: description of subcommand domaininfo
    'domaininfo': (_(u"""This subcommand shows some information about the
given domain."""),
_(u"""For a more detailed information about the domain the optional argument
<details> can be specified. A possible <details> value can be one of the
following six keywords:"""),
"""    accounts, aliasdomains, aliases, catchall, relocated, full""",),
    # TP: description of subcommand domainquota
    'domainquota': (_(u"""This subcommand is used to configure a new quota
limit for the accounts of the domain - not for the domain itself."""),
_(u"""The default quota limit for accounts is defined in the vmm.cfg
(domain.quota_bytes and domain.quota_messages)."""),
_(u"""The new quota limit will affect only those accounts for which the limit
has not been overridden. If you want to restore the default to all accounts,
you may pass the keyword 'force'. When the argument <messages> was omitted the
default number of messages 0 (zero) will be applied."""),),
    # TP: description of subcommand domainservices
    'domainservices': (_(u"""To define which services could be used by the
users of the domain — with the given <fqdn> — use this subcommand."""),
_(u"""Each specified <service> will be enabled/usable. All other services
will be deactivated/unusable. Possible <service> names are:"""),
u"""    imap, pop3, sieve, smtp""",
_(u"""The new service set will affect only those accounts for which the set has
not been overridden. If you want to restore the default to all accounts, you
may pass the keyword 'force'."""),),
    # TP: description of subcommand domaintransport
    'domaintransport': (_(u"""A new transport for the indicated domain can be
set with this subcommand."""),
_(u"""The new transport will affect only those accounts for which the transport
has not been overridden. If you want to restore the default to all accounts,
you may pass the keyword 'force'."""),),
    # TP: description of subcommand domainnote
    'domainnote': (_(u"""With this subcommand, it is possible to attach a
note to the specified domain. Without an argument, an existing note is
removed."""),),
    # TP: description of subcommand aliasdomainadd
    'aliasdomainadd': (_(u"""This subcommand adds the new alias domain
(<fqdn>) to the destination <domain> that should be aliased."""),),
    # TP: description of subcommand aliasdomaindelete
    'aliasdomaindelete': (_(u"""Use this subcommand if the alias domain
<fqdn> should be removed."""),),
    # TP: description of subcommand aliasdomaininfo
    'aliasdomaininfo': (_(u"""This subcommand shows to which domain the alias
domain <fqdn> is assigned to."""),),
    # TP: description of subcommand aliasdomainswitch
    'aliasdomainswitch': (_(u"""If the destination of the existing alias
domain <fqdn> should be switched to another <destination> use this
subcommand."""),),
    # TP: description of subcommand useradd
    'useradd': (_(u"""Use this subcommand to create a new e-mail account for
the given <address>."""),
_(u"""If the <password> is not provided, vmm will prompt for it interactively.
When no <password> is provided and account.random_password is set to true, vmm
will generate a random password and print it to stdout after the account has
been created."""),),
    # TP: description of subcommand userdelete
    'userdelete': (_(u"""Use this subcommand to delete the account with the
given <address>."""),
_(u"""If there are one or more aliases with an identical destination address,
vmm will abort the requested operation and show an error message. To prevent
this, specify the optional keyword 'force'."""),),
    # TP: description of subcommand userinfo
    'userinfo': (_(u"""This subcommand displays some information about the
account specified by <address>."""),
_(u"""If the optional argument <details> is given some more information will be
displayed. Possible values for <details> are:"""),
u"""    aliases, du. full""",),
    # TP: description of subcommand username
    'username': (_(u"""The user's real <name> can be set/updated with this
subcommand."""),
_(u"""If no <name> is given, the value stored for the account is erased."""),
),
    # TP: description of subcommand userpassword
    'userpassword': (_(u"""The password of an account can be updated with this
subcommand."""),
_(u"""If no <password> was provided, vmm will prompt for it interactively."""),
),
    # TP: description of subcommand usernote
    'usernote': (_(u"""With this subcommand, it is possible to attach a note
to the specified account. Without an argument, an existing note is
removed."""),),
    # TP: description of subcommand userquota
    'userquota': (_(u"""This subcommand is used to set a new quota limit for
the given account."""),
_(u"""When the argument <messages> was omitted the default number of messages
0 (zero) will be applied."""),
_(u"""Instead of <storage> pass the keyword 'domain' to remove the
account-specific override, causing the domain's value to be in effect."""),),
    # TP: description of subcommand userservices
    'userservices': (_(u"""To grant a user access to the specified services,
use this command."""),
_(u"""All omitted services will be deactivated/unusable for the user with the
given <address>."""),
_(u"""Instead of <service> pass 'domain' to remove the account-specific
override, causing the domain's value to be in effect."""),),
    # TP: description of subcommand usertransport
    'usertransport': (_(u"""A different <transport> for an account can be
specified with this subcommand."""),
_(u"""Instead of <transport> pass 'domain' to remove the account-specific
override, causing the domain's value to be in effect."""),),
    # TP: description of subcommand aliasadd
    'aliasadd': (_(u"""This subcommand is used to create a new alias
<address> with one or more <destination> addresses."""),
_(u"""Within the destination address, the placeholders '%n', '%d', and '%='
will be replaced by the local part, the domain, or the email address with '@'
replaced by '=' respectively. In combination with alias domains, this enables
domain-specific destinations."""),),
    # TP: description of subcommand aliasdelete
    'aliasdelete': (_(u"""This subcommand is used to delete one or multiple
<destination>s from the alias with the given <address>."""),
_(u"""When no <destination> address was specified the alias with all its
destinations will be deleted."""),),
    # TP: description of subcommand aliasinfo
    'aliasinfo': (_(u"""Information about the alias with the given <address>
can be displayed with this subcommand."""),),
    # TP: description of subcommand relocatedadd
    'relocatedadd': (_(u"""A new relocated user can be created with this
subcommand."""),
_(u"""<address> is the user's ex-email address, for example
b.user@example.com, and <newaddress> points to the new email address where
the user can be reached."""),),
    # TP: description of subcommand relocatedinfo
    'relocatedinfo': (_(u"""This subcommand shows the new address of the
relocated user with the given <address>."""),),
    # TP: description of subcommand relocateddelete
    'relocateddelete': (_(u"""Use this subcommand in order to delete the
relocated user with the given <address>."""),),
    # TP: description of subcommand catchalladd
    'catchalladd': (_(u"""This subcommand allows to specify destination
addresses for a domain, which shall receive mail addressed to unknown
local-parts within that domain. Those catch-all aliases hence "catch all" mail
to any address in the domain (unless a more specific alias, mailbox or
relocated user exists)."""),
_(u"""WARNING: Catch-all addresses can cause mail server flooding because
spammers like to deliver mail to all possible combinations of names, e.g.
to all addresses between abba@example.org and zztop@example.org."""),),
    # TP: description of subcommand catchallinfo
    'catchallinfo': (_(u"""This subcommand displays information about catch-all
aliases defined for the domain <fqdn>."""),),
    # TP: description of subcommand catchalldelete
    'catchalldelete': (_(u"""With this subcommand, catch-all aliases defined
for a domain can be removed, either all of them, or those <destination>s which
were specified explicitly."""),),
}

del _
