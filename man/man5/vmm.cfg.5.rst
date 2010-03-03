=========
 vmm.cfg
=========

--------------------------
configuration file for vmm
--------------------------

:Author:         Pascal Volk <neverseen@users.sourceforge.net>
:Date:           2010-03-03
:Version:        vmm-0.6.0
:Manual group:   vmm Manual
:Manual section: 5

.. contents::
  :backlinks: top
  :class: htmlout

SYNOPSIS
========
vmm.cfg


DESCRIPTION
===========
|vmm(1)|_ reads its configuration data from *vmm.cfg*.

The configuration file is split into multiple sections. A section starts with
the section name, enclosed in square brackets '**[**' and '**]**', followed
by '*option* = *value*' pairs.

Whitespace around the '=' and at the end of a value is ignored.

Empty lines and lines starting with '#' or ';' will be ignored.

Each value uses one of the following data types:

* *Boolean* to indicate if something is enabled/activated (true) or
  disabled/deactivated (false).

  | Accepted values for *true* are: **1**, **yes**, **true** and **on**.
  | Accepted values for *false* are: **0**, **no**, **false** and **off**.

* *Int* an integer number, written without a fractional or decimal component.

  | For example **1**, **50** or **321** are integers.

* *String* a sequence of characters and numbers.

  | For example '**word**', '**hello world**' or '**/usr/bin/strings**'

Most options have a default value, shown in parentheses after the option's
name. In order to use a option's default setting, comment out the line,
either with a **#** or **;** or simply remove the setting from *vmm.cfg*.

A minimal *vmm.cfg* would be::

  [database]
  user = me
  pass = xxxxxxxx


SEARCH ORDER
-------------
By default |vmm(1)|_ looks for *vmm.cfg* in the following directories in the
order listed:

  | */root*
  | */usr/local/etc*
  | */etc*

The first configuration file found will be used.


SECTIONS
========
This section describes all sections and their options of the *vmm.cfg*.


ACCOUNT
-------
The options in the section **account** are used to specify user account
related settings.

.. _account.delete_directory:

``delete_directory (default: false)`` : *Boolean*
  Determines the behavior of |vmm(1)|_ when an account is deleted
  (|userdelete|_). If this option is set to *true* the user's home directory
  will be deleted  recursively.

.. _account.directory_mode:

``directory_mode (default: 448)`` : *Int*
  Access mode for a user's home directory and all directories inside. The
  value has to be specified in decimal (base 10) notation.

  | For example: 'drwx------' -> octal 0700 -> decimal 448

.. _account.disk_usage:

``disk_usage (default: false)`` : *Boolean*
  Determines whether the disk usage of a user's Maildir always should be
  summarized, using **du**\(1), and displayed with account information.

  This could be slow on large Maildirs. When you have enabled quotas,
  **vmm**'s |userinfo|_ subcomammand will also display the current quota
  usage of the account. You may also use |userinfo|_'s optional argument
  **du** or **full**, in order to display the current disk usage of an
  account's Maildir.

.. _account.imap:

``imap (default: true)`` : *Boolean*
  Determines whether a newly created user can log in via IMAP.

.. _account.password_length:

``password_length (default: 8)`` : *Int*
  Determines how many characters and/or numbers should be used for randomly
  generated passwords. Any value less than 8 will be increased to 8.

.. _account.pop3:

``pop3 (default: true)`` : *Boolean*
    Determines whether a newly created user can log in via POP3.

.. _account.random_password:

``random_password (default: false)`` : *Boolean*
  Determines whether **vmm** should generate a random password when no
  password was given for the |useradd|_ subcommand. If this option is set to
  *false* **vmm** will prompt you to enter a password for the new account.

  You can specify the password length of generated passwords with the
  |account.password_length|_ option.

.. _account.sieve:

``sieve (default: true)`` : *Boolean*
  Determines whether a newly created user can log in via ManageSieve.

.. _account.smtp:

``smtp (default: true)`` : *Boolean*
  Determines whether a newly created user can log in via SMTP (SMTP AUTH).

Example::

  [account]
  delete_directory = false
  directory_mode = 448
  disk_usage = false
  random_password = true
  password_length = 10
  smtp = true
  pop3 = true
  imap = true
  sieve = true


BIN
---
The **bin** section is used to specify some paths to some binaries required
by |vmm(1)|_.

.. _bin.dovecotpw:

``dovecotpw (default: /usr/sbin/dovecotpw)`` : *String*
  The absolute path to the dovecotpw binary. This binary is used to
  generate a password hash, if |misc.password_scheme|_ is set to one of
  'SMD5', 'SSHA', 'CRAM-MD5', 'HMAC-MD5', 'LANMAN', 'NTLM' or 'RPA'.

.. _bin.du:

``du (default: /usr/bin/du)`` : *String*
  The absolute path to **du**\(1). This binary is used to summarize the disk
  usage of a user's Maildir.

.. _bin.postconf:

``postconf (default: /usr/sbin/postconf)`` : *String*
  The absolute path to Postfix' |postconf(1)|_. This binary is required when
  |vmm(1)|_ has to check for some Postfix settings, e.g.
  |virtual_alias_expansion_limit|_.

