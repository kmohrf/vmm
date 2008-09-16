#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2008 VEB IT
# See COPYING for distribution information.
# $Id$

import sys
from ConfigParser import ConfigParser
from shutil import copy2

cf = '/usr/local/etc/vmm.cfg'
fh = file(cf, 'r')
cp = ConfigParser()
cp.readfp(fh)
fh.close()

if not cp.has_option('maildir', 'name') or not cp.has_option('maildir',
        'folders') or cp.has_option('maildir', 'folder'):
    copy2(cf, cf+'.bak_upd_0.4.x-0.5')
    fh = file(cf, 'w')
    if not cp.has_option('maildir', 'name'):
        if cp.has_option('maildir', 'folder'):
            cp.set('maildir', 'name', cp.get('maildir', 'folder'))
            cp.remove_option('maildir', 'folder')
        else:
            cp.set('maildir', 'name', 'Maildir')
    if not cp.has_option('maildir', 'folders'):
        cp.set('maildir', 'folders', 'Drafts:Sent:Templates:Trash')
    if cp.has_option('maildir', 'folder'):
        cp.remove_option('maildir', 'folder')
    cp.write(fh)
    fh.close()

if not cp.has_option('bin', 'postconf'):
    fh = file(cf, 'w')
    try:
        postconf = sys.argv[1].strip()
        if len(postconf):
            cp.set('bin', 'postconf', postconf)
        else: # possible?
            cp.set('bin', 'postconf', '/usr/sbin/postconf')
    except IndexError:
        cp.set('bin', 'postconf', '/usr/sbin/postconf')
    cp.write(fh)
    fh.close()
    print
    print "Please have a look at your %s" %cf
    print "and verify the value from option 'postconf' in section 'bin'."
    print

