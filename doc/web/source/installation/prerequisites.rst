==========================
Installation Prerequisites
==========================
You already should have installed and configured Postfix and Dovecot
≥ 2.0.0 with PostgreSQL support. You also need access to a local or remote
PostgreSQL server.

Check for pgsql support in Dovecot and Postfix
----------------------------------------------
To verify that your Dovecot and Postfix installation has support for
PostgreSQL use the :command:`postconf` and :command:`dovecot` commands as
shown below:

.. code-block:: console

  root@host:~# postconf -m | grep pgsql
  pgsql
  root@host:~# postconf -a | grep dovecot
  dovecot
  root@host:~# dovecot --build-options | grep postgresql
  SQL drivers: mysql postgresql sqlite

vmm depends on Python (≥ 3.2) and Psycopg_ (≥ 2.0).

If your Dovecot and/or Postfix installation shouldn't support PostgreSQL you
could possibly fix this by installing the missing package (see below) or by
recompiling the corresponding part.

Package names by OS/Distribution
--------------------------------
Debian GNU/Linux (Wheezy)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 ‣ `postfix <http://packages.debian.org/postfix>`_ and
   `postfix-pgsql <http://packages.debian.org/postfix-pgsql>`_
 ‣ `dovecot-core <http://packages.debian.org/dovecot-core>`_ and
   `dovecot-lmtpd <http://packages.debian.org/dovecot-lmtpd>`_
 ‣ `dovecot-imapd <http://packages.debian.org/dovecot-imapd>`_ and/or
   `dovecot-pop3d <http://packages.debian.org/dovecot-pop3d>`_
 ‣ `postgresql-client <http://packages.debian.org/postgresql-client>`_
   (or `postgresql <http://packages.debian.org/postgresql>`_ , if you do not
   have a dedicated PostgreSQL server.)
 ‣ `python3 <http://packages.debian.org/python3>`_ and
   `python3-psycopg2 <http://packages.debian.org/python3-psycopg2>`_
 ‣ `gettext <http://packages.debian.org/gettext>`_

FreeBSD
^^^^^^^
Packages or build from ports:
 ‣ dovecot
 ‣ postfix
 ‣ postgresql-client (and postgresql-server, if you do not have a dedicated
   PostgreSQL server.)
 ‣ python25, py25-mx-base and py25-pyPgSQL optionally py25-pycrypto

Gentoo Linux
^^^^^^^^^^^^
 ‣ `dev-python/pypgsql <http://gentoo-portage.com/dev-python/pypgsql>`_
 ‣ `mail-mta/postfix <http://gentoo-portage.com/mail-mta/postfix>`_
 ‣ `net-mail/dovecot <http://gentoo-portage.com/net-mail/dovecot>`_
 ‣ `dev-db/postgresql-base <http://gentoo-portage.com/dev-db/postgresql-base>`_
 ‣ `dev-db/postgresql-server \
   <http://gentoo-portage.com/dev-db/postgresql-server>`_

Applied use-Flags (/etc/portage/package.use)::

 mail-mta/postfix dovecot-sasl postgres -pam sasl
 net-mail/dovecot postgres -pam pop3d sieve
 dev-db/postgresql-server -perl

OpenBSD (5.2)
^^^^^^^^^^^^^
Packages
 ‣ postfix-2.x.y-pgsql
 ‣ dovecot-2.x.y and dovecot-postgresql-2.x.y
 ‣ postgresql-client
 ‣ python-3.2.x

Build from source
 ‣ Psycopg_

Or build the above mentioned software from ports.

openSUSE Linux
^^^^^^^^^^^^^^
 ‣ postfix and postfix-postgresql
 ‣ postgresql-server and postgresql
 ‣ dovecot
 ‣ python and pyPgSQL optionally python-crypto

.. include:: ../ext_references.rst
