=====
 vmm
=====

----------------------------------------------------------
command line tool to manage email domains/accounts/aliases
----------------------------------------------------------

:Author:         Pascal Volk <neverseen@users.sourceforge.net>
:Date:           2010-08-01
:Version:        vmm-0.6.0
:Manual group:   vmm Manual
:Manual section: 1

.. contents::
  :backlinks: top
  :class: htmlout

SYNOPSIS
========
**vmm** *subcommand* *object* [ *arguments* ]


DESCRIPTION
===========
**vmm** (a virtual mail manager) is a command line tool for
administrators/postmasters to manage (alias) domains, accounts and alias
addresses. It's designed for Dovecot and Postfix with a PostgreSQL backend.


SUBCOMMANDS
===========
Each subcommand has both a long and a short form. The short form is shown
enclosed in parentheses. Both forms are case sensitive.


GENERAL SUBCOMMANDS
-------------------
.. _configget:

``configget (cg) option``
  This subcommand is used to display the actual value of the given
  configuration *option*. The option has to be written as
  *section*\ **.**\ *option*, e.g. **misc.transport**.

.. _configset:

``configset (cs) option value``
  Use this subcommand to set/update a single configuration option. *option*
  is the configuration option, written as *section*\ **.**\ *option*. *value*
  is the *option*'s new value.

  Example::

    vmm configget misc.transport
    misc.transport = dovecot:
    vmm configset misc.transport lmtp:unix:private/dovecot-lmtp
    vmm cg misc.transport
    misc.transport = lmtp:unix:private/dovecot-lmtp

.. _configure:

``configure (cf) [ section ]``
  Starts the interactive configuration for all configuration sections.

  In this process the currently set value of each option will be shown in
  square brackets. If no value is configured, the default value of each
  option will be displayed in square brackets. Pres the enter key, to accept
  the displayed value.

  If the optional argument *section* is given, only the configuration
  options from the given section will be displayed and will be
  configurable. The following sections are available:

  | - **account**
  | - **bin**
  | - **database**
  | - **domain**
  | - **maildir**
  | - **misc**

  Example::

    vmm configure domain
    Using configuration file: /usr/local/etc/vmm.cfg

    * Configuration section: “domain”
    Enter new value for option directory_mode [504]:
    Enter new value for option delete_directory [True]: no
    Enter new value for option auto_postmaster [True]:
    Enter new value for option force_deletion [True]: off

.. _getuser:

``getuser (gu) userid``
  If only the *userid* is available, for example from process list, the
  subcommand **getuser** will show the user's address.

  Example::

    vmm getuser 70004
    Account information
    -------------------
            UID............: 70004
            GID............: 70000
            Address........: c.user@example.com

.. _listdomains:

``listdomains (ld) [ pattern ]``
  This subcommand lists all available domains. All domain names will be
  prefixed either with '[+]', if the domain is a primary domain, or with
  '[-]', if it is an alias domain name. The output can be limited with an
  optional *pattern*.

  To perform a wild card search, the **%** character can be used at the
  start and/or the end of the *pattern*.

  Example::

    vmm listdomains %example%
    Matching domains
    ----------------
            [+] example.com
            [-]     e.g.example.com
            [-]     example.name
            [+] example.net
            [+] example.org

.. _help:

``help (h)``
  Prints all available subcommands to stdout. After this **vmm** exits.

.. _version:

``version (v)``
  Prints the version information from **vmm**.


DOMAIN SUBCOMMANDS
------------------
.. _domainadd:

``domainadd (da) domain [ transport ]``
  Adds the new *domain* into the database and creates the domain directory.

  If the optional argument *transport* is given, it will overwrite the
  default transport (|misc.transport|_) from |vmm.cfg(5)|_. The specified
  *transport* will be the default transport for all new accounts in this
  domain.

  Examples::

    vmm domainadd support.example.com smtp:mx1.example.com
    vmm domainadd sales.example.com

.. _domaininfo:

``domaininfo (di) domain [ details ]``
  This subcommand shows some information about the given *domain*.

  For a more detailed information about the *domain* the optional argument
  *details* can be specified. A possible *details* value may be one of the
  following five keywords:

  ``accounts``
    to list all existing accounts
  ``aliasdomains``
    to list all assigned alias domains
  ``aliases``
    to list all available aliases addresses
  ``relocated``
    to list all relocated users
  ``full``
    to list all information mentioned above

  Example::

    vmm domaininfo sales.example.com
    Domain information
    ------------------
            Domainname.....: sales.example.com
            GID............: 70002
            Transport......: dovecot:
            Domaindir......: /home/mail/5/70002
            Aliasdomains...: 0
            Accounts.......: 0
            Aliases........: 0
            Relocated......: 0

.. _domaintransport:

``domaintransport (dt) domain transport [ force ]``
  A new *transport* for the indicated *domain* can be set with this
  subcommand.

  If the additional keyword **force** is given all account specific
  transport settings will be overwritten. Otherwise this setting will affect
  only new created accounts.

  Example::

    vmm domaintransport support.example.com dovecot:

.. _domaindelete:

``domaindelete (dd) domain [ force ]``
  This subcommand deletes the specified *domain*.

  If there are accounts, aliases and/or relocated users assigned to the given
  domain, **vmm** will abort the requested operation and show an error
  message. If you know, what you are doing, you can specify the keyword
  **force**.

  If you really always know what you are doing, edit your *vmm.cfg* and set
  the option |domain.force_deletion|_ to true.


ALIAS DOMAIN SUBCOMMANDS
------------------------
.. _aliasdomainadd:

``aliasdomainadd (ada) aliasdomain targetdomain``
  This subcommand adds the new *aliasdomain* to the *targetdomain* that
  should be aliased.

  Example::

    vmm aliasdomainadd example.name example.com

