# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.maillocation

    Virtual Mail Manager's maillocation module to handle Dovecot's
    mail_location setting for accounts.

"""

from VirtualMailManager.pycompat import any


__all__ = ('MailLocation',
           'MAILDIR_ID', 'MBOX_ID', 'MDBOX_ID', 'SDBOX_ID',
           'MAILDIR_NAME', 'MBOX_NAME', 'MDBOX_NAME', 'SDBOX_NAME')

MAILDIR_ID = 0x1
MBOX_ID = 0x2
MDBOX_ID = 0x3
SDBOX_ID = 0x4
MAILDIR_NAME = 'Maildir'
MBOX_NAME = 'mail'
MDBOX_NAME = 'mdbox'
SDBOX_NAME = 'dbox'

_storage = {
    MAILDIR_ID: dict(dovecot_version=10, postfix=True, prefix='maildir:',
                     directory=MAILDIR_NAME),
    MBOX_ID: dict(dovecot_version=10, postfix=True, prefix='mbox:',
                  directory=MBOX_NAME),
    MDBOX_ID: dict(dovecot_version=20, postfix=False, prefix='mdbox:',
                   directory=MDBOX_NAME),
    SDBOX_ID: dict(dovecot_version=12, postfix=False, prefix='dbox:',
                   directory=SDBOX_NAME),
}

_type_id = {
    'maildir': MAILDIR_ID,
    MBOX_NAME: MBOX_ID,
    MDBOX_NAME: MDBOX_ID,
    SDBOX_NAME: SDBOX_ID,
}


class MailLocation(object):
    """A small class for mail_location relevant information."""
    __slots__ = ('_info')

    def __init__(self, mid=None, type_=None):
        """Creates a new MailLocation instance.

        Either mid or type_ must be specified.

        Keyword arguments:
        mid -- the id of a mail_location (int)
          one of the maillocation constants: `MAILDIR_ID`, `MBOX_ID`,
          `MDBOX_ID` and `SDBOX_ID`
        type_ -- the type/mailbox format of the mail_location (str)
          one of the maillocation constants: `MAILDIR_NAME`, `MBOX_NAME`,
          `MDBOX_NAME` and `SDBOX_NAME`
        """
        assert any((mid, type_))
        if mid:
            assert isinstance(mid, (int, long)) and mid in _storage
            self._info = _storage[mid]
        else:
            assert isinstance(type_, basestring) and type_.lower() in _type_id
            self._info = _storage[_type_id[type_.lower()]]

    def __str__(self):
        return '%(prefix)s~/%(directory)s' % self._info

    @property
    def directory(self):
        """The mail_location's directory name."""
        return self._info['directory']

    @property
    def dovecot_version(self):
        """The required Dovecot version (concatenated major and minor
        parts) for this mailbox format."""
        return self._info['dovecot_version']

    @property
    def postfix(self):
        """`True` if Postfix supports this mailbox format, else `False`."""
        return self._info['postfix']

    @property
    def prefix(self):
        """The prefix of the mail_location."""
        return self._info['prefix']

    @property
    def mail_location(self):
        """The mail_location, e.g. ``maildir:~/Maildir``"""
        return self.__str__()
