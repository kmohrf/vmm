#!/usr/bin/env python3
# Copyright 2007 - 2014, Pascal Volk
# See COPYING for distribution information.

from setuptools import find_packages, setup

VERSION = '0.6.2'

description = 'Tool to manage mail domains/accounts/aliases for Dovecot and Postfix'
long_description = """
vmm, a virtual mail manager, is a command line tool for
administrators/postmasters to manage (alias-)domains, accounts,
aliases and relocated users.
It is designed for Dovecot and Postfix with a PostgreSQL backend.
"""

setup(
    name='vmm',
    version=VERSION,
    description=description,
    long_description=long_description,
    packages=find_packages('vmm'),
    author='Pascal Volk',
    author_email='user+vmm@localhost.localdomain.org',
    license='BSD-3-Clause',
    url='http://vmm.localdomain.org/',
    download_url='http://sf.net/projects/vmm/files/',
    install_requires={
        'psycopg2 (>=2.0)',
    },
    classifiers={
        # https://pypi.org/pypi?:action=list_classifiers
        'Development Status :: 5 - Production/Stable',
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
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Email',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    }
)
