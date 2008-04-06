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
if not cf.has_option('misc', 'transport'):
    cff = file('/usr/local/etc/vmm.cfg', 'w')
    cf.set('misc', 'transport', 'dovecot:')
    cf.write(cff)
    cff.close()
