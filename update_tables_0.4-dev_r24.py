#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2008 VEB IT
# See COPYING for distribution information.
# $Id$

from ConfigParser import ConfigParser
from pyPgSQL import PgSQL

cff = file('/usr/local/etc/vmm.cfg', 'r')
cf = ConfigParser()
cf.readfp(cff)
cff.close()

dbh = PgSQL.connect(database=cf.get('database', 'name'),
        user=cf.get('database', 'user'), host=cf.get('database', 'host'),
        password=cf.get('database', 'pass'), client_encoding='utf8',
        unicode_results=True)
dbc = dbh.cursor()
dbc.execute("SET NAMES 'UTF8'")

for service in ['smtp', 'pop3', 'imap', 'managesieve']:
    dbc.execute(
            "ALTER TABLE users ADD %s boolean NOT NULL DEFAULT TRUE" % service)
    dbh.commit()

dbc.execute("SELECT uid FROM users WHERE disabled")
res = dbc.fetchall()
if len(res):
    for uid in res:
        dbc.execute("UPDATE users SET smtp = FALSE, pop3 = FALSE, imap = FALSE, managesieve = FALSE WHERE uid = %s", uid[0])
    dbh.commit()
dbc.execute("ALTER TABLE users DROP disabled")
dbh.commit()

dbc.execute("DROP VIEW dovecot_password")
dbh.commit()
dbc.execute("""CREATE OR REPLACE VIEW dovecot_password AS
    SELECT local_part || '@' || domains.domainname AS "user",
           passwd AS "password", smtp, pop3, imap, managesieve
      FROM users
           LEFT JOIN domains USING (gid)""")
dbh.commit()
dbh.close()

# print importnat information
print 
print "* set permissions for replaced views:"
print "connect to your database [psql %s] and execute:" % cf.get('database',
'name')
print "GRANT SELECT ON dovecot_password TO your_dovecot_dbuser;"
