# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Exception classes for Virtual Mail Manager"""

class VMMException(Exception):
    """Exception class for VirtualMailManager exceptions"""
    def __init__(self, msg, code):
        Exception.__init__(self, msg)
        self._code = int(code)
        ### for older python versions, like py 2.4.4 on OpenBSD 4.2
        if not hasattr(self, 'message'):
            self.message = msg

    def msg(self):
        """Returns the exception message."""
        return self.message

    def code(self):
        """Returns the numeric exception error code."""
        return self._code

class VMMConfigException(VMMException):
    """Exception class for Configurtion exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMPermException(VMMException):
    """Exception class for permissions exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMNotRootException(VMMException):
    """Exception class for non-root exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMDomainException(VMMException):
    """Exception class for Domain exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMAliasDomainException(VMMException):
    """Exception class for AliasDomain exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMAccountException(VMMException):
    """Exception class for Account exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMAliasException(VMMException):
    """Exception class for Alias exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMEmailAddressException(VMMException):
    """Exception class for EmailAddress exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMMailLocationException(VMMException):
    """Exception class for MailLocation exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMRelocatedException(VMMException):
    """Exception class for Relocated exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)

class VMMTransportException(VMMException):
    """Exception class for Transport exceptions"""
    def __init__(self, msg, code):
        VMMException.__init__(self, msg, code)
