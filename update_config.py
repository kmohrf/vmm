#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2014, Pascal Volk
# See COPYING for distribution information.

import os
os.sys.path.remove(os.sys.path[0])
from time import time
from configparser import ConfigParser
from shutil import copy2

pre_060 = False

try:
    from vmm.constants.VERSION import VERSION
    pre_060 = True
except ImportError:
    try:
        from vmm.constants import VERSION
    except ImportError:
        os.sys.stderr.write('error: no vmm version information found\n')
        raise SystemExit(2)

# we have to remove the old CamelCase files
if pre_060:
    import vmm
    vmm_inst_dir = os.path.dirname(vmm.__file__)
    tmp_info = open('/tmp/vmm_inst_dir', 'w')
    tmp_info.write(vmm_inst_dir)
    tmp_info.close()

try:
    import psycopg2
except ImportError:
    has_psycopg2 = False
else:
    has_psycopg2 = True


def get_config_file():
    f = None
    for d in ('/root', '/usr/local/etc', '/etc'):
        tmp = os.path.join(d, 'vmm.cfg')
        if os.path.isfile(tmp):
            f = tmp
            break
    if f:
        return f
    else:
        os.sys.stderr.write('error: vmm.cfg not found\n')
        raise SystemExit(2)


def update(cp):
    if VERSION == '0.5.2':
        upd_052(cp)
    elif VERSION in ('0.6.0', '0.6.1'):
        os.sys.stdout.write('info: vmm.cfg: nothing to do for version %s\n' %
                            VERSION)
        return
    else:
        os.sys.stderr.write('error: the version %s is not supported by this '
                            'script\n' % VERSION)
        raise SystemExit(3)


def get_cfg_parser(cf):
    fh = open(cf, 'r')
    cp = ConfigParser()
    cp.readfp(fh)
    fh.close()
    return cp


def update_cfg_file(cp, cf):
    copy2(cf, cf + '.bak.' + str(time()))
    fh = open(cf, 'w')
    cp.write(fh)
    fh.close()


def add_sections(cp, sections):
    for section in sections:
        if not cp.has_section(section):
            cp.add_section(section)


def move_option(cp, src, dst):
    ds, do = dst.split('.')
    if not cp.has_option(ds, do):
        ss, so = src.split('.')
        cp.set(ds, do, cp.get(ss, so))
        cp.remove_option(ss, so)
        sect_opt.append((dst, 'R'))


def add_option(cp, dst, val):
    ds, do = dst.split('.')
    if not cp.has_option(ds, do):
        cp.set(ds, do, val)
        sect_opt.append((dst, 'N'))


def set_dovecot_version(cp):
    if len(os.sys.argv) > 1:
        dovecot_version = os.sys.argv[1].strip()
        if not dovecot_version:
            dovecot_version = '1.2.11'
    else:
        dovecot_version = '1.2.11'
    cp.set('misc', 'dovecot_version', dovecot_version)
    sect_opt.append(('misc.dovecot_version', 'M'))


def get_option(cp, src):
    ss, so = src.split('.')
    return cp.get(ss, so)


def upd_052(cp):
    global had_config
    global had_gid_mail

    had_config = cp.remove_section('config')
    had_gid_mail = cp.remove_option('misc', 'gid_mail')
    add_sections(cp, ('domain', 'account', 'mailbox'))
    if cp.has_section('domdir'):
        for src, dst in (('domdir.mode',   'domain.directory_mode'),
                         ('domdir.delete', 'domain.delete_directory'),
                         ('domdir.base',   'misc.base_directory')):
            move_option(cp, src, dst)
        cp.remove_section('domdir')
    if cp.has_section('services'):
        for service in cp.options('services'):
            move_option(cp, 'services.%s' % service, 'domain.%s' % service)
        cp.remove_section('services')
    for src, dst in (('maildir.mode',      'account.directory_mode'),
                     ('maildir.diskusage', 'account.disk_usage'),
                     ('maildir.delete',    'account.delete_directory'),
                     ('maildir.folders',   'mailbox.folders'),
                     ('maildir.name',      'mailbox.root'),
                     ('misc.forcedel',     'domain.force_deletion'),
                     ('misc.transport',    'domain.transport'),
                     ('misc.passwdscheme', 'misc.password_scheme'),
                     ('misc.dovecotvers',  'misc.dovecot_version')):
        move_option(cp, src, dst)
    cp.remove_section('maildir')
    if not has_psycopg2:
        add_option(cp, 'database.module', 'pyPgSQL')
    set_dovecot_version(cp)


# def main():
if __name__ == '__main__':
    sect_opt = []
    had_config = False
    had_gid_mail = False
    cf = get_config_file()
    cp = get_cfg_parser(cf)
    update(cp)
    if len(sect_opt):
        update_cfg_file(cp, cf)
        sect_opt.sort()
        print('Please have a look at your configuration: %s' % cf)
        print('This are your Modified/Renamed/New settings:')
        for s_o, st in sect_opt:
            print('%s   %s = %s' % (st, s_o, get_option(cp, s_o)))
        if had_config:
            print('\nRemoved section "config" with option "done" (obsolte)')
        if had_gid_mail:
            print('\nRemoved option "gid_mail" from section "misc"',
                  '(obsolte)\n')
        os.sys.exit(0)
    if had_config or had_gid_mail:
        update_cfg_file(cp, cf)
        if had_config:
            print('\nRemoved section "config" with option "done" (obsolte)')
        if had_gid_mail:
            print('\nRemoved option "gid_mail" from section "misc"',
                  '(obsolte)\n')
