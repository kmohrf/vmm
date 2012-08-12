============================
Managing catch-all addresses
============================
catchalladd
-----------
Syntax:
 | **vmm catchalladd** *fqdn destination ...*
 | **vmm caa** *fqdn destination ...*

This subcommand allows to specify destination addresses for a domain, which
shall receive mail addressed to unknown local-parts within that domain.
Those catch-all aliases hence "catch all" mail to  any address in the domain
(unless a more specific alias, mailbox or relocated entry exists).

.. warning::
   Catch-all addresses can cause mail server flooding because spammers like
   to deliver mail to all possible combinations of names, e.g. to all
   addresses between abba\@example.org and zztop\@example.org.

Example:

.. code-block:: console

 root@host:~# vmm catchalladd example.com user@example.org

.. versionadded:: 0.6.0

catchalldelete
--------------
Syntax:
 | **vmm catchalldelete** *fqdn* [*destination*]
 | **vmm cad** *fqdn* [*destination*]

With this subcommand, catch-all aliases defined for a domain can be removed,
either all of them, or a single one if specified explicitly.

Example:

.. code-block:: console

 root@host:~# vmm catchalldelete example.com user@example.com

.. versionadded:: 0.6.0

catchallinfo
------------
Syntax:
 | **vmm catchallinfo** *fqdn*
 | **vmm cai** *fqdn*

This subcommand displays information about catch-all aliases defined for
a domain.

Example:

.. code-block:: console

 root@host:~# vmm catchallinfo example.com
 Catch-all information
 ---------------------
   Mail to unknown localparts in domain example.com will be sent to:
          * user@example.org

.. versionadded:: 0.6.0

