#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2008 VEB IT
# See COPYING for distribution information.
# $Id$

from ConfigParser import ConfigParser

cff = file('/usr/local/etc/vmm.cfg', 'r')
cf = ConfigParser()
cf.readfp(cff)
cff.close()

if not cf.has_option('misc', 'transport') or not cf.has_section('services'):
    cff = file('/usr/local/etc/vmm.cfg', 'w')
    if not cf.has_option('misc', 'transport'):
        cf.set('misc', 'transport', 'dovecot:')
    if not cf.has_section('services'):
        cf.add_section('services')
        for service in ['smtp', 'pop3', 'imap', 'managesieve']:
            cf.set('services', service, 'true')
    cf.write(cff)
    cff.close()
