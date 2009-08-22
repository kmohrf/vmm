#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2009, VEB IT
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
        os.sys.exit(2)

def update(cp):
    if VERSION == '0.4':
        upd_040(cp)
    elif VERSION == '0.5':
        upd_050(cp)
    elif VERSION == '0.5.1':
        upd_051(cp)
    elif VERSION == '0.5.2':
        os.sys.stdout.write('info: nothing to do for version %s\n' % VERSION)
        os.sys.exit(0)
    else:
        os.sys.stderr.write(
            'error: the version %s is not supported by this script\n' % VERSION)
        os.sys.exit(3)

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

def upd_040(cp):
    if not cp.has_option('maildir', 'name') or not cp.has_option('maildir',
        'folders') or cp.has_option('maildir', 'folder'):
        if not cp.has_option('maildir', 'name'):
            if cp.has_option('maildir', 'folder'):
                cp.set('maildir', 'name', cp.get('maildir', 'folder'))
                cp.remove_option('maildir', 'folder')
                sect_opt.append(('maildir', 'name'))
            else:
                cp.set('maildir', 'name', 'Maildir')
                sect_opt.append(('maildir', 'name'))
        if not cp.has_option('maildir', 'folders'):
            cp.set('maildir', 'folders', 'Drafts:Sent:Templates:Trash')
            sect_opt.append(('maildir', 'folders'))
        if cp.has_option('maildir', 'folder'):
            cp.remove_option('maildir', 'folder')
    upd_050(cp)

def upd_050(cp):
    if not cp.has_option('bin', 'postconf'):
        try:
            postconf = os.sys.argv[1].strip()
            if len(postconf):
                cp.set('bin', 'postconf', postconf)
                sect_opt.append(('bin', 'postconf'))
            else: # possible?
                cp.set('bin', 'postconf', '/usr/sbin/postconf')
                sect_opt.append(('bin', 'postconf'))
        except IndexError:
            cp.set('bin', 'postconf', '/usr/sbin/postconf')
            sect_opt.append(('bin', 'postconf'))
    upd_051(cp)

def upd_051(cp):
    if not cp.has_option('misc', 'dovecotvers') or cp.has_option('services',
            'managesieve'):
        if not cp.has_option('misc', 'dovecotvers'):
            cp.set('misc', 'dovecotvers', os.sys.argv[2].strip())
            sect_opt.append(('misc', 'dovecotvers'))
        if cp.has_option('services', 'managesieve'):
            cp.set('services','sieve',cp.getboolean('services', 'managesieve'))
            cp.remove_option('services', 'managesieve')
            sect_opt.append(('services', 'sieve'))

# def main():
if __name__ == '__main__':
    sect_opt = []
    cf = get_config_file()
    cp = get_cfg_parser(cf)
    update(cp)
    if len(sect_opt): 
        update_cfg_file(cp, cf)
        print 'Please have a look at your configuration: %s' %cf
        print 'and verify the value from:'
        for s_o in sect_opt:
            print '  [%s] %s' % s_o
        print


