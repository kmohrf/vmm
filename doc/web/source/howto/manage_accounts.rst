=================
Managing accounts
=================
useradd
-------
.. program:: vmm useradd

Syntax:
 | **vmm useradd** *address* [**-n** *note*] [**-p** *password*]
 | **vmm ua** *address* [**-n** *note*] [**-p** *password*]

.. option:: -n note

 the note that should be set

.. option:: -p password

 the new user's password

Use this subcommand to create a new e-mail account for the given *address*.

If the password is not provided, :command:`vmm` will prompt for it
interactively.
When no *password* is provided and *account.random_password* is set to
**true**, :command:`vmm` will generate a random password and print it to
stdout after the account has been created.

Example:

.. code-block:: console

 root@host:~# vmm ua d.user@example.com -p "A 5ecR3t P4s5\/\/0rd"
 root@host:~# vmm useradd e.user@example.com
 Enter new password:
 Retype new password:

userdelete
----------

.. program:: vmm userdelete

Syntax:
 | **vmm userdelete** *address* [**‒‒delete-directory**] [**‒‒force**]
 | **vmm ud** *address* [**‒‒delete-directory**] [**‒‒force**]

.. option:: --delete-directory

 When this option is present, :command:`vmm` will also delete the account's
 home directory.
 This overrides the *account.delete_directory* setting of :file:`vmm.cfg`.

.. option:: --force

 When this option is given, :command:`vmm` will delete the account, even if
 there are aliases with the account's address as their destination.
 Those aliases will be deleted too.

Use this subcommand to delete the account with the given *address*.

If there are one or more aliases with an identical destination address,
:command:`vmm` will abort the requested operation and show an error message.
To prevent this, give the optional argument :option:`--force`.

userinfo
--------
Syntax:
 | **vmm userinfo** *address* [**-d** *details*]
 | **vmm ui** *address* [**-d** *details*]

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
.. program:: vmm username

Syntax:
 | **vmm username** *address* **-d** | **-n** *name*
 | **vmm un** *address* **-d** | **-n** *name*

.. option:: -d

 delete the user's name

.. option:: -n name

 a user's real name

The user's real *name* can be set/updated with this subcommand.

In order to delete the value stored for the account, pass the :option:`-d`
option.

Example:

.. code-block:: console

 root@host:~# vmm un d.user@example.com -n "John Doe"

usernote
--------
.. program:: vmm usernote

Syntax:
 | **vmm usernote** *address* **-d** | **-n** *note*
 | **vmm uo** *address* **-d** | **-n** *note*

.. option:: -d

 delete the user's note

.. option:: -n note

 the note that should be set

With this subcommand, it is possible to attach a note to the specified
account.
In order to delete an existing note, pass the :option:`-d` option.

Example:

.. code-block:: console

 root@host:~# vmm uo d.user@example.com -n 'Only needed until end of May 2013'

.. versionadded:: 0.6.0

userpassword
------------
.. program:: vmm userpassword

Syntax:
 | **vmm userpassword** *address* ([**-p** *password*] [**-s** *scheme*] | \
  [**‒‒hash** *pwhash*])
 | **vmm up** *address* ([**-p** *password*] [**-s** *scheme*] | \
  [**‒‒hash** *pwhash*])

.. option:: -p password

 The user's new password.

.. option:: -s scheme

 When a *scheme* was specified, it overrides the *misc.password_scheme*
 setting, configured in the :file:`vmm.cfg` file.

.. option:: --hash pwhash

 A hashed password, prefixed with **{**\ *SCHEME*\ **}**; as generated by
 :command:`doveadm pw`.
 You should enclose the hashed password in single quotes, if it contains
 one ore more dollar signs (**$**).

The password of an account can be updated with this subcommand.

If no *password* or *pwhash* was provided, :command:`vmm` will prompt for a
password interactively.

.. note::
  When passing a hashed password, :command:`vmm` checks only if the included
  *SCHEME* is supported by your Dovecot installation.  No further checks are
  done.

Example:

.. code-block:: console

 root@host:~# vmm up d.user@example.com -p "A |\/|0r3 5ecur3 P4s5\/\/0rd?"

userquota
---------
Syntax:
 | **vmm userquota** *address storage* [**-m** *messages*]
 | **vmm uq** *address storage* [**-m** *messages*]

This subcommand is used to set a new quota limit for the given account.

When the argument *messages* was omitted the default number of messages
**0** (zero) will be applied.

Instead of a *storage* limit pass the keyword **domain** to remove the
account-specific override, causing the domain's value to be in effect.

Example:

.. code-block:: console

 root@host:~# userquota d.user@example.com 750m

.. versionadded:: 0.6.0

userservices
------------
Syntax:
 | **vmm userservices** *address* [**-s** *service ...*]
 | **vmm us** *address* [**-s** *service ...*]

To grant a user access to the specified services, use this command.

All omitted services will be deactivated/unusable for the user with the
given *address*.

Instead of any *service* pass the keyword **domain** to remove the
account-specific override, causing the domain's value to be in effect.

Example:

.. code-block:: console

 root@host:~# userservices d.user@example.com -s smtp imap

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
