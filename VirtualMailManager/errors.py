# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.errors
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    VMM's Exception classes
"""


class VMMError(Exception):
    """Exception base class for VirtualMailManager exceptions"""

    def __init__(self, msg, code):
        Exception.__init__(self, msg)
        self.msg = msg
        self.code = int(code)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.msg, self.code)


class ConfigError(VMMError):
    """Exception class for configuration exceptions"""
    pass


class PermissionError(VMMError):
    """Exception class for permissions exceptions"""
    pass


class NotRootError(VMMError):
    """Exception class for non-root exceptions"""
    pass


class DomainError(VMMError):
    """Exception class for Domain exceptions"""
    pass


class AliasDomainError(VMMError):
    """Exception class for AliasDomain exceptions"""
    pass


class AccountError(VMMError):
    """Exception class for Account exceptions"""
    pass


class AliasError(VMMError):
    """Exception class for Alias exceptions"""
    pass


class EmailAddressError(VMMError):
    """Exception class for EmailAddress exceptions"""
    pass


class MailLocationError(VMMError):
    """Exception class for MailLocation exceptions"""
    pass


class RelocatedError(VMMError):
    """Exception class for Relocated exceptions"""
    pass


class TransportError(VMMError):
    """Exception class for Transport exceptions"""
    pass
