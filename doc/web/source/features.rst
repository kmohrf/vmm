===============
Features of vmm
===============

General features
----------------
 ‣ Unicode/UTF-8 capable (input/storage/output)
 ‣ supports IDN_
 ‣ supports the mailbox format Maildir_ and Dovecot's own high-performance
   mailbox formats single- and multi-\ dbox_
 ‣ configurable basic mailbox structure, including sub-mailboxes
 ‣ multilingual — currently:

  * Dutch
  * English
  * Finnish
  * French
  * German
  * Vietnamese

Domain features
---------------
 ‣ configurable transport_ setting per domain
 ‣ unique group identifier (GID) per domain
 ‣ each domain may have one or more alias domain names
 ‣ activate or deactivate services (SMTP, POP3, IMAP and ManageSieve) for new
   or all accounts of a domain
 ‣ configurable quota limits (size and/or number of messages) for the
   domain's accounts
 ‣ supports relocated_ users
 ‣ the postmaster account can be created automatically when a new domain is
   created
 ‣ supports per-domain catch-all aliases

Alias domain features
---------------------
 ‣ alias domain names can be switched between domains

Account features
----------------
 ‣ configurable transport per account
 ‣ activate or deactivate one/more/all services (SMTP, POP3, IMAP and
   ManageSieve) per account
 ‣ configurable quota limit (size and/or number of messages) per user
 ‣ per-account configuration overrides defaults defined by the domain,
   otherwise the setting is inherited
 ‣ unique user identifier (UID) per user

Alias features
--------------
 ‣ supports multiple destinations per e-mail alias
 ‣ destinations can be deleted separately
 ‣ respects Postfix' virtual_alias_expansion_limit_ on creation
 ‣ destinations can be interpolated using the original address' local-part
   and domain, allowing aliases to have different meaning in alias domains,
   e.g. with the following defined in example.org::

    postmaster@example.org  →  postmaster+%d@admin.example.org

   If example.com is an alias domain of example.org, the alias will become::

    postmaster@example.org  →  postmaster+example.org@admin.example.org
    postmaster@example.com  →  postmaster+example.com@admin.example.org

Wanted features
---------------
 ‣ Do you want more? Please use the `issue tracker`_ to submit your proposal.

.. include:: ext_references.rst
