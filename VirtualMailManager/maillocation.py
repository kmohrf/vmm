# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.maillocation

    Virtual Mail Manager's maillocation module to handle Dovecot's
    mail_location setting for accounts.

"""

from VirtualMailManager.pycompat import any


__all__ = ('MailLocation', 'known_format',
           'MAILDIR_ID', 'MBOX_ID', 'MDBOX_ID', 'SDBOX_ID')

MAILDIR_ID = 0x1
MBOX_ID = 0x2
MDBOX_ID = 0x3
SDBOX_ID = 0x4
MAILDIR_NAME = 'Maildir'
MBOX_NAME = 'mail'
MDBOX_NAME = 'mdbox'
SDBOX_NAME = 'dbox'

_storage = {
    MAILDIR_ID: dict(dovecot_version=0x10000f0, postfix=True,
                     prefix='maildir:', directory=MAILDIR_NAME,
                     mid=MAILDIR_ID),
    MBOX_ID: dict(dovecot_version=0x10000f0, postfix=True, prefix='mbox:',
                  directory=MBOX_NAME, mid=MBOX_ID),
    MDBOX_ID: dict(dovecot_version=0x20000a1, postfix=False, prefix='mdbox:',
                   directory=MDBOX_NAME, mid=MDBOX_ID),
    SDBOX_ID: dict(dovecot_version=0x10000f0, postfix=False, prefix='dbox:',
                   directory=SDBOX_NAME, mid=SDBOX_ID),
}

_format_id = {
    'maildir': MAILDIR_ID,
    'mbox': MBOX_ID,
    'mdbox': MDBOX_ID,
    'dbox': SDBOX_ID,
}


class MailLocation(object):
    """A small class for mail_location relevant information."""
    __slots__ = ('_info')

    def __init__(self, mid=None, format=None):
        """Creates a new MailLocation instance.

        Either a mid or the format must be specified.

        Keyword arguments:
        mid -- the id of a mail_location (int)
          one of the maillocation constants: `MAILDIR_ID`, `MBOX_ID`,
          `MDBOX_ID` and `SDBOX_ID`
        format -- the mailbox format of the mail_location. One out of:
        ``maildir``, ``mbox``, ``dbox`` and ``mdbox``.
        """
        assert any((mid, format))
        if mid:
            assert isinstance(mid, (int, long)) and mid in _storage
            self._info = _storage[mid]
        else:
            assert isinstance(format, basestring) and \
                    format.lower() in _format_id
            self._info = _storage[_format_id[format.lower()]]

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

    @property
    def mid(self):
        """The mail_location's unique ID."""
        return self._info['mid']


def known_format(format):
    """Checks if the mailbox *format* is known, returns bool."""
    return format.lower() in _format_id
