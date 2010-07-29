# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.constants
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    VirtualMailManager's constants:
        * version information
        * upper and lower limits MIN_* / MAX_*
        * exit codes
        * error codes
"""
# version information

__all__ = ['__author__', '__date__', '__version__']
AUTHOR = 'Pascal Volk <neverseen@users.sourceforge.net>'
RELDATE = '2009-09-09'
VERSION = '0.5.2'
__author__ = AUTHOR
__copyright__ = 'Copyright (c) 2007-2010 %s' % __author__
__date__ = RELDATE
__version__ = VERSION


# limits

MIN_GID = 70000
MIN_UID = 70000


# exit codes

EX_SUCCESS = 0
EX_MISSING_ARGS = 1
EX_UNKNOWN_COMMAND = 2
EX_USER_INTERRUPT = 3


# error codes

ACCOUNT_AND_ALIAS_PRESENT = 20
ACCOUNT_EXISTS = 21
ACCOUNT_MISSING_PASSWORD = 69
ACCOUNT_PRESENT = 22
ALIASDOMAIN_EXISTS = 23
ALIASDOMAIN_ISDOMAIN = 24
ALIASDOMAIN_NO_DOMDEST = 25
ALIAS_ADDR_DEST_IDENTICAL = 26
ALIAS_EXCEEDS_EXPANSION_LIMIT = 27
ALIAS_EXISTS = 28
ALIAS_MISSING_DEST = 29
ALIAS_PRESENT = 30
CONF_ERROR = 31
CONF_NOFILE = 32
CONF_NOPERM = 33
CONF_WRONGPERM = 34
DATABASE_ERROR = 35
DOMAINDIR_GROUP_MISMATCH = 36
DOMAIN_ALIAS_EXISTS = 37
DOMAIN_EXISTS = 38
DOMAIN_INVALID = 39
DOMAIN_NO_NAME = 40
DOMAIN_TOO_LONG = 41
FOUND_DOTS_IN_PATH = 42
INVALID_ADDRESS = 43
INVALID_ARGUMENT = 44
INVALID_MAIL_LOCATION = 70
INVALID_OPTION = 45
INVALID_SECTION = 46
LOCALPART_INVALID = 47
LOCALPART_TOO_LONG = 48
MAILDIR_PERM_MISMATCH = 49
MAILLOCATION_INIT = 50
NOT_EXECUTABLE = 51
NO_SUCH_ACCOUNT = 52
NO_SUCH_ALIAS = 53
NO_SUCH_ALIASDOMAIN = 54
NO_SUCH_BINARY = 55
NO_SUCH_DIRECTORY = 56
NO_SUCH_DOMAIN = 57
NO_SUCH_RELOCATED = 58
RELOCATED_ADDR_DEST_IDENTICAL = 59
RELOCATED_EXISTS = 60
RELOCATED_MISSING_DEST = 61
TRANSPORT_INIT = 62
UNKNOWN_MAILLOCATION_ID = 63
UNKNOWN_MAILLOCATION_NAME = 64
UNKNOWN_SERVICE = 65
UNKNOWN_TRANSPORT_ID = 66
VMM_ERROR = 67
VMM_TOO_MANY_FAILURES = 68
