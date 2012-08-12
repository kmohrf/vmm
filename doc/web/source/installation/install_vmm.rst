==============
Installing vmm
==============
After you've prepared everything, it's time to install vmm.
Change into the :file:`vmm-0.6.0` directory an execute the
:file:`install.sh` script.
You can adjust the installation prefix by modifying line 8 of the script.

.. code-block:: console

 root@host:~# cd /path/to/vmm-0.6.0
 root@host:/path/to/vmm-0.6.0# ./install.sh

 Don't forget to edit /usr/local/etc/vmm.cfg - or run: vmm cf
 and /etc/postfix/pgsql-*.cf files.

 root@host:/path/to/vmm-0.6.0#

pgsql-\*.cf files
-----------------
After executing the install script you have to edit all :file:`pgsql-{*}.cf`
files in `postconf -h config_directory`. For details see `pgsql_table(5)`_.

The used parameter values are:

========= =============
parameter value
========= =============
dbname    mailsys
hosts     localhost
password  some_password
user      postfix
========= =============

So it's easy to use just the :command:`sed` command, in order to edit all
files at once. For example:

.. code-block:: console

 root@host:~# sed -i "s|\bpostfix\b|_postfix|g" `postconf -h config_directory`/pgsql-*.cf
 root@host:~# sed -i "s|some_password|3Q>MO…|g" `postconf -h config_directory`/pgsql-*.cf
 root@host:~#

If your `sed` doesn't like the `-i` option (is unable to edit files in place),
you can do it with :command:`perl`:

.. code-block:: console

 # perl -pi -e "s|\bpostfix\b|_postfix|g" `postconf -h config_directory`/pgsql-*.cf

.. note:: Don't forget to start or restart Dovecot and Postfix.

vmm configure
-------------
Finally you have to edit your :file:`vmm.cfg`. You can edit the configuration
file in your favorite editor or execute :command:`vmm configure`.
vmm's configuration parameters are described in :manpage:`vmm.cfg(5)`.
The initial :doc:`../vmm.cfg` is also well documented.

Ready, set, go!
---------------
For a list of available subcommands execute :command:`vmm help`.
For details about the subcommands see :manpage:`vmm(1)` or continue reading
at :doc:`../howto`.

.. include:: ../ext_references.rst