Example::

  [bin]
  dovecotpw = /usr/sbin/dovecotpw
  du = /usr/bin/du
  postconf = /usr/sbin/postconf


DATABASE
--------
The **database** section is used to specify some options required to
connect to the database.

.. _database.host:

``host (default: localhost)`` : *String*
  Hostname or IP address of the database server.

.. _database.name:

``name (default: mailsys)`` : *String*
  Name of the database.

.. _database.pass:

``pass (default: None)`` : *String*
  Database password.

.. _database.user:

``user (default: None)`` : *String*
  Name of the database user.

Example::

  [database]
  host = localhost
  user = vmm
  pass = PY_SRJ}L/0p-oOk
  name = mailsys


DOMAIN
------
The **domain** section specifies some domain related settings.

.. _domain.auto_postmaster:

``auto_postmaster (default: true)`` : *Boolean*
  Determines if |vmm(1)|_ should create also a postmaster account when a new
  domain is created (|domainadd|_).

.. _domain.delete_directory:

``delete_directory (default: false)`` : *Boolean*
  Specifies whether the domain directory and all user directories inside
  should be deleted when a domain is deleted (|domaindelete|_).

.. _domain.directory_mode:

``directory_mode (default: 504)`` : *Int*
  Access mode for the domain directory in decimal (base 10) notation.

  | For example: 'drwxrwx---' -> octal 0770 -> decimal 504

.. _domain.force_deletion:

``force_deletion (default: false)`` : *Boolean*
  Force deletion of accounts and aliases when a domain is deleted
  (|domaindelete|_).

Example::

  [domain]
  auto_postmaster = true
  delete_directory = false
  directory_mode = 504
  force_deletion = false


MAILBOX
-------
The **mailbox** section is used to specify some options for new created
mailboxes in the users home directories. The INBOX will be created always.

.. _mailbox.folders:

``folders (default: Drafts:Sent:Templates:Trash)`` : *String*
  A colon separated list of mailboxes that should be created. (Works currently
  only if the |mailbox.format|_ is either **maildir** or **mbox**. For other
  formats use Dovecot's autocreate plugin
  <http://wiki.dovecot.org/Plugins/Autocreate>.) If no additionally mailboxes
  should be created, set the value of this option to a single colon ('**:**').

  If you want to create folders containing one or more subfolders, separate
  them with a single dot ('**.**').

.. _mailbox.format:

``format (default: maildir)`` : *String*
  The mailbox format to be used for a user's mailbox. Depending on the used
  Dovecot version there are up to four supported formats:

    ``maildir``
      since Dovecot v1.0.0
    ``mbox``
      since Dovecot v1.0.0
    ``dbox``
      since Dovecot v1.2.0
    ``mdbox``
      comes with Dovecot v2.0.0


Example::

  [mailbox]
  folders = Drafts:Sent:Templates:Trash:Lists.Dovecot:Lists.Postfix
  format = maildir

.. _imap_uft7:

.. note:: If you want to use internationalized mailbox names in the
  **folders** setting, you have to specify them in a modified version of the
  UTF-7 encoding (see :RFC:`3501`, section 5.1.3).

  Dovecot provides a useful utility for mUTF-7 <-> UTF-8 conversion:
  **imap-utf7**, it's available since Dovecot version 1.2.0.
..

imap-utf7 example::

  user@host:~$ /usr/local/libexec/dovecot/imap-utf7 -r Wysłane
  Wys&AUI-ane
  user@host:~$ /usr/local/libexec/dovecot/imap-utf7 "&AVo-mietnik"
  Śmietnik


MISC
----
The **misc** section is used to define miscellaneous settings.

.. _misc.base_directory:

``base_directory (default: /srv/mail)`` : *String*
  All domain directories will be created inside this directory.

.. _misc.password_scheme:

``password_scheme (default: CRAM-MD5)`` : *String*
  Password scheme to use (see also: **dovecotpw -l**).

.. _misc.gid_mail:

``gid_mail (default: 8)`` : *Int*
  Numeric group ID of group mail (`mail_privileged_group` from
  *dovecot.conf*)

.. _misc.transport:

``transport (default: dovecot:)`` : *String*
  Default transport for domains and accounts. For details see
  |transport(5)|_.

.. _misc.dovecot_version:

``dovecot_version (default: 12)`` : *Int*
  The concatenated major and minor version number of the currently used
  Dovecot version. (see: **dovecot --version**).

  When, for example, the command **dovecot --version** prints *1.1.18*, set
  the value of this option to **11**.

Example::

  [misc]
  base_directory = /srv/mail
  password_scheme = PLAIN
  gid_mail = 8
  transport = dovecot:
  dovecot_version = 11


FILES
=====
*/root/vmm.cfg*
  | will be used when found.
*/usr/local/etc/vmm.cfg*
  | will be used when the above file doesn't exist.
*/etc/vmm.cfg*
  | will be used when none of the both above mentioned files exists.


SEE ALSO
========
|vmm(1)|_


COPYING
=======
vmm and its manual pages were written by Pascal Volk and are licensed under
the terms of the BSD License.

.. include:: ../substitute_links.rst
.. include:: ../substitute_links_5.rst
