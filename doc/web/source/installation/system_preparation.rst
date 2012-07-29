==================
System Preparation
==================
.. _doveauth:

We have to create a system user, named `doveauth`.
The `doveauth` user will execute Dovecot's authentication processes.

We will also create an additional system group, named `dovemail`.
The GID of the group `dovemail` will be the supplementary GID for all
mail related Dovecot processes, e.g. the `dict` service for quota limits.

And finally we will create the ``base_directory``, with it's subdirectories.
It is the location for all domain directories and the virtual user's home
directories.

The example below shows the steps executed on a Debian GNU/Linux system.

.. code-block:: console

 root@host:~# adduser --system --home /nonexistent --no-create-home --group \
 > --disabled-login --gecos "Dovecot IMAP/POP3 authentication user" doveauth
 root@host:~# addgroup --system dovemail
 root@host:~# mkdir /srv/mail
 root@host:~# cd /srv/mail
 root@host:/srv/mail# mkdir 0 1 2 3 4 5 6 7 8 9 a b c d e f g h i j k l m n o p q r s t u v w x y z
 root@host:/srv/mail# chmod 771 /srv/mail
 root@host:/srv/mail# chmod 751 /srv/mail/*

.. _root-setuid-copy-of-deliver:

root SETUID copy of deliver
---------------------------
.. note:: This step is only necessary if you are still using Dovecot v\ **1**.x

For security reasons the permissions in the domain/user directories will
be very restricted.
Each user will get its own unique UID_ and the GID_ from the domain.
So it will be only possible for a user of the domain to access the domain
directory (read only) and the user will get granted read write access only
for its home directory.

For this reason it is necessary to provide a setuid_-root copy of Dovecot's
LDA_ (:command:`deliver`) for Postfix.
Because Postfix will refuse to execute commands with root privileges, or
with the privileges of the mail system owner (normally `postfix`) you should
`nobody` let do the job.
Therefore the permissions will be set very restrictive again.
Only `nobody` will be able to execute the setuid-root copy of
:command:`deliver`.

.. code-block:: console

 root@host:~# mkdir -p /usr/local/lib/dovecot
 root@host:~# chmod 700 /usr/local/lib/dovecot
 root@host:~# chown nobody /usr/local/lib/dovecot
 root@host:~# cp /usr/lib/dovecot/deliver /usr/local/lib/dovecot/
 root@host:~# chown root:`id -g nobody` /usr/local/lib/dovecot/deliver
 root@host:~# chmod u+s,o-rwx /usr/local/lib/dovecot/deliver

.. include:: ../ext_references.rst
