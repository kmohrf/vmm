=========
Using vmm
=========

vmm is the easy to use command-line tool of the Virtual Mail Manager.
It allows you to simply and quickly administer your mail server.
The general command syntax looks like::

 vmm -h|-v|--help|--version
 vmm subcommand -h|--help
 vmm subcommand arguments [options]

Each subcommand has both a long and a short form.
Both forms are case sensitive.
The subcommands are categorized by their functionality:

.. toctree::
   :maxdepth: 1

   howto/general_subcommands
   howto/manage_domains
   howto/manage_alias_domains
   howto/manage_accounts
   howto/manage_alias_addresses
   howto/manage_catch-all_addresses
   howto/manage_relocated_users


Most of the *subcommand*\ s take one or more *argument*\ s.

Options
-------
The following options are recognized by :program:`vmm`.

.. program:: vmm

.. option:: -h, --help

 show a list of available subcommands and exit.

.. option:: -v, --version

 show :command:`vmm`'s version and copyright information and exit.


Arguments
---------
*address*
 The complete e-mail address (*local-part*\ @\ *fqdn*) of an user account,
 alias address or relocated user.

*destination*
 Is either an e-mail address when used with
 :doc:`Alias subcommands <howto/manage_alias_addresses>`.
 Or a *fqdn* when used with
 :doc:`Alias domain subcommands <howto/manage_alias_domains>`.

*fqdn*
 The fully qualified domain name – without the trailing dot – of a domain
 or alias domain.

*messages*
 An integer value which specifies a quota limit in number of messages.
 **0** (zero) means unlimited - no quota limit for the number of messages.

*option*
 Is the name of a configuration option, prefixed with the section name and
 a dot.
 For example: *misc*\ **.**\ *transport*
 All configuration options are described in :manpage:`vmm.cfg(5)`.

*service*
 The name of a service, commonly used with Dovecot.
 Supported services are: **imap**, **pop3**, **sieve** and **smtp**.

*storage*
 Specifies a quota limit in bytes.
 One of the following prefixes can be appended to the integer value:
 **b** (bytes), **k** (kilobytes), **M** (megabytes) or **G** (gigabytes).
 **0** (zero) means unlimited - no quota limit in bytes.

*transport*
 A transport for Postfix, written as: *transport*\ **:** or
 *transport*\ **:**\ *nexthop*.
 See :manpage:`transport(5)` for more details.

Files
-----
:command:`vmm` reads its configuration data from :file:`vmm.cfg`.

:file:`/root/vmm.cfg`
 will be used when found.

:file:`/usr/local/etc/vmm.cfg`
 will be used when the above file doesn't exist.

:file:`/etc/vmm.cfg`
 will be used when none of the both above mentioned files exists.