.. _aliasdomaininfo:

``aliasdomaininfo (adi) aliasdomain``
  This subcommand shows to which domain the *aliasdomain* is assigned to.

  Example::

    vmm aliasdomaininfo example.name
    Alias domain information
    ------------------------
            The alias domain example.name belongs to:
                * example.com

.. _aliasdomainswitch:

``aliasdomainswitch (ads) aliasdomain targetdomain``
  If the target of the existing *aliasdomain* should be switched to another
  *targetdomain* use this subcommand.

  Example::

    vmm aliasdomainswitch example.name example.org

.. _aliasdomaindelete:

``aliasdomaindelete (add) aliasdomain``
  Use this subcommand if the alias domain *aliasdomain* should be removed.

  Example::

    vmm aliasdomaindelete e.g.example.com


ACCOUNT SUBCOMMANDS
-------------------
.. _useradd:

``useradd (ua) address [ password ]``
  Use this subcommand to create a new email account for the given *address*.

  If the *password* is not provided, **vmm** will prompt for it
  interactively.

  Examples::

    vmm ua d.user@example.com 'A 5ecR3t P4s5\\/\\/0rd'
    vmm ua e.user@example.com
    Enter new password:
    Retype new password:

.. _userinfo:

``userinfo (ui) address [ details ]``
  This subcommand displays some information about the account specified by
  *address*.

  If the optional argument *details* is given some more information will be
  displayed. Possible values for *details* are:

  ``aliases``
    to list all alias addresses with the destination *address*
  ``du``
    to display the disk usage of a user's Maildir. In order to summarize the
    disk usage each time the this subcommand is executed automatically, set
    |account.disk_usage|_ in the *vmm.cfg* to true.
  ``full``
    to list all information mentioned above

.. _username:

``username (un) address "User's Name"``
  The user's real name can be set/updated with this subcommand.

  Example::

    vmm un d.user@example.com 'John Doe'

.. _userpassword:

``userpassword (up) address [ password ]``
  The *password* from an account can be updated with this subcommand.

  If the *password* is not provided, **vmm** will prompt for it
  interactively.

  Example::

    vmm up d.user@example.com 'A |\\/|0r3 5ecur3 P4s5\\/\\/0rd?'

.. _usertransport:

``usertransport (ut) address transport``
  A different *transport* for an account can be specified with this
  subcommand.

  Example::

    vmm ut d.user@example.com smtp:pc105.it.example.com

.. _userdisable:

``userdisable (u0) address [ service ... ]``
  If a user shouldn't have access to one or more services you can restrict
  the access with this subcommand.

  If no *service* was given all services  (**smtp**, **pop3**, **imap**, and
  **sieve**) will be disabled for the account with the specified *address*.
  Otherwise only the specified *service*/s will be restricted.

  Examples::

    vmm u0 b.user@example.com imap pop3
    vmm userdisable c.user@example.com

.. _userenable:

``userenable (u1) address [ service ... ]``
  To allow access to one or more restricted services use this subcommand.

  If no *service* was given all services (**smtp**, **pop3**, **imap**, and
  **sieve**) will be enabled for the account with the specified *address*.
  Otherwise only the specified *service*/s will be enabled.

.. _userdelete:

``userdelete (ud) address [ force ]``
  Use this subcommand to delete the account with the given *address*.

  If there are one or more aliases with an identical destination *address*,
  **vmm** will abort the requested operation and show an error message. To
  prevent this, specify the optional keyword **force**.


ALIAS SUBCOMMANDS
-----------------
.. _aliasadd:

``aliasadd (aa) alias target``
  This subcommand is used to create a new alias.

  Examples::

    vmm aliasadd john.doe@example.com d.user@example.com
    vmm aa support@example.com d.user@example.com
    vmm aa support@example.com e.user@example.com

.. _aliasinfo:

``aliasinfo (ai) alias``
  Information about an alias can be displayed with this subcommand.

  Example::

    vmm aliasinfo support@example.com
    Alias information
    -----------------
            Mail for support@example.com will be redirected to:
                 * d.user@example.com
                 * e.user@example.com

.. _aliasdelete:

``aliasdelete (ad) alias [ target ]``
  Use this subcommand to delete the *alias*.

  If the optional destination address *target* is given, only this
  destination will be removed from the *alias*.

  Example::

    vmm ad support@example.com d.user@example.com


RELOCATED SUBCOMMANDS
---------------------
.. _relocatedadd:

``relocatedadd (ra) old_address new_address``
  A new relocated user can be created with this subcommand.

  *old_address* is the users ex-email address, for example
  b.user@example.com, and *new_address* points to the new email address
  where the user can be reached.

  Example::

    vmm relocatedadd b.user@example.com b-user@company.tld

.. _relocatedinfo:

``relocatedinfo (ri) old_address``
  This subcommand shows the new address of the relocated user with the
  *old_address*.

  Example::

    vmm relocatedinfo b.user@example.com
    Relocated information
    ---------------------
            User “b.user@example.com” has moved to “b-user@company.tld”

.. _relocateddelete:

``relocateddelete (rd) old_address``
  Use this subcommand in order to delete the relocated user with the
  *old_address*.

  Example::

    vmm relocateddelete b.user@example.com


FILES
=====
*/root/vmm.cfg*
  | will be used when found.
*/usr/local/etc/vmm.cfg*
  | will be used when the above file doesn't exist.
*/etc/vmm.cfg*
  | will be used when none of the both above mentioned files exists.


SEE ALSO
========
|vmm.cfg(5)|_


COPYING
=======
vmm and its manual pages were written by Pascal Volk and are licensed under
the terms of the BSD License.

.. include:: ../substitute_links.rst
.. include:: ../substitute_links_1.rst
