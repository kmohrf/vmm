#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# opyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Exception classes for Virtual Mail Manager"""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

class VMMException(Exception):
    """Ausnahmeklasse für die Klasse VirtualMailManager"""
    def __init__(self, msg):
        Exception.__init__(self, msg)

class VMMConfigException(Exception):
    """Ausnahmeklasse für Konfigurationssausnamhem"""
    def __init__(self, msg):
        Exception.__init__(self, msg)

class VMMPermException(Exception):
    """Ausnahmeklasse für Berechtigungsausnamhem"""
    pass

class VMMNotRootException(Exception):
    """Ausnahmeklasse für unberechtige Zugriffe"""
    def __init__(self, msg):
        Exception.__init__(self, msg)

class VMMDomainException(VMMException):
    """Ausnahmeklasse für Domainausnamhem"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMAccountException(VMMException):
    """Ausnahmeklasse für Accountausnamhem"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMAliasException(VMMException):
    """Ausnahmeklasse für Aliasausnamhem"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)
