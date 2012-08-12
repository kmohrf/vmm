========================
Managing alias addresses
========================
aliasadd
--------
Syntax:
 | **vmm aliasadd** *address destination ...*
 | **vmm aa** *address destination ...*

This subcommand is used to create a new alias *address* with one or more
*destination* addresses.

Within the destination address, the placeholders **%n**, **%d**, and **%=**
will be replaced by the local-part, the domain, or the email address with
**@** replaced by **=** respectively.
In combination with alias domains, this enables domain-specific destinations.

Example:

.. code-block:: console

 root@host:~# vmm aliasadd john.doe@example.com d.user@example.com
 root@host:~# vmm aa support@example.com d.user@example.com e.user@example.com
 root@host:~# vmm aa postmaster@example.com postmaster+%d@example.org

aliasdelete
-----------
Syntax:
 | **vmm aliasdelete** *address* [*destination*]
 | **vmm ad** *address* [*destination*]

Use this subcommand to delete the alias with the given *address*.

If the optional *destination* address is given, only this destination will
be removed from the alias.

Example:

.. code-block:: console

 root@host:~# vmm ad support@example.com d.user@example.com

aliasinfo
---------
Syntax:
 | **vmm aliasinfo** *address*
 | **vmm ai** *address*

Information about the alias with the given *address* can be displayed with
this subcommand.

Example:

.. code-block:: console

 root@host:~# vmm aliasinfo support@example.com
 Alias information
 -----------------
         Mail for support@example.com will be redirected to:
              * e.user@example.com

