========================
Managing relocated users
========================
relocatedadd
------------
Syntax:
 | **vmm relocatedadd** *address newaddress*
 | **vmm ra** *address newaddress*

A new relocated user can be created with this subcommand.

*address* is the user's ex-email address, for example b.user\@example.com,
and *newaddress* points to the new email address where the user can be
reached.

Example:

.. code-block:: console

 root@host:~# vmm relocatedadd b.user@example.com b-user@company.tld

relocateddelete
---------------
Syntax:
 | **vmm relocateddelete** *address*
 | **vmm rd** *address*

Use this subcommand in order to delete the relocated user with the given
*address*.

Example:

.. code-block:: console

 root@host:~# vmm relocateddelete b.user@example.com

relocatedinfo
-------------
Syntax:
 | **vmm relocatedinfo** *address*
 | **vmm ri** *address*

This subcommand shows the new address of the relocated user with the given
*address*.

Example:

.. code-block:: console

 root@host:~# vmm relocatedinfo b.user@example.com
 Relocated information
 ---------------------
         User 'b.user@example.com' has moved to 'b-user@company.tld'
