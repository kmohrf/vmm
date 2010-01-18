=========
 vmm.cfg
=========

--------------------------
configuration file for vmm
--------------------------

:Author:         Pascal Volk <neverseen@users.sourceforge.net>
:Date:           2010-01-18
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
**vmm**\(1) reads its configuration data from *vmm.cfg*.

The configuration file is split into multiple sections. A section starts with
the section name, enclosed in square brackets '**[**' and '**]**', followed
by '*option* = *value*' pairs::

    [database]
    host = 127.0.0.1

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

SEARCH ORDER
-------------
By default **vmm**\(1) looks for *vmm.cfg* in the following directories in the
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

``delete_directory`` : *Boolean*
    Determines the behavior of **vmm**\(1) when an account is deleted. If
    this option is set to *true* the user's home directory will be deleted
    recursively.

``directory_mode`` : *Int*
    Access mode for a user's home directory and all directories inside.
    The value has to be specified in decimal (base 10) notation.

    | For example: 'drwx------' -> octal 0700 -> decimal 448

``disk_usage`` : *Boolean*
    Determines whether the disk usage of a user's Maildir always should be
    summarized, using **du**\(1), and displayed with account information.

    This could be slow on large Maildirs. When you have enabled quotas,
    **vmm**'s **userinfo** subcomammand will also display the current quota
    usage of the account. You may also use **userinfo**'s optional argument
    **du** or **full**, in order to display the current disk usage of an
    account.

``imap`` : *Boolean*
    Determines whether a newly created user can log in via IMAP.

``password_length`` : *Int*
    Determines how many characters and/or numbers should be used for random
    generated passwords. Any value less than 8 will be increased to 8.

``pop3`` : *Boolean*
    Determines whether a newly created user can log in via POP3.

``random_password`` : *Boolean*
    Determines whether **vmm** should generate a random password when no
    password was given for the **useradd** subcommand. If this option is
    set to *false* **vmm** will prompt you to enter a password for the new
    account.

    You can specify the password length of generated passwords with the
    **password_length** option.

``sieve`` : *Boolean*
    Determines whether a newly created user can log in via ManageSieve.

``smtp`` : *Boolean*
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
by **vmm**\(1).

``dovecotpw`` : *String*
    The absolute path to the dovecotpw binary. This binary is used to
    generate a password hash, if **misc.password_scheme** is set to one of
    'SMD5', 'SSHA', 'CRAM-MD5', 'HMAC-MD5', 'LANMAN', 'NTLM' or 'RPA'.

``du`` : *String*
    The absolute path to **du**\(1). This binary is used to summarize the
    disk usage of a user's Maildir.

``postconf`` : *String*
    The absolute path to Postfix' **postconf**\(1). This binary is required
    when **vmm**\(1) has to check for some Postfix settings, e.g.
    `virtual_alias_expansion_limit`.

Example::

    [bin]
    dovecotpw = /usr/sbin/dovecotpw
    du = /usr/bin/du
    postconf = /usr/sbin/postconf

CONFIG
------
The **config** section is an internal used control section.

``done`` : *Boolean*
    This option is set to *false* when **vmm**\(1) is installed for the first
    time. When you edit *vmm.cfg*, set this option to *true*. This option is
    also set to *true* when you configure **vmm**\(1) with the command **vmm
    configure**.

    If this option is set to *false*, **vmm**\(1) will start in the
    interactive configurations mode.

Example::

    [config]
    done = true

DATABASE
--------
The **database** section is used to specify some options required to
connect to the database.

``host`` : *String*
    Hostname or IP address of the database server.

``name`` : *String*
    Name of the database.

``pass`` : *String*
    Database password.

``user`` : *String*
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

``auto_postmaster`` : *Boolean*
    Determines if **vmm**\(1) should create also a postmaster account when a
    new domain is created.

``delete_directory`` : *Boolean*
    Specifies whether the domain directory and all user directories inside
    should be deleted when a domain is deleted.

``directory_mode`` : *Int*
    Access mode for the domain directory in decimal (base 10) notation.

    | For example: 'drwxrwx---' -> octal 0770 -> decimal 504

``force_deletion`` : *Boolean*
    Force deletion of accounts and aliases when a domain is deleted.

Example::

    [domain]
    auto_postmaster = true
    delete_directory = false
    directory_mode = 504
    force_deletion = false

MAILDIR
-------
The **maildir** section is used to specify some default options for new
created Maildirs and folders inside.

``folders`` : *String*
    A colon separated list of folder names, that should be created. If no
    folders should be created inside the Maildir, set the value of this
    option to a single colon ('**:**').

    If you want to create folders containing one or more subfolders, separate
    them with a single dot ('**.**').

``name`` : *String*
    Default name of the Maildir folder in users home directories.

Example::

    [maildir]
    folders = Drafts:Sent:Templates:Trash:Lists.Dovecot:Lists.Postfix
    name = Maildir

MISC
----
The **misc** section is used to define miscellaneous settings.

``base_directory`` : *String*
    All domain directories will be created inside this directory.

``password_scheme`` : *String*
    Password scheme to use (see also: **dovecotpw -l**).

``gid_mail`` : *Int*
    Numeric group ID of group mail (`mail_privileged_group` from
    *dovecot.conf*)

``transport`` : *String*
    Default transport for domains and accounts. For details see
    **transport**\(5).

``dovecot_version`` : *Int*
    The concatenated major and minor version number of the currently used
    Dovecot version. (see: **dovecot --version**).

    This option affects various database operations. There are some
    differences between Dovecot v1.1.x and v1.2.x. For example, when the
    command **dovecot --version** shows 1.1.18, set the value of this option
    to **11**.

Example::

    [misc]
    base_directory = /srv/mail
    password_scheme = CRAM-MD5
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
vmm(1), command line tool to manage email domains/accounts/aliases

COPYING
=======
vmm and its manual pages were written by Pascal Volk and are licensed under
the terms of the BSD License.

