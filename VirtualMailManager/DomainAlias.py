#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Virtual Mail Manager's DomainAlias class to manage alias domains."""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

from Exceptions import VMMDomainAliasException as VDAE
import constants.ERROR as ERR

class DomainAlias:
    """Class to manage e-mail alias domains."""
    def __init__(self, dbh, domainname, targetDomain):
        self._dbh = dbh

    def _exists(self):
        pass

    def save(self):
        pass

    def info(self):
        pass
    
    def delete(self):
        pass
