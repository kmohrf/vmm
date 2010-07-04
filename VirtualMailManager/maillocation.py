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
           'ID_MAILDIR', 'ID_MBOX', 'ID_MDBOX', 'ID_SDBOX')

ID_MAILDIR = 0x1
ID_MBOX = 0x2
ID_MDBOX = 0x3
ID_SDBOX = 0x4

_storage = {
    ID_MAILDIR: dict(dovecot_version=0x10000f00, postfix=True,
                     prefix='maildir:', directory='Maildir', mid=ID_MAILDIR),
    ID_MBOX: dict(dovecot_version=0x10000f00, postfix=True, prefix='mbox:',
                  directory='mail', mid=ID_MBOX),
    ID_MDBOX: dict(dovecot_version=0x20000a01, postfix=False,
                   prefix='mdbox:', directory='mdbox', mid=ID_MDBOX),
    ID_SDBOX: dict(dovecot_version=0x10000f00, postfix=False, prefix='dbox:',
                   directory='dbox', mid=ID_SDBOX),
}

_format_id = {
    'maildir': ID_MAILDIR,
    'mbox': ID_MBOX,
    'mdbox': ID_MDBOX,
    'dbox': ID_SDBOX,
}


class MailLocation(object):
    """A small class for mail_location relevant information."""
    __slots__ = ('_info')

    def __init__(self, mid=None, format=None):
        """Creates a new MailLocation instance.

        Either a mid or the format must be specified.

        Keyword arguments:
        mid -- the id of a mail_location (int)
          one of the maillocation constants: `ID_MAILDIR`, `ID_MBOX`,
          `ID_MDBOX` and `ID_SDBOX`
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
