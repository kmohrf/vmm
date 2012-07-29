=====================
Dovecot configuration
=====================
This page describes in short how to configure Dovecot.

If you are upgrading your Dovecot installation from v1.\ **1**.x to
v1.\ **2**.x or v\ **1**.x to v\ **2**.x, you should also read Upgrading_
in the `Dovecot wiki`_.

Dovecot v1.x
------------
This setup uses two configuration files.
:file:`dovecot.conf`, the MainConfig_ of the Dovecot server and
:file:`dovecot-sql.conf`, containing the settings for passdb_ and userdb_
lookups.
For more details see also `AuthDatabase/SQL`_ in the Dovecot wiki.

dovecot.conf
^^^^^^^^^^^^
The following configuration example can be used as complete configuration
file. You can also adjust your existing settings.
Use :command:`dovecot -n | head -n 1` to locate your :file:`dovecot.conf`.

.. note:: Please modify the `postmaster_address` to meet your specific needs.

.. code-block:: text
 :emphasize-lines: 7

 # all your other settings
 #disable_plaintext_auth = no
 mail_location = maildir:~/Maildir
 first_valid_uid = 70000
 first_valid_gid = 70000
 protocol lda {
   postmaster_address = postmaster@YOUR-DOMAIN.TLD
   # uncomment this to use server side filtering (Dovecot v1.0.x/v1.1.x)
   #mail_plugins = cmusieve
   # uncomment this to use server side filtering (Dovecot v1.2.x)
   #mail_plugins = sieve
 }
 protocol pop3 {
   pop3_uidl_format = %08Xu%08Xv
 }
 # uncomment this to use the ManageSieve protocol, if supported by your installation
 #protocol managesieve {
 #  # only valid with Dovecot v1.0.x/v1.1.x.
 #  # see also: http://wiki.dovecot.org/ManageSieve/Configuration#v1.0.2BAC8-v1.1
 #  sieve = ~/.dovecot.sieve
 #  sieve_storage = ~/sieve
 #}
 auth default {
   mechanisms = cram-md5 login plain
   passdb sql {
     args = /etc/dovecot/dovecot-sql.conf
   }
   userdb sql {
     args = /etc/dovecot/dovecot-sql.conf
   }
   user = doveauth
   socket listen {
     master {
       path = /var/run/dovecot/auth-master
       mode = 0600
     }
     client {
       path = /var/spool/postfix/private/dovecot-auth
       mode = 0660
       user = postfix
       group = postfix
     }
   }
 }
 # uncomment this if you use the ManageSieve protocol with Dovecot v1.2.x
 #plugin {
 #  # Sieve and ManageSieve settings
 #  # see also: http://wiki.dovecot.org/ManageSieve/Configuration#v1.2
 #  sieve = ~/.dovecot.sieve
 #  sieve_dir = ~/sieve
 #}


.. _dovecot-sql-conf:

dovecot-sql.conf
^^^^^^^^^^^^^^^^
This lines contains all information that are required by Dovecot to access
the database and to do the lookups in passdb and userdb.

.. code-block:: text

 driver = pgsql
 connect = host=localhost dbname=mailsys user=dovecot password=$Dovecot_PASS
 default_pass_scheme = CRAM-MD5
 password_query = SELECT userid AS "user", password FROM dovecotpassword('%Ln', '%Ld') WHERE %Ls
 user_query = SELECT SELECT home, uid, gid, mail FROM dovecotuser('%Ln', '%Ld')

Dovecot v2.x
------------
Beginning with Dovecot version 2.0 the configuration was split into multiple
files.
It isn't required to use multiple configuration files.
:file:`dovecot.conf` is still the most important configuration file.
Use the command :command:`doveconf -n | head -n 1` to locate your
:file:`dovecot.conf`.
You could put all settings in your :file:`dovecot.conf`.
You can also include multiple files into your :file:`dovecot.conf`.

I personally prefer it to comment out most of the :file:`dovecot.conf`
and include only my :file:`local.conf`, which contains all the necessary 
settings.
You can download my :download:`local.conf <../_static/local.conf>` and use
it in your setup.

If you want to use multiple configuration files, you have to apply the
following settings to the configuration files mentioned down below.
Everything that isn't mentioned, was commented out.

.. _dovecot2.conf:

dovecot.conf
^^^^^^^^^^^^
.. code-block:: text

 protocols = imap lmtp
 # uncomment if your users should be able to manage their sieve scripts
 #protocols = imap lmtp sieve

 # uncomment if you want to use the quota plugin
 #dict {
 #  quota = pgsql:/usr/local/etc/dovecot/dovecot-dict-sql.conf.ext
 #}

See also :ref:`dovecot-dict-sql-conf-ext` below.

.. warning:: Adjust the paths of the :file:`dovecot-dict-sql.conf.ext`
   (above) and :file:`dovecot-sql.conf.ext` (below) files to suit your needs.


.. _conf-d-10-auth-conf:

conf.d/10-auth.conf
^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 auth_mechanisms = plain login cram-md5
 passdb {
   driver = sql
   args = /usr/local/etc/dovecot/dovecot-sql.conf.ext
 }
 userdb {
   driver = sql
   args = /usr/local/etc/dovecot/dovecot-sql.conf.ext
 }
 #!include auth-system.conf.ext

