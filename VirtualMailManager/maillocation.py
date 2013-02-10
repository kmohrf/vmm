# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2013, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.maillocation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Virtual Mail Manager's maillocation module to handle Dovecot's
    mail_location setting for accounts.

"""

from VirtualMailManager.constants import MAILLOCATION_INIT
from VirtualMailManager.errors import MailLocationError as MLErr


__all__ = ('MailLocation', 'known_format')

_ = lambda msg: msg
_format_info = {
    'maildir': dict(dovecot_version=0x10000f00, postfix=True),
    'mdbox': dict(dovecot_version=0x20000b05, postfix=False),
    'sdbox': dict(dovecot_version=0x20000c03, postfix=False),
}


class MailLocation(object):
    """Class to handle mail_location relevant information."""
    __slots__ = ('_directory', '_mbfmt', '_mid', '_dbh')
    _kwargs = ('mid', 'mbfmt', 'directory')

    def __init__(self, dbh, **kwargs):
        """Creates a new MailLocation instance.

        Either the mid keyword or the mbfmt and directory keywords must be
        specified.

        Arguments:

        `dbh` : psycopg2._psycopg.connection
          A database connection for the database access.

        Keyword arguments:

        `mid` : int
          the id of a mail_location
        `mbfmt` : str
          the mailbox format of the mail_location. One out of: ``maildir``,
          ``sdbox`` and ``mdbox``.
        `directory` : str
          name of the mailbox root directory.
        """
        self._dbh = dbh
        self._directory = None
        self._mbfmt = None
        self._mid = 0

        for key in kwargs.keys():
            if key not in self.__class__._kwargs:
                raise ValueError('unrecognized keyword: %r' % key)
        mid = kwargs.get('mid')
        if mid:
            assert isinstance(mid, int)
            self._load_by_mid(mid)
        else:
            args = kwargs.get('mbfmt'), kwargs.get('directory')
            assert all(isinstance(arg, str) for arg in args)
            if args[0].lower() not in _format_info:
                raise MLErr(_("Unsupported mailbox format: '%s'") % args[0],
                            MAILLOCATION_INIT)
            directory = args[1].strip()
            if not directory:
                raise MLErr(_("Empty directory name"), MAILLOCATION_INIT)
            if len(directory) > 20:
                raise MLErr(_("Directory name is too long: '%s'") % directory,
                            MAILLOCATION_INIT)
            self._load_by_names(args[0].lower(), directory)

    def __str__(self):
        return '%s:~/%s' % (self._mbfmt, self._directory)

    @property
    def directory(self):
        """The mail_location's directory name."""
        return self._directory

    @property
    def dovecot_version(self):
        """The required Dovecot version for this mailbox format."""
        return _format_info[self._mbfmt]['dovecot_version']

    @property
    def postfix(self):
        """`True` if Postfix supports this mailbox format, else `False`."""
        return _format_info[self._mbfmt]['postfix']

    @property
    def mbformat(self):
        """The mail_location's mailbox format."""
        return self._mbfmt

    @property
    def mail_location(self):
        """The mail_location, e.g. ``maildir:~/Maildir``"""
        return self.__str__()

    @property
    def mid(self):
        """The mail_location's unique ID."""
        return self._mid

    def _load_by_mid(self, mid):
        """Load mail_location relevant information by *mid*"""
        dbc = self._dbh.cursor()
        dbc.execute('SELECT format, directory FROM mailboxformat, '
                    'maillocation WHERE mid = %u AND '
                    'maillocation.fid = mailboxformat.fid' % mid)
        result = dbc.fetchone()
        dbc.close()
        if not result:
            raise ValueError('Unknown mail_location id specified: %r' % mid)
        self._mid = mid
        self._mbfmt, self._directory = result

    def _load_by_names(self, mbfmt, directory):
        """Try to load mail_location relevant information by *mbfmt* and
        *directory* name. If it fails goto _save()."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT mid FROM maillocation WHERE fid = (SELECT fid "
                    "FROM mailboxformat WHERE format = %s) AND directory = %s",
                    (mbfmt, directory))
        result = dbc.fetchone()
        dbc.close()
        if not result:
            self._save(mbfmt, directory)
        else:
            self._mid = result[0]
            self._mbfmt = mbfmt
            self._directory = directory

    def _save(self, mbfmt, directory):
        """Save a new mail_location in the database."""
        dbc = self._dbh.cursor()
        dbc.execute("SELECT nextval('maillocation_id')")
        mid = dbc.fetchone()[0]
        dbc.execute("INSERT INTO maillocation (fid, mid, directory) VALUES ("
                    "(SELECT fid FROM mailboxformat WHERE format = %s), %s, "
                    "%s)",  (mbfmt, mid, directory))
        self._dbh.commit()
        dbc.close()
        self._mid = mid
        self._mbfmt = mbfmt
        self._directory = directory


def known_format(mbfmt):
    """Checks if the mailbox format *mbfmt* is known, returns bool."""
    return mbfmt.lower() in _format_info

del _
