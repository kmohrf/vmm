#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

import os
from distutils.core import setup

from VirtualMailManager.constants.VERSION import VERSION

long_description = """
Virtual Mail Manager is a command line tool for administrators/postmasters to
manage domains, accounts and aliases. It's designed for Dovecot and Postfix
with a PostgreSQL backend.
"""

# remove existing MANIFEST
if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')


setup(name='VirtualMailManager',
      version=VERSION,
      description='Tool to manage mail domains/accounts/aliases for Dovecot and Postfix',
      long_description=long_description,
      packages=['VirtualMailManager', 'VirtualMailManager.ext',
          'VirtualMailManager.constants'],
      author='Pascal Volk',
      author_email='p.volk@veb-it.de',
      license='BSD License',
      url='http://vmm.sf.net/',
      download_url='http://sf.net/project/showfiles.php?group_id=213727',
      platforms=['linux2', 'openbsd4'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Natural Language :: English',
          'Natural Language :: German',
          'Operating System :: POSIX',
          'Operating System :: POSIX :: BSD',
          'Operating System :: POSIX :: Linux',
          'Operating System :: POSIX :: Other',
          'Programming Language :: Python',
          'Topic :: Communications :: Email',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities'
      ],
      requires=['pyPgSQL']
      )
