#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

import os
from distutils.core import setup
from distutils.dist import DistributionMetadata

VERSION = '0.5.2'

descr = 'Tool to manage mail domains/accounts/aliases for Dovecot and Postfix'
long_description = """
vmm, a virtual mail manager, is a command line tool for
administrators/postmasters to manage (alias-)domains, accounts,
aliases and relocated users.
It is designed for Dovecot and Postfix with a PostgreSQL backend.
"""
packages = [
    'VirtualMailManager',
    'VirtualMailManager.constants',
    'VirtualMailManager.ext',
    'VirtualMailManager.pycompat',
]
classifiers = ['Development Status :: 5 - Production/Stable',
               'Environment :: Console',
               'Intended Audience :: System Administrators',
               'License :: OSI Approved :: BSD License',
               'Natural Language :: Dutch',
               'Natural Language :: English',
               'Natural Language :: French',
               'Natural Language :: German',
               'Operating System :: POSIX',
               'Operating System :: POSIX :: BSD',
               'Operating System :: POSIX :: Linux',
               'Operating System :: POSIX :: Other',
               'Programming Language :: Python',
               'Topic :: Communications :: Email',
               'Topic :: System :: Systems Administration',
               'Topic :: Utilities']

# sucessfuly tested on:
platforms = ['freebsd7', 'linux2', 'openbsd4']

# remove existing MANIFEST
if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

setup_args = {'name': 'VirtualMailManager',
              'version': VERSION,
              'description': descr,
              'long_description': long_description,
              'packages': packages,
              'author': 'Pascal Volk',
              'author_email': 'neverseen@users.sourceforge.net',
              'license': 'BSD License',
              'url': 'http://vmm.localdomain.org/',
              'download_url':'http://sf.net/projects/vmm/files/',
              'platforms': platforms,
              'classifiers': classifiers}

if 'requires' in DistributionMetadata._METHOD_BASENAMES:
    setup_args['requires'] = ['pyPgSQL']

setup(**setup_args)
