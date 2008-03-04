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

# Create new tables
queries = ("CREATE SEQUENCE transport_id",
        """CREATE TABLE transport (
    tid         bigint NOT NULL DEFAULT nextval('transport_id'),
    transport   varchar(270) NOT NULL,
    CONSTRAINT pkey_transport PRIMARY KEY (tid),
    CONSTRAINT ukey_transport UNIQUE (transport)
)""",
        "INSERT INTO transport(transport) VALUES ('dovecot:')",
        "CREATE SEQUENCE maillocation_id",
        """CREATE TABLE maillocation(
    mid     bigint NOT NULL DEFAULT nextval('maillocation_id'),
    maillocation varchar(20) NOT NULL,
    CONSTRAINT pkey_maillocation PRIMARY KEY (mid),
    CONSTRAINT ukey_maillocation UNIQUE (maillocation)
)""",
        "INSERT INTO maillocation(maillocation) VALUES ('Maildir')"
        )
for query in queries:
    dbc.execute(query)
dbh.commit()


# fix table domains (Part I)
dbc.execute('ALTER TABLE domains ADD tid bigint NOT NULL DEFAULT 1')
dbh.commit()
dbc.execute("ALTER TABLE domains ADD CONSTRAINT fkey_domains_tid_transport \
 FOREIGN KEY (tid) REFERENCES transport (tid)")
dbh.commit()

dbc.execute("SELECT DISTINCT transport from domains \
 WHERE transport != 'dovecot:'")
res = dbc.fetchall()
if len(res):
    for trsp in res:
        dbc.execute("INSERT INTO transport(transport) VALUES (%s)", trsp[0])
    dbh.commit()

    dbc.execute("SELECT tid, transport FROM transport WHERE tid > 1")
    res = dbc.fetchall()
    for tid, trsp in res:
        dbc.execute("UPDATE domains SET tid = %s WHERE transport = %s", tid,
                trsp)
    dbh.commit()


# fix table users (Part I)
dbc.execute("ALTER TABLE users ADD mid bigint NOT NULL DEFAULT 1")
dbh.commit()
dbc.execute("ALTER TABLE users ADD tid bigint NOT NULL DEFAULT 1")
dbh.commit()
dbc.execute("ALTER TABLE users ADD CONSTRAINT fkey_users_mid_maillocation \
 FOREIGN KEY (mid) REFERENCES maillocation (mid)")
dbh.commit()
dbc.execute("ALTER TABLE users ADD CONSTRAINT fkey_users_tid_transport \
 FOREIGN KEY (tid) REFERENCES transport (tid)")
dbh.commit()

dbc.execute("SELECT DISTINCT mail FROM users WHERE mail != 'Maildir'")
res = dbc.fetchall()
if len(res):
    for mailloc in res:
        dbc.execute("INSERT INTO maillocation(maillocation) VALUES (%s)",
                mailloc[0])
    dbh.commit()

    dbc.execute("SELECT mid, maillocation FROM maillocation WHERE mid > 1")
    res = dbc.fetchall()
    for mid, mailloc in res:
        dbc.execute("UPDATE users SET mid = %s WHERE mail = %s", mid,
                maillocation)
    dbh.commit()

dbc.execute("SELECT gid, tid FROM domains")
res = dbc.fetchall()
for gid, tid in res:
    dbc.execute("UPDATE users SET tid = %s WHERE gid = %s", tid, gid)
dbh.commit()


# Update VIEW postfix_maildir
dbc.execute("""CREATE OR REPLACE VIEW postfix_maildir AS
     SELECT local_part || '@' || domains.domainname AS address,
     domains.domaindir||'/'||uid||'/'||maillocation.maillocation||'/' AS maildir
       FROM users
            LEFT JOIN domains USING (gid)
            LEFT JOIN maillocation USING (mid)""")
dbh.commit()

# Update VIEW dovecot_user
dbc.execute("""CREATE OR REPLACE VIEW dovecot_user AS
    SELECT local_part || '@' || domains.domainname AS userid,
           domains.domaindir || '/' || uid AS home, uid, gid
      FROM users
           LEFT JOIN domains USING (gid)""")
dbh.commit()

# fix table users (Part II)
dbc.execute("ALTER TABLE users DROP home")
dbh.commit()
dbc.execute("ALTER TABLE users DROP mail")
dbh.commit()


# Replace VIEW postfix_transport
dbc.execute("DROP VIEW postfix_transport")
dbh.commit()
dbc.execute("""CREATE OR REPLACE VIEW postfix_transport AS
    SELECT local_part || '@' || domains.domainname AS address,
           transport.transport
      FROM users
           LEFT JOIN transport USING (tid)
           LEFT JOIN domains USING (gid)""")
dbh.commit()


# fix table domains (Part II)
dbc.execute("ALTER TABLE domains DROP transport")
dbh.commit()


# fix table alias
dbc.execute('ALTER TABLE alias DROP id')
dbh.commit()
dbc.execute('DROP SEQUENCE alias_id')
dbh.commit()


# fix table relocated
dbc.execute('ALTER TABLE relocated DROP id')
dbh.commit()
dbc.execute('DROP SEQUENCE relocated_id')
dbh.commit()


# add new VIEW vmm_domain_info
dbc.execute("""CREATE OR REPLACE VIEW vmm_domain_info AS
    SELECT gid, domainname, transport, domaindir, count(uid) AS accounts,
           aliases
      FROM domains
           LEFT JOIN transport USING (tid)
           LEFT JOIN users USING (gid)
           LEFT JOIN vmm_alias_count USING (gid)
  GROUP BY gid, domainname, transport, domaindir, aliases""")
dbh.commit()
dbh.close()
