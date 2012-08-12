======================
Managing alias domains
======================
An alias domain is an alias for a domain that was previously added with the
subcommand :ref:`domainadd`.
All accounts, aliases and relocated users from the domain will be also
available in the alias domain.
In the following is to be assumed that example.net is an alias for example.com.

Postfix will not accept erroneously e-mails for unknown.user\@example.net
and bounce them back later to the mostly faked sender.
Postfix will immediately reject all e-mails addressed to nonexistent users.

This behavior is ensured as long as you use the recommended database queries
in your :file:`{$config_directory}/pgsql-*.cf` configuration files.

aliasdomainadd
--------------
Syntax:
 | **vmm aliasdomainadd** *fqdn destination*
 | **vmm ada** *fqdn destination*

This subcommand adds the new alias domain (*fqdn*) to the *destination*
domain that should be aliased.

Example:

.. code-block:: console

 root@host:~# vmm aliasdomainadd example.net example.com

aliasdomaindelete
-----------------
Syntax:
 | **vmm aliasdomaindelete** *fqdn*
 | **vmm add** *fqdn*

Use this subcommand if the alias domain *fqdn* should be removed.

Example:

.. code-block:: console

 root@host:~# vmm aliasdomaindelete e.g.example.com

aliasdomaininfo
---------------
Syntax:
 | **vmm aliasdomaininfo** *fqdn*
 | **vmm adi** *fqdn*

This subcommand shows to which domain the alias domain *fqdn* is assigned to.

Example:

.. code-block:: console

 root@host:~# vmm adi example.net
 Alias domain information
 ------------------------
         The alias domain example.net belongs to:
             * example.com

aliasdomainswitch
-----------------
Syntax:
 | **vmm aliasdomainswitch** *fqdn destination*
 | **vmm aos** *fqdn destination*

If the destination of the existing alias domain *fqdn* should be switched
to another *destination* use this subcommand.

Example:

.. code-block:: console

 root@host:~# vmm aliasdomainswitch example.name example.org
