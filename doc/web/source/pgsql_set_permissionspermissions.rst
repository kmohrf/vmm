There's a python script which grants permissions to your Dovecot and Postfix
database users.

.. code-block:: console

 user@host:~$ python /path/to/vmm-0.6.0/pgsql/set-permissions.py -h
 Usage: set-permissions.py OPTIONS
 
 Set permissions for Dovecot and Postfix in the vmm database.
 
 Options:
   -h, --help            show this help message and exit
   -a, --askpass         Prompt for the database password.
   -H HOST, --host=HOST  Hostname or IP address of the database server. Leave
                         blank in order to use the default Unix-domain socket.
   -n NAME, --name=NAME  Specifies the name of the database to connect to.
                         Default: mailsys
   -p PASS, --pass=PASS  Password for the database connection.
   -P PORT, --port=PORT  Specifies the TCP port or the local Unix-domain socket
                         file extension on which the server is listening for
                         connections. Default: 5432
   -U USER, --user=USER  Connect to the database as the user USER instead of
                         the default: root
   -D USER, --dovecot=USER
                         Database user name of the Dovecot database user.
                         Default: dovecot
   -M USER, --postfix=USER
                         Database user name of the Postfix (MTA)  database
                         user. Default: postfix
 user@host:~$ python /path/to/vmm-0.6.0/pgsql/set-permissions.py -a -H 127.0.0.1 -U vmm
 Password: 
 user@host:~$ 

