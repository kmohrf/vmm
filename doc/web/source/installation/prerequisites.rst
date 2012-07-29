==========================
Installation Prerequisites
==========================
You already should have installed and configured Postfix and Dovecot with
PostgreSQL support. You also need access to a local or remote PostgreSQL
server.

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

vmm depends on Python (≥ 2.4.0) and Psycopg_ (≥ 2.0) or pyPgSQL_ (≥ 2.5.1)
[#]_. Psycopg and pyPgSQL are depending on parts of the *eGenix.com mx Base
Distribution* (mxDateTime_ and mxTools_).

If you are using Python ≤ 2.5.0:

 ‣ if you want to store your users' passwords as ``PLAIN-MD4`` digest in
   the database, vmm will try to use ``Crypto.Hash.MD4`` from PyCrypto_
 ‣ if you are using Dovecot ≥ v1.1.0 and you want to store your users'
   passwords as ``SHA256`` or ``SSHA256`` hashes, vmm will try to use
   ``Crypto.Hash.SHA256`` from PyCrypto. For ``SHA256``/``SSHA256`` you
   should have installed PyCrypto, at least in version 2.1.0alpha1.

 When the Crypto.Hash module couldn't be imported, vmm will use
 dovecotpw/doveadm, if  the *misc.password_scheme* setting in your
 :file:`vmm.cfg` is set to ``PLAIN-MD4``, ``SHA256`` or ``SSHA256``.

If your Dovecot and/or Postfix installation shouldn't support PostgreSQL you
could possibly fix this by installing the missing package (see below) or by
recompiling the corresponding part.

Package names by OS/Distribution
--------------------------------
Debian GNU/Linux (Squeeze/Wheezy)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
 ‣ `postfix <http://packages.debian.org/postfix>`_ and
   `postfix-pgsql <http://packages.debian.org/postfix-pgsql>`_
 ‣ Squeeze:

   * `dovecot-common <http://packages.debian.org/dovecot-common>`_

 ‣ Wheezy (and Squeeze backports):

   * `dovecot-core <http://packages.debian.org/dovecot-core>`_ and
     `dovecot-lmtpd <http://packages.debian.org/dovecot-lmtpd>`_

 ‣ `dovecot-imapd <http://packages.debian.org/dovecot-imapd>`_ and/or
   `dovecot-pop3d <http://packages.debian.org/dovecot-pop3d>`_
 ‣ `postgresql-client <http://packages.debian.org/postgresql-client>`_
   (or `postgresql <http://packages.debian.org/postgresql>`_ , if you do not
   have a dedicated PostgreSQL server.)
 ‣ `python <http://packages.debian.org/python>`_,
   `python-egenix-mxdatetime \
   <http://packages.debian.org/python-egenix-mxdatetime>`_
   and `python-psycopg2 <http://packages.debian.org/python-psycopg2>`_
   optionally `python-crypto <http://packages.debian.org/python-crypto>`_
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

OpenBSD
^^^^^^^
Packages or build from ports:
 ‣ postfix
 ‣ dovecot
 ‣ postgresql-client
 ‣ python and py-mxDateTime optionally py-crypto

Build from source:
 ‣ pyPgSQL_

openSUSE Linux
^^^^^^^^^^^^^^
 ‣ postfix and postfix-postgresql
 ‣ postgresql-server and postgresql
 ‣ dovecot
 ‣ python and pyPgSQL optionally python-crypto


.. rubric:: Footnotes
.. [#] Beginning with version 0.7.0 of vmm support for pyPgSQL will be dropped.

.. include:: ../ext_references.rst
