#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

import os
os.sys.path.remove(os.sys.path[0])
from time import time
from ConfigParser import ConfigParser
from shutil import copy2
from VirtualMailManager.constants.VERSION import VERSION


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
    elif VERSION == '0.6.0':
        os.sys.stdout.write('info: nothing to do for version %s\n' % VERSION)
        return
    else:
        os.sys.stderr.write(
            'error: the version %s is not supported by this script\n' % VERSION)
        raise SystemExit(3)

def get_cfg_parser(cf):
    fh = file(cf, 'r')
    cp = ConfigParser()
    cp.readfp(fh)
    fh.close()
    return cp

def update_cfg_file(cp, cf):
    copy2(cf, cf+'.bak.'+str(time()))
    fh = file(cf, 'w')
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

def get_option(cp, src):
    ss, so = src.split('.')
    return cp.get(ss, so)

def upd_052(cp):
    add_sections(cp, ('domain', 'account'))
    if cp.has_section('domdir'):
        for src, dst in (('domdir.mode',   'domain.directory_mode'),
                         ('domdir.delete', 'domain.delete_directory'),
                         ('domdir.base',   'misc.base_dir')):
            move_option(cp, src, dst)
        cp.remove_section('domdir')
    if cp.has_section('services'):
        for service in cp.options('services'):
            move_option(cp, 'services.%s'%service, 'account.%s'%service)
        cp.remove_section('services')
    for src, dst in (('maildir.mode',      'account.directory_mode'),
                     ('maildir.diskusage', 'account.disk_usage'),
                     ('maildir.delete',    'account.delete_directory'),
                     ('misc.forcedel',     'domain.force_del'),
                     ('misc.passwdscheme', 'misc.password_scheme'),
                     ('misc.dovecotvers',  'misc.dovecot_vers')):
        move_option(cp, src, dst)
    for dst, val in (('account.random_password', 'false'),
                     ('account.password_len',    '8'),
                     ('domain.auto_postmaster',  'true')):
        add_option(cp, dst, val)

# def main():
if __name__ == '__main__':
    sect_opt = []
    cf = get_config_file()
    cp = get_cfg_parser(cf)
    update(cp)
    if len(sect_opt):
        update_cfg_file(cp, cf)
        sect_opt.sort()
        print 'Please have a look at your configuration: %s' %cf
        print 'This are your Renamed/New settings:'
        for s_o, st in sect_opt:
            print '%s   %s = %s' % (st, s_o, get_option(cp, s_o))
        print