See also :ref:`dovecot-sql-conf-ext` below.


conf.d/10-mail.conf
^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 first_valid_gid = 70000
 first_valid_uid = 70000
 mail_access_groups = dovemail
 mail_location = maildir:~/Maildir
 
 # uncomment if you want to use the quota plugin
 #mail_plugins = quota

conf.d/10-master.conf
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 # if you don't want to use secure imap, you have to disable the imaps listener
 ##service imap-login {
 ##  inet_listener imaps {
 ##    port = 0
 ##  }
 ##}

 service lmtp {
   unix_listener /var/spool/postfix/private/dovecot-lmtp {
     user = postfix
     group = postfix
     mode = 0600
   }
 }

 service auth {
   user = doveauth
   unix_listener auth-userdb {
   }
   unix_listener /var/spool/postfix/private/dovecot-auth {
     user = postfix
     group = postfix
     mode = 0600
   }
 }

 service auth-worker {
   unix_listener auth-worker {
     user = doveauth
     group = $default_internal_user
     mode = 0660
   }
   user = doveauth
 }

 service dict {
   unix_listener dict {
     group = dovemail
     mode = 0660
   }
 }

conf.d/10-ssl.conf
^^^^^^^^^^^^^^^^^^
.. code-block:: text

 # SSL/TLS support: yes, no, required. <doc/wiki/SSL.txt>
 #ssl = yes

 ssl_cert = </etc/ssl/certs/dovecot.pem
 ssl_key = </etc/ssl/private/dovecot.pem

 # if you want to disable SSL/TLS, you have set 'ssl = no' and disable the
 # imaps listener in conf.d/10-master.conf

conf.d/15-lda.conf
^^^^^^^^^^^^^^^^^^
.. note:: Please modify the `postmaster_address` to meet your specific needs.

.. code-block:: text
 :emphasize-lines: 1

 postmaster_address = postmaster@YOUR-DOMAIN.TLD
 recipient_delimiter = +
 protocol lda {
   # uncomment if you want to use the quota plugin
   #mail_plugins = $mail_plugins
   # uncomment if you want to use the quota and sieve plugins
   #mail_plugins = $mail_plugins sieve
 }

conf.d/20-imap.conf
^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 protocol imap {
   # uncomment if you want to use the quota plugin
   #mail_plugins = $mail_plugins imap_quota
 }

conf.d/20-lmtp.conf
^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 protocol lmtp {
   # uncomment if you want to use the quota plugin
   #mail_plugins = $mail_plugins
   # uncomment if you want to use the quota and sieve plugins
   #mail_plugins = $mail_plugins sieve
 }

conf.d/90-quota.conf
^^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 # uncomment if you want to use the quota plugin
 #plugin {
 #  quota = dict:user:%{uid}::proxy::quota
 #  quota_rule = *:storage=0:messages=0
 #  quota_rule2 = Trash:storage=+100M
 #}

conf.d/90-sieve.conf
^^^^^^^^^^^^^^^^^^^^
.. code-block:: text

 # uncomment if you want to use sieve (and maybe managesieve)
 #plugin {
 #  recipient_delimiter = +
 #  sieve = ~/.dovecot.sieve
 #  sieve_dir = ~/sieve
 #}


.. _dovecot-sql-conf-ext:

dovecot-sql.conf.ext
^^^^^^^^^^^^^^^^^^^^
This file was referenced above in the `passdb` and `userdb` sections of
:ref:`conf-d-10-auth-conf`.

.. code-block:: text

 driver = pgsql
 connect = host=localhost dbname=mailsys user=dovecot password=$Dovecot_PASS
 
 password_query = \
  SELECT userid AS "user", password FROM dovecotpassword('%Ln', '%Ld') WHERE %Ls
 
 # uncomment this user_query if you want to use the quota plugin
 #user_query = \
 # SELECT home, uid, gid, mail, quota_rule FROM dovecotquotauser('%Ln', '%Ld')

 # otherwise uncomment the following user_query
 #user_query = SELECT home, uid, gid, mail FROM dovecotuser('%Ln', '%Ld')
 
 iterate_query = \
  SELECT local_part AS username, domain_name.domainname AS domain \
    FROM users \
         LEFT JOIN domain_data USING (gid) \
         LEFT JOIN domain_name USING (gid)


.. _dovecot-dict-sql-conf-ext:

dovecot-dict-sql.conf.ext
^^^^^^^^^^^^^^^^^^^^^^^^^
If you want to use the quota plugin add this lines to your
:file:`dovecot-dict-sql.conf.ext`.
This file was referenced in the `dict` section of :ref:`dovecot2.conf`.

.. code-block:: text

 connect = host=localhost dbname=mailsys user=dovecot password=$Dovecot_PASS
 map {
   pattern = priv/quota/storage
   table = userquota
   username_field = uid
   value_field = bytes
 }
 map {
   pattern = priv/quota/messages
   table = userquota
   username_field = uid
   value_field = messages
 }

.. include:: ../ext_references.rst
