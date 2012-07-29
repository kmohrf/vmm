=====================
Postfix configuration
=====================
This page mentions all Postfix configuration parameters, which have to be
modified and/or added in/to the Postfix :file:`main.cf`.

main.cf
-------
Add or replace the following configuration parameters in the global Postfix
configuration file.
The Postfix PostgreSQL client configuration files (:file:`pgsql-{*}.cf`)
mentioned below will be created when vmm will be installed.

.. code-block:: text

 sql      = pgsql:${config_directory}/
 proxysql = proxy:${sql}

 # relocated users from the database
 #relocated_maps = ${proxysql}pgsql-relocated_maps.cf
 
 # transport settings from our database
 transport_maps = ${proxysql}pgsql-transport_maps.cf
 
 # virtual domains, mailboxes and aliases
 virtual_mailbox_domains = ${proxysql}pgsql-virtual_mailbox_domains.cf
 virtual_alias_maps = ${proxysql}pgsql-virtual_alias_maps.cf
 virtual_minimum_uid = 70000
 virtual_uid_maps = ${sql}pgsql-virtual_uid_maps.cf
 virtual_gid_maps = ${sql}pgsql-virtual_gid_maps.cf
 virtual_mailbox_base = /
 virtual_mailbox_maps = ${proxysql}pgsql-virtual_mailbox_maps.cf
 
 # dovecot LDA (only recommended with Dovecot v1.x)
 #dovecot_destination_recipient_limit = 1
 #virtual_transport = dovecot:
 
 # dovecot lmtp (requires Dovecot ≧ v2.0.0)
 virtual_transport = lmtp:unix:private/dovecot-lmtp
 
 # dovecot SASL
 smtpd_sasl_type = dovecot
 smtpd_sasl_path = private/dovecot-auth
 smtpd_sasl_auth_enable = yes
 # Keep smtpd_sasl_local_domain identical to Dovecot's auth_default_realm:
 # empty. Both are empty by default. Let it commented out.
 # Read more at: http://wiki2.dovecot.org/Authentication/Mechanisms/DigestMD5
 #smtpd_sasl_local_domain =
 smtpd_sasl_security_options = noplaintext, noanonymous
 #broken_sasl_auth_clients = yes

 smtpd_recipient_restrictions =
  permit_mynetworks
  permit_sasl_authenticated
  reject_unauth_destination

mater.cf
--------
.. note:: This step is only necessary if you are still using Dovecot v\ **1**.x

Add the service `dovecot` to Postfix's master process configuration file.
Append this lines:

.. code-block:: text

 dovecot   unix  -       n       n       -       -       pipe
  flags=DORhu user=nobody argv=/usr/local/lib/dovecot/deliver -f ${sender}
  -d ${user}@${nexthop} -n -m ${extension}

The command of the `argv` attribute points to the
:ref:`root SETUID copy of deliver <root-setuid-copy-of-deliver>`.
For more details about the `flags` used above see: `pipe(8)`_.
All other arguments are explained in the Dovecot LDA_ documentation.

.. include:: ../ext_references.rst
