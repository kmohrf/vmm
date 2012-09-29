===================
General subcommands
===================

configget
---------
Syntax:
 | **vmm configget** *option*
 | **vmm cg** *option*

This subcommand is used to display the actual value of the given
configuration *option*.

Example:

.. code-block:: console

 root@host:~# vmm configget misc.crypt_sha512_rounds
 misc.crypt_sha512_rounds = 5000

.. versionadded:: 0.6.0

configset
---------
Syntax:
 | **vmm configset** *option value*
 | **vmm cs** *option value*

Use this subcommand to set or update a single configuration option's value.
*option* is the configuration option, *value* is the *option*'s new value.

.. note::
 This subcommand will create a new :file:`vmm.cfg` without any comments.
 Your current configuration file will be backed as :file:`vmm.cfg.bak`.

Example:

.. code-block:: console

 root@host:~# vmm configget domain.transport
 domain.transport = dovecot:
 root@host:~# vmm configset domain.transport lmtp:unix:private/dovecot-lmtp
 root@host:~# vmm cg domain.transport
 domain.transport = lmtp:unix:private/dovecot-lmtp

.. versionadded:: 0.6.0

configure
---------
Syntax:
 | **vmm configure** [*section*]
 | **vmm cf** [*section*]

Starts the interactive configuration for all configuration sections.

In this process the currently set value of each option will be displayed
in square brackets.
If no value is configured, the default value of each option will be
displayed in square brackets.
Press the return key, to accept the displayed value.

If the optional argument *section* is given, only the configuration options
from the given section will be displayed and will be configurable.
The following sections are available:

======== ==========================
section  description
======== ==========================
account  Account settings
bin      Paths to external binaries
database Database settings
domain   Domain settings
mailbox  Mailbox settings
misc     Miscellaneous settings
======== ==========================

All configuration options are described in :manpage:`vmm.cfg(5)`.

.. note::
 This subcommand will create a new :file:`vmm.cfg` without any comments.
 Your current configuration file will be backed as :file:`vmm.cfg.bak`.

Example:

.. code-block:: console

 root@host:~# vmm configure mailbox
 Using configuration file: /usr/local/etc/vmm.cfg

 * Configuration section: `mailbox'
 Enter new value for option folders [Drafts:Sent:Templates:Trash]:
 Enter new value for option format [maildir]: mdbox
 Enter new value for option subscribe [True]:
 Enter new value for option root [Maildir]: mdbox

getuser
-------
Syntax:
 | **vmm getuser** *uid*
 | **vmm gu** *ui*

If only the *uid* is available, for example from process list, the
subcommand **getuser** will show the user's address.

Example:

.. code-block:: console

 root@host:~# vmm getuser 79876
 Account information
 -------------------
         UID............: 79876
         GID............: 70704
         Address........: a.user@example.com

help
----
Syntax:
 | **vmm help** [*subcommand*]
 | **vmm h** [*subcommand*]

Prints a list of available subcommands with a short description to stdout.
When a *subcommand* was given, help for that *subcommand* will be displayed.
After this :command:`vmm` exits.

listaddresses
-------------
Syntax:
 | **vmm listaddresses** [*pattern*]
 | **vmm ll** [*pattern*]

This command lists all defined addresses. Addresses belonging to
alias-domains are prefixed with a '-', addresses of regular domains with
a '+'.
Additionally, the letters 'u', 'a', and 'r' indicate the type of each
address: user, alias and relocated respectively. The output can be limited
with an optional *pattern*.

To perform a wild card search, the **%** character can be used at the start
and/or the end of the *pattern*.

Example:

.. code-block:: console

 root@host:~# vmm ll example.com
 Matching addresses
 ------------------
         [u+] a.user@example.com
         [r+] b.user@example.com
         [u+] d.user@example.com
         [u+] john.doe@example.com
         [u+] postmaster@example.com
         [a+] support@example.com

.. versionadded:: 0.6.0

listaliases
-----------
Syntax:
 | **vmm listaliases** [*pattern*]
 | **vmm la** [*pattern*]

This command lists all defined aliases. Aliases belonging to alias-domains
are prefixed with a '-', addresses of regular domains with a '+'.
The output can be limited with an optional *pattern*.

To perform a wild card search, the **%** character can be used at the start
and/or the end of the *pattern*.

Example:

.. code-block:: console

 root@host:~# vmm listaliases example.com
 Matching aliases
 ----------------
         [+] support@example.com

.. versionadded:: 0.6.0

listdomains
-----------
Syntax:
 | **vmm listdomains** [*pattern*]
 | **vmm ld** [*pattern*]

This subcommand lists all available domains.
All domain names will be prefixed either with '[+]', if the domain is
a primary domain, or with '[-]', if it is an alias domain name.
The output can be limited with an optional pattern.

To perform a wild card search, the **%** character can be used at the start
and/or the end of the *pattern*.

Example:

.. code-block:: console

 root@host:~# vmm listdomains %example%
 Matching domains
 ----------------
         [+] example.com
         [-]     e.g.example.com
         [-]     example.name
         [+] example.net
         [+] example.org

listpwschemes
-------------
Syntax:
 | **vmm listpwschemes**
 | **vmm lp**

This subcommand lists all password schemes which could be used in the
:file:`vmm.cfg` as value of the *misc.password_scheme* option.
The output varies, depending on the used Dovecot version and the system's
libc.

When your Dovecot installation isn't too old, you will see additionally
a few usable encoding suffixes.
One of them can be appended to the password scheme.

Example:

.. code-block:: console

 root@host:~# vmm listpwschemes
 Usable password schemes
 -----------------------
         CRYPT SHA512-CRYPT LDAP-MD5 DIGEST-MD5 SHA256 SHA512 SSHA512
         SKEY SSHA NTLM RPA MD5-CRYPT HMAC-MD5 SHA1 PLAIN SHA CRAM-MD5
         SSHA256 MD5 LANMAN CLEARTEXT PLAIN-MD5 PLAIN-MD4 OTP SMD5
         SHA256-CRYPT

 Usable encoding suffixes
 ------------------------
         .B64 .BASE64 .HEX

.. versionadded:: 0.6.0

listrelocated
-------------
Syntax:
 | **vmm listrelocated** [*pattern*]
 | **vmm lr** [*pattern*]

This command lists all defined relocated addresses.
Relocated entries belonging to alias-domains are prefixed with a '-',
addresses of regular domains with a '+'.
The output can be limited with an optional *pattern*.

To perform a wild card search, the **%** character can be used at the start
and/or the end of the *pattern*.

Example:

.. code-block:: console

 root@host:~# vmm listrelocated example.com
 Matching relocated users
 ------------------------
         [+] b.user@example.com

.. versionadded:: 0.6.0

listusers
---------
Syntax:
 | **vmm listusers** [*pattern*]
 | **vmm lu** [*pattern*]

This command lists all user accounts.
User accounts belonging to alias-domains are prefixed with a '-', addresses
of regular domains with a '+'.
The output can be limited with an optional *pattern*.

To perform a wild card search, the **%** character can be used at the start
and/or the end of the *pattern*.

Example:

.. code-block:: console

 root@host:~# vmm listusers example.com
 Matching user accounts
 ----------------------
         [+] a.user@example.com
         [+] d.user@example.com
         [+] john.doe@example.com
         [+] postmaster@example.com

.. versionadded:: 0.6.0

version
-------
Syntax:
 | **vmm version**
 | **vmm v**

Prints :command:`vmm`'s version and copyright information to stdout.
After this :command:`vmm` exits.
