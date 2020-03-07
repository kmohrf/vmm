#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2007 - 2014, Pascal Volk
# See COPYING for distribution information.

import os
from distutils.core import setup

VERSION = '0.6.2'

descr = 'Tool to manage mail domains/accounts/aliases for Dovecot and Postfix'
long_description = """
vmm, a virtual mail manager, is a command line tool for
administrators/postmasters to manage (alias-)domains, accounts,
aliases and relocated users.
It is designed for Dovecot and Postfix with a PostgreSQL backend.
"""
packages = [
    'vmm',
    'vmm.cli',
    'vmm.ext',
]
# http://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = ['Development Status :: 5 - Production/Stable',
               'Environment :: Console',
               'Intended Audience :: System Administrators',
               'License :: OSI Approved :: BSD License',
               'Natural Language :: Dutch',
               'Natural Language :: English',
               'Natural Language :: Finnish',
               'Natural Language :: French',
               'Natural Language :: German',
               'Natural Language :: Vietnamese',
               'Operating System :: POSIX',
               'Operating System :: POSIX :: BSD',
               'Operating System :: POSIX :: Linux',
               'Operating System :: POSIX :: Other',
               'Programming Language :: Python',
               'Programming Language :: Python :: 2',
               'Topic :: Communications :: Email',
               'Topic :: System :: Systems Administration',
               'Topic :: Utilities']

# sucessfuly tested on:
platforms = ['freebsd7', 'linux2', 'openbsd5']

# remove existing MANIFEST
if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

setup_args = {'name': 'vmm',
              'version': VERSION,
              'description': descr,
              'long_description': long_description,
              'packages': packages,
              'author': 'Pascal Volk',
              'author_email': 'user+vmm@localhost.localdomain.org',
              'license': 'BSD License',
              'requires': ['psycopg2 (>=2.0)'],
              'url': 'http://vmm.localdomain.org/',
              'download_url': 'http://sf.net/projects/vmm/files/',
              'platforms': platforms,
              'classifiers': classifiers}

setup(**setup_args)
