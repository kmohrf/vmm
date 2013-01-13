================
Managing domains
================
.. _domainadd:

domainadd
---------
Syntax:
 | **vmm domainadd** *fqdn* [**-t** *transport*]
 | **vmm da** *fqdn* [**-t** *transport*]
 
Adds the new domain into the database and creates the domain directory.

If the optional argument transport is given, it will override the default
transport (*domain.transport*) from :file:`vmm.cfg`.
The specified *transport* will be the default transport for all new accounts
in this domain.

Configuration-related behavior:

 *domain.auto_postmaster*
  When that option is set to **true** (default) :command:`vmm` will
  automatically create the postmaster account for the new domain and prompt
  for **postmaster**\ @\ *fqdn*'s password.

 *account.random_password*
  When the value of that option is also set to **true**, :command:`vmm`
  will automatically create the postmaster account for the new domain and
  print the generated postmaster password to stdout.

Example:

.. code-block:: console

 root@host:~# vmm domainadd support.example.com -t smtp:[mx1.example.com]:2025
 Creating account for postmaster@support.example.com
 Enter new password: 
 Retype new password: 
 root@host:~# vmm cs account.random_password true
 root@host:~# vmm da sales.example.com
 Creating account for postmaster@sales.example.com
 Generated password: pLJUQ6Xg_z

domaindelete
------------
Syntax:
 | **vmm domaindelete** *fqdn* [**‒‒force**]
 | **vmm dd** *fqdn* [**‒‒force**]

This subcommand deletes the domain specified by *fqdn*.

If there are accounts, aliases and/or relocated users assigned to the given
domain, :command:`vmm` will abort the requested operation and show an error
message.
If you know, what you are doing, you can specify the optional argument
**‒‒force**.

If you really always know what you are doing, edit your :file:`vmm.cfg` and
set the option *domain.force_deletion* to **true**.

domaininfo
----------
Syntax:
 | **vmm domaininfo** *fqdn* [**-d** *details*]
 | **vmm di** *fqdn* [**-d** *details*]

This subcommand shows some information about the given domain.

For a more detailed information about the domain the optional argument
*details* can be specified.
A possible *details* value can be one of the following six keywords:

============ ==========================================================
keyword      description
============ ==========================================================
accounts     to list the e-mail addresses of all existing user accounts
aliasdomains to list all assigned alias domain names
aliases      to list all available alias e-mail addresses
catchall     to list all catch-all destinations
relocated    to list the e-mail addresses of all relocated users
full         to list all information mentioned above
============ ==========================================================

Example:

.. code-block:: console

 root@host:~# vmm domaininfo sales.example.com
 Domain information
 ------------------
         Domain Name......: sales.example.com
         GID..............: 70708
         Domain Directory.: /srv/mail/c/70708
         Quota Limit/User.: Storage: 500.00 MiB; Messages: 10,000
         Active Services..: IMAP SIEVE
         Transport........: lmtp:unix:private/dovecot-lmtp
         Alias Domains....: 0
         Accounts.........: 1
         Aliases..........: 0
         Relocated........: 0
         Catch-All Dests..: 0

domainnote
----------
Syntax:
 | **vmm domainnote** *fqdn* [**-n** *note*]
 | **vmm do** *fqdn* [**-n** *note*]

With this subcommand, it is possible to attach a note to the specified
domain.
Without an argument, an existing note is removed.

Example:

.. code-block:: console

 root@host:~# vmm do example.com -n 'Belongs to Robert'

.. versionadded:: 0.6.0

domainquota
-----------
Syntax:
 | **vmm domainquota** *fqdn storage* [**-m** *messages*] [**‒‒force**]
 | **vmm dq** *fqdn storage* [**-m** *messages*] [**‒‒force**]

This subcommand is used to configure a new quota limit for the accounts
of the domain - not for the domain itself.

The default quota limit for accounts is defined in the :file:`vmm.cfg`
(*domain.quota_bytes* and *domain.quota_messages*).

The new quota limit will affect only those accounts for which the limit has
not been overridden.
If you want to restore the default to all accounts, you may pass the optional
argument **‒‒force**.
When the argument *messages* was omitted the default number of messages
**0** (zero) will be applied.

Example:

.. code-block:: console

 root@host:~# vmm domainquota example.com 1g ‒‒force

.. versionadded:: 0.6.0

domainservices
--------------
Syntax:
 | **vmm domainservices** *fqdn* [**-s** *service ...*] [**‒‒force**]
 | **vmm ds** *fqdn* [**-s** *service ...*] [**‒‒force**]

To define which services could be used by the users of the domain — with
the given *fqdn* — use this subcommand.

Each specified *service* will be enabled/usable.
All other services will be deactivated/unusable.
Possible service names are: **imap**, **pop3**, **sieve** and **smtp**.
The new service set will affect only those accounts for which the set has
not been overridden.
If you want to restore the default to all accounts, you may pass the
option **‒‒force**.

.. versionadded:: 0.6.0

domaintransport
---------------
Syntax:
 | **vmm domaintransport** *fqdn transport* [**‒‒force**]
 | **vmm dt** *fqdn transport* [**‒‒force**]

A new transport for the indicated domain can be set with this subcommand.

The new transport will affect only those accounts for which the transport
has not been overridden.
If you want to restore the default to all accounts, you may pass the
option **‒‒force**.

Example:

.. code-block:: console

 root@host:~# vmm domaintransport support.example.com dovecot:
