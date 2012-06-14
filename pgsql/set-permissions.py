#!/usr/bin/env python
# coding: utf-8
# Copyright 2012, Pascal Volk
# See COPYING for distribution information.

"""
    Use this script in order to set database permissions for your Dovecot
    and Postfix database users.

    Run `python set-permissions.py -h` for details.
"""

import getpass
import sys

from optparse import OptionParser

has_psycopg2 = False
try:
    import psycopg2
    has_psycopg2 = True
except ImportError:
    try:
        from pyPgSQL import PgSQL
    except ImportError:
        sys.stderr.write('error: no suitable database module found\n')
        raise SystemExit(1)

if has_psycopg2:
    DBErr = psycopg2.DatabaseError
else:
    DBErr = PgSQL.libpq.DatabaseError


def check_opts(opts, err_hdlr):
    if not opts.postfix:
        err_hdlr('missing Postfix database user name')
    if not opts.dovecot:
        err_hdlr('missing Dovecot database user name')
    if opts.askp:
        opts.dbpass = getpass.getpass()


def get_dbh(database, user, password, host, port):
    if has_psycopg2:
        return psycopg2.connect(database=database, user=user,
                                password=password, host=host, port=port)
    return PgSQL.connect(user=user, password=password, host=host,
                         database=database, port=port)


def get_optparser():
    descr = 'Set permissions for Dovecot and Postfix in the vmm database.'
    usage = 'usage: %prog OPTIONS'
    parser = OptionParser(description=descr, usage=usage)
    parser.add_option('-a', '--askpass', dest='askp', default=False,
            action='store_true', help='Prompt for the database password.')
    parser.add_option('-H', '--host', dest='host', metavar='HOST',
            default=None,
            help='Hostname or IP address of the database server. Leave ' +
                 'blank in order to use the default Unix-domain socket.')
    parser.add_option('-n', '--name', dest='name', metavar='NAME',
            default='mailsys',
            help='Specifies the name of the database to connect to. ' +
                 'Default: %default')
    parser.add_option('-p', '--pass', dest="dbpass", metavar='PASS',
            default=None, help='Password for the database connection.')
    parser.add_option('-P', '--port', dest='port', metavar='PORT', type='int',
            default=5432,
            help='Specifies the TCP port or the local Unix-domain socket ' +
                 'file extension on which the server is listening for ' +
                 'connections. Default: %default')
    parser.add_option('-U', '--user', dest='user', metavar='USER',
            default=getpass.getuser(),
            help='Connect to the database as the user USER instead of the ' +
                 'default: %default')
    parser.add_option('-D', '--dovecot', dest='dovecot', metavar='USER',
            default='dovecot',
            help='Database user name of the Dovecot database user. Default: ' +
                 '%default')
    parser.add_option('-M', '--postfix', dest='postfix', metavar='USER',
            default='postfix',
            help='Database user name of the Postfix (MTA)  database user. ' +
                 'Default: %default')
    return parser


def set_permissions(dbh, dc_vers, dovecot, postfix):
    dc_rw = ('userquota_11', 'userquota')[dc_vers == 12]
    dbc = dbh.cursor()
    dbc.execute('GRANT SELECT ON domain_data, domain_name, mailboxformat, '
                'maillocation, quotalimit, service_set, users TO %s' % dovecot)
    dbc.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON %s TO %s' %
                (dc_rw, dovecot))
    dbc.execute('GRANT SELECT ON alias, catchall, domain_data, domain_name, '
                'maillocation, postfix_gid, relocated, transport, users TO %s'
                % postfix)
    dbc.close()


def set_permissions84(dbh, dc_vers, dovecot, postfix):
    dc_rw_tbls = ('userquota_11', 'userquota')[dc_vers == 12]
    dc_ro_tbls = 'mailboxformat, maillocation, service_set, quotalimit'
    pf_ro_tbls = 'alias, catchall, postfix_gid, relocated, transport'
    db = dict(dovecot=dovecot, postfix=postfix)
    db['dovecot_tbls'] = {
        'domain_data': 'domaindir, gid, qid, ssid',
        'domain_name': 'domainname, gid',
        'users': 'gid, local_part, mid, passwd, qid, ssid, uid',
    }
    db['postfix_tbls'] = {
        'domain_data': 'domaindir, gid, tid',
        'domain_name': 'domainname, gid',
        'maillocation': 'directory, mid',
        'users': 'gid, local_part, mid, tid, uid',
    }
    dbc = dbh.cursor()
    dbc.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON %s TO %s' %
                (dc_rw_tbls, db['dovecot']))
    dbc.execute('GRANT SELECT ON %s TO %s' % (dc_ro_tbls, db['dovecot']))
    dbc.execute('GRANT SELECT ON %s TO %s' % (pf_ro_tbls, db['postfix']))
    for table, columns in db['dovecot_tbls'].iteritems():
        dbc.execute('GRANT SELECT (%s) ON %s TO %s' % (columns, table,
                                                       db['dovecot']))
    for table, columns in db['postfix_tbls'].iteritems():
        dbc.execute('GRANT SELECT (%s) ON %s TO %s' % (columns, table,
                                                       db['postfix']))
    dbc.close()


def set_versions(dbh, versions):
    dbc = dbh.cursor()
    if hasattr(dbh, 'server_version'):
        versions['pgsql'] = dbh.server_version
    else:
        try:
            dbc.execute("SELECT current_setting('server_version_num')")
            versions['pgsql'] = int(dbc.fetchone()[0])
        except DBErr:
            versions['pgsql'] = 80199
    dbc.execute("SELECT relname FROM pg_stat_user_tables WHERE relname LIKE "
                "'userquota%'")
    res = dbc.fetchall()
    dbc.close()
    tbls = [tbl[0] for tbl in res]
    if 'userquota' in tbls:
        versions['dovecot'] = 12
    elif 'userquota_11' in tbls:
        versions['dovecot'] = 11
    else:
        sys.stderr.write('error: no userquota table found\nis "' + dbh.dsn +
                         '" correct? is the database up to date?\n')
        dbh.close()
        raise SystemExit(1)


if __name__ == '__main__':
    optparser = get_optparser()
    opts, args = optparser.parse_args()
    check_opts(opts, optparser.error)
    dbh = get_dbh(opts.name, opts.user, opts.dbpass, opts.host, opts.port)
    versions = {}
    set_versions(dbh, versions)
    if versions['pgsql'] < 80400:
        set_permissions(dbh, versions['dovecot'], opts.dovecot, opts.postfix)
    else:
        set_permissions84(dbh, versions['dovecot'], opts.dovecot, opts.postfix)
    dbh.commit()
    dbh.close()
