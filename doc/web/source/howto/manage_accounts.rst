=================
Managing accounts
=================
useradd
-------
Syntax:
 | **vmm useradd** *address* [*password*]
 | **vmm ua** *address* [*password*]

Use this subcommand to create a new e-mail account for the given *address*.

If the password is not provided, :command:`vmm` will prompt for it
interactively.
When no *password* is provided and *account.random_password* is set to
**true**, :command:`vmm` will generate a random password and print it to
stdout after the account has been created.

Example:

.. code-block:: console

 root@host:~# vmm ua d.user@example.com "A 5ecR3t P4s5\/\/0rd"
 root@host:~# vmm useradd e.user@example.com
 Enter new password:
 Retype new password:

userdelete
----------
Syntax:
 | **vmm userdelete** *address* [*force*]
 | **vmm ud** *address* [*force*]

Use this subcommand to delete the account with the given *address*.

If there are one or more aliases with an identical destination address,
:command:`vmm` will abort the requested operation and show an error message.
To prevent this, specify the optional keyword **force**.

userinfo
--------
Syntax:
 | **vmm userinfo** *address* [*details*]
 | **vmm ui** *address* [*details*]

This subcommand displays some information about the account specified by
*address*.

If the optional argument *details* is given some more information will be
displayed.
Possible values for *details* are:

======= ==============================================================
value   description
======= ==============================================================
aliases to list all alias addresses with the destination *address*
du      to display the disk usage of the user's mail directory.
        In order to summarize the disk usage each time this subcommand
        is executed automatically, set *account.disk_usage* in your
        :file:`vmm.cfg` to **true**.
full    to list all information mentioned above
======= ==============================================================

Example:

.. code-block:: console

 root@host:~# vmm ui d.user@example.com
 Account information
 -------------------
         Address..........: d.user@example.com
         Name.............: None
         UID..............: 79881
         GID..............: 70704
         Home.............: /srv/mail/2/70704/79881
         Mail_Location....: mdbox:~/mdbox
         Quota Storage....: [  0.00%] 0/500.00 MiB [domain default]
         Quota Messages...: [  0.00%] 0/10,000 [domain default]
         Transport........: lmtp:unix:private/dovecot-lmtp [domain default]
         SMTP.............: disabled [domain default]
         POP3.............: disabled [domain default]
         IMAP.............: enabled [domain default]
         SIEVE............: enabled [domain default]

username
--------
Syntax:
 | **vmm username** *address* [*name*]
 | **vmm un** *address* [*name*]

The user's real *name* can be set/updated with this subcommand.

If no *name* is given, the value stored for the account is erased.

Example:

.. code-block:: console

 root@host:~# vmm un d.user@example.com "John Doe"

usernote
--------
Syntax:
 | **vmm usernote** *address* [*note*]
 | **vmm uo** *address* [*note*]

With this subcommand, it is possible to attach a note to the specified
account.
Without an argument, an existing note is removed.

Example:

.. code-block:: console

 root@host:~# vmm uo d.user@example.com Only needed until end of May 2012

.. versionadded:: 0.6.0

userpassword
------------
Syntax:
 | **vmm userpassword** *address* [*password*]
 | **vmm up** *address* [*password*]

The password of an account can be updated with this subcommand.

If no *password* was provided, :command:`vmm` will prompt for it interactively.

Example:

.. code-block:: console

 root@host:~# vmm up d.user@example.com "A |\/|0r3 5ecur3 P4s5\/\/0rd?"

userquota
---------
Syntax:
 | **vmm userquota** *address storage* [*messages*]
 | **vmm uq** *address storage* [*messages*]

This subcommand is used to set a new quota limit for the given account.

When the argument *messages* was omitted the default number of messages
**0** (zero) will be applied.

Instead of *storage* pass **domain** to remove the account-specific
override, causing the domain's value to be in effect.

Example:

.. code-block:: console

 root@host:~# userquota d.user@example.com 750m

.. versionadded:: 0.6.0

userservices
------------
Syntax:
 | **vmm userservices** *address* [*service ...*]
 | **vmm us** *address* [*service ...*]

To grant a user access to the specified services, use this command.

All omitted services will be deactivated/unusable for the user with the
given *address*.

Instead of *service* pass **domain** to remove the account-specific override,
causing the domain's value to be in effect.

Example:

.. code-block:: console

 root@host:~# userservices d.user@example.com SMTP IMAP

.. _usertransport:

usertransport
-------------
Syntax:
 | **vmm usertransport** *address transport*
 | **vmm ut** *address transport*

A different *transport* for an account can be specified with this subcommand.

Instead of *transport* pass **domain** to remove the account-specific
override, causing the domain's value to be in effect.

Example:

.. code-block:: console

 root@host:~# ut c.user@example.com smtp:[pc105.it.example.com]
