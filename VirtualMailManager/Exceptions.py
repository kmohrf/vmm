# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.Exceptions

    VMM's Exception classes
"""


class VMMException(Exception):
    """Exception base class for VirtualMailManager exceptions"""

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
    """Exception class for configuration exceptions"""
    pass


class VMMPermException(VMMException):
    """Exception class for permissions exceptions"""
    pass


class VMMNotRootException(VMMException):
    """Exception class for non-root exceptions"""
    pass


class VMMDomainException(VMMException):
    """Exception class for Domain exceptions"""
    pass


class VMMAliasDomainException(VMMException):
    """Exception class for AliasDomain exceptions"""
    pass


class VMMAccountException(VMMException):
    """Exception class for Account exceptions"""
    pass


class VMMAliasException(VMMException):
    """Exception class for Alias exceptions"""
    pass


class VMMEmailAddressException(VMMException):
    """Exception class for EmailAddress exceptions"""
    pass


class VMMMailLocationException(VMMException):
    """Exception class for MailLocation exceptions"""
    pass


class VMMRelocatedException(VMMException):
    """Exception class for Relocated exceptions"""
    pass


class VMMTransportException(VMMException):
    """Exception class for Transport exceptions"""
    pass
