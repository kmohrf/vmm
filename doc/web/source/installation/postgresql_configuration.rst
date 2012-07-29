========================
PostgreSQL configuration
========================
Adjust pg_hba.conf
------------------
The connection to a PostgreSQL server can be established either through a
local Unix-domain socket or a TCP/IP socket. The :file:`pg_hba.conf` file
defines which users/groups are allowed to connect from which clients and
how they have to authenticate.
The :file:`pg_hba.conf` file is mostly stored in the database cluster's data
directory. The data directory is often :file:`/usr/local/pgsql/data` or
:file:`/var/lib/pgsql/data.` On Debian GNU/Linux systems the
:file:`pg_hba.conf` is located in :file:`/etc/postgresql/{VERSION}/{CLUSTER}`
(for example: :file:`/etc/postgresql/9.1/main`).

Some information about the :file:`pg_hba.conf` is available in the PostgreSQL
Wiki/`Client Authentication`_, even more detailed in the pg_hba.conf_
documentation.

For TCP/IP connections
^^^^^^^^^^^^^^^^^^^^^^
Add a line like the following to your :file:`pg_hba.conf` if you want to
connect via a TCP/IP connection to the PostgreSQL server.
Make sure to adjust the CIDR address if PostgreSQL is running on a
different system::

 # IPv4 local connections:
 host    mailsys     +mailsys    127.0.0.1/32          md5

For Unix-domain socket connections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you want to use PostgreSQL's local Unix domain socket for database
connections add a line like the second one to your :file:`pg_hba.conf`::

 # "local" is for Unix domain socket connections only
 local   mailsys     +mailsys                    md5
 local   all         all                         ident sameuser

.. note:: `ident sameuser` will not work, because `dovecot-auth` will be
   executed by the unprivileged user `doveauth`
   (see :ref:`System Preparation <doveauth>`), not by the `dovecot` user.

Create database users and the database
--------------------------------------
You should create some database users for vmm, Dovecot and Postfix as well
as their group.
Each of them will get different privileges granted.
Finally create a new database.

Create a database superuser, which will be able to create users and databases,
if necessary. If you have sudo privileges run:

.. code-block:: console

 user@host:~$ sudo su - postgres
 [sudo] password for user:
 postgres@host:~$ createuser -s -d -r -E -e -P $USERNAME

If you are root, omit the :command:`sudo` command. Just execute
:command:`su - postgres` and create the database superuser.

Start :command:`psql` as superuser and connect to the database `template1`:

.. code-block:: console

 user@host:~$ psql template1

Then create users, their group and the empty database:

.. code-block:: postgresql-console

 template1=# CREATE ROLE vmm LOGIN ENCRYPTED PASSWORD 'DB PASSWORD for vmm';
 template1=# CREATE ROLE dovecot LOGIN ENCRYPTED password 'DB PASSWORD for Dovecot';
 template1=# CREATE ROLE postfix LOGIN ENCRYPTED password 'DB PASSWORD for Postfix';
 template1=# CREATE ROLE mailsys WITH USER postfix, dovecot, vmm;
 template1=# CREATE DATABASE mailsys WITH OWNER vmm ENCODING 'UTF8';
 template1=# \q

Import tables and functions
---------------------------
Now start :command:`psql` and connect as your `vmm` user to the database
`mailsys`:

.. code-block:: console

 user@host:~$ psql mailsys vmm -W -h localhost

In PostgreSQL's terminal-based front-end import the database layout/tables
and functions into your database.

Dovecot v1.2.x/v2.0.x/v2.1.x
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: postgresql-console

 mailsys=> \i /path/to/vmm-0.6.0/pgsql/create_tables-dovecot-1.2.x.pgsql
 mailsys=> \q

Dovecot v1.0.x/v1.1.x
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: postgresql-console

 mailsys=> \i /path/to/vmm-0.6.0/pgsql/create_tables.pgsql
 mailsys=> \q

Set database permissions
------------------------
.. include:: ../pgsql_set_permissionspermissions.rst

.. include:: ../ext_references.rst
