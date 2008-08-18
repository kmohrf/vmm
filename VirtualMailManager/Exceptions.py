#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Exception classes for Virtual Mail Manager"""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

class VMMException(Exception):
    """Exception class for VirtualMailManager exceptions"""
    def __init__(self, msg):
        Exception.__init__(self, msg)

class VMMConfigException(Exception):
    """Exception class for Configurtion exceptions"""
    def __init__(self, msg):
        Exception.__init__(self, msg)

class VMMPermException(Exception):
    """Exception class for permissions exceptions"""
    pass

class VMMNotRootException(Exception):
    """Exception class for non-root exceptions"""
    def __init__(self, msg):
        Exception.__init__(self, msg)

class VMMDomainException(VMMException):
    """Exception class for Domain exceptions"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMDomainAliasException(VMMException):
    """Exception class for DomainAlias exceptions"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMAccountException(VMMException):
    """Exception class for Account exceptions"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMAliasException(VMMException):
    """Exception class for Alias exceptions"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMMailLocationException(VMMException):
    """Exception class for MailLocation exceptions"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

class VMMTransportException(VMMException):
    """Exception class for Transport exceptions"""
    def __init__(self, msg):
        VMMException.__init__(self, msg)

