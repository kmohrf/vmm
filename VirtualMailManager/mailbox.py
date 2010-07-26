# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.mailbox
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    VirtualMailManager's mailbox classes for the Maildir, single dbox
    (sdbox) and multi dbox (mdbox) mailbox formats.
"""

import os
import re
from binascii import a2b_base64, b2a_base64
from subprocess import Popen, PIPE

from VirtualMailManager.Account import Account
from VirtualMailManager.common import is_dir
from VirtualMailManager.errors import VMMError
from VirtualMailManager.constants import VMM_ERROR


__all__ = ('new', 'Maildir', 'SingleDbox', 'MultiDbox',
           'utf8_to_mutf7', 'mutf7_to_utf8')

cfg_dget = lambda option: None


def _mbase64_encode(inp, dest):
    if inp:
        mb64 = b2a_base64(''.join(inp).encode('utf-16be'))
        dest.append('&%s-' % mb64.rstrip('\n=').replace('/', ','))
        del inp[:]


def _mbase64_to_unicode(mb64):
    return unicode(a2b_base64(mb64.replace(',', '/') + '==='), 'utf-16be')


def utf8_to_mutf7(src):
    """
    Converts the international mailbox name `src` into a modified
    version version of the UTF-7 encoding.
    """
    ret = []
    tmp = []
    for c in src:
        ordc = ord(c)
        if 0x20 <= ordc <= 0x25 or 0x27 <= ordc <= 0x7E:
            _mbase64_encode(tmp, ret)
            ret.append(c)
        elif ordc == 0x26:
            _mbase64_encode(tmp, ret)
            ret.append('&-')
        else:
            tmp.append(c)
    _mbase64_encode(tmp, ret)
    return ''.join(ret)


def mutf7_to_utf8(src):
    """
    Converts the mailbox name `src` from modified UTF-7 encoding to UTF-8.
    """
    ret = []
    tmp = []
    for c in src:
        if c == '&' and not tmp:
            tmp.append(c)
        elif c == '-' and tmp:
            if len(tmp) is 1:
                ret.append('&')
            else:
                ret.append(_mbase64_to_unicode(''.join(tmp[1:])))
            tmp = []
        elif tmp:
            tmp.append(c)
        else:
            ret.append(c)
    if tmp:
        ret.append(_mbase64_to_unicode(''.join(tmp[1:])))
    return ''.join(ret)


class Mailbox(object):
    """Base class of all mailbox classes."""
    __slots__ = ('_boxes', '_root', '_sep', '_user')
    FILE_MODE = 0600
    _ctrl_chr_re = re.compile('[\x00-\x1F\x7F-\x9F]')
    _box_name_re = re.compile('^[\x20-\x25\x27-\x7E]+$')

    def __init__(self, account):
        """
        Creates a new mailbox instance.
        Use one of the `Maildir`, `SingleDbox` or `MultiDbox` classes.
        """
        assert isinstance(account, Account)
        is_dir(account.home)
        self._user = account
        self._boxes = []
        self._root = self._user.mail_location.directory
        self._sep = '/'
        os.chdir(self._user.home)

    def _add_boxes(self, mailboxes, subscribe):
        raise NotImplementedError

    def _validate_box_name(self, name, good, bad):
        """
        Validates the mailboxes name `name`.  When the name is valid, it
        will be added to the `good` set.  Invalid mailbox names will be
        appended to the `bad` list.
        """
        name = name.strip()
        if not name:
            return
        if self.__class__._ctrl_chr_re.search(name):  # no control chars
            bad.append(name)
            return
        if name[0] in (self._sep, '~'):
            bad.append(name)
            return
        if self._sep == '/':
            if '//' in name or '/./' in name or '/../' in name or \
               name.startswith('../'):
                bad.append(name)
                return
        if '/' in name or '..' in name:
            bad.append(name)
            return
        if not self.__class__._box_name_re.match(name):
            tmp = utf8_to_mutf7(name)
            if name == mutf7_to_utf8(tmp):
                if self._user.mail_location.mbformat == 'maildir':
                    good.add(tmp)
                else:
                    good.add(name)
                return
            else:
                bad.append(name)
                return
        good.add(name)

    def add_boxes(self, mailboxes, subscribe):
        """
        Create all mailboxes from the `mailboxes` list in the user's
        mail directory.  When `subscribe` is ``True`` all created mailboxes
        will be listed in the subscriptions file.
        Returns a list of invalid mailbox names, if any.
        """
        assert isinstance(mailboxes, list) and isinstance(subscribe, bool)
        good = set()
        bad = []
        for box in mailboxes:
            self._validate_box_name(box, good, bad)
        self._add_boxes(good, subscribe)
        return bad

    def create(self):
        """Create the INBOX in the user's mail directory."""
        raise NotImplementedError


class Maildir(Mailbox):
    """Class for Maildir++ mailboxes."""

    __slots__ = ('_subdirs')

    def __init__(self, account):
        """
        Create a new Maildir++ instance.
        Call the instance's create() method, in order to create the INBOX.
        For additional mailboxes use the add_boxes() method.
        """
        super(self.__class__, self).__init__(account)
        self._sep = '.'
        self._subdirs = ('cur', 'new', 'tmp')

    def _create_maildirfolder_file(self, path):
        """Mark the Maildir++ folder as Maildir folder."""
        maildirfolder_file = os.path.join(self._sep + path, 'maildirfolder')
        os.close(os.open(maildirfolder_file, os.O_CREAT | os.O_WRONLY,
                         self.__class__.FILE_MODE))
        os.chown(maildirfolder_file, self._user.uid, self._user.gid)

    def _make_maildir(self, path):
        """
        Create Maildir++ folders with the cur, new and tmp subdirectories.
        """
        mode = cfg_dget('account.directory_mode')
        uid = self._user.uid
        gid = self._user.gid
        os.mkdir(path, mode)
        os.chown(path, uid, gid)
        for subdir in self._subdirs:
            dir_ = os.path.join(path, subdir)
            os.mkdir(dir_, mode)
            os.chown(dir_, uid, gid)

    def _subscribe_boxes(self):
        """Writes all created mailboxes to the subscriptions file."""
        if not self._boxes:
            return
        subscriptions = open('subscriptions', 'w')
        subscriptions.write('\n'.join(self._boxes))
        subscriptions.write('\n')
        subscriptions.flush()
        subscriptions.close()
        os.chown('subscriptions', self._user.uid, self._user.gid)
        os.chmod('subscriptions', self.__class__.FILE_MODE)
        del self._boxes[:]

    def _add_boxes(self, mailboxes, subscribe):
        for mailbox in mailboxes:
            self._make_maildir(self._sep + mailbox)
            self._create_maildirfolder_file(mailbox)
            self._boxes.append(mailbox)
        if subscribe:
            self._subscribe_boxes()

    def create(self):
        """Creates a Maildir++ INBOX."""
        self._make_maildir(self._root)
        os.chdir(self._root)


class SingleDbox(Mailbox):
    """
    Class for (single) dbox mailboxes.
    See http://wiki.dovecot.org/MailboxFormat/dbox for details.
    """

    __slots__ = ()

    def __init__(self, account):
        """
        Create a new dbox instance.
        Call the instance's create() method, in order to create the INBOX.
        For additional mailboxes use the add_boxes() method.
        """
        assert cfg_dget('misc.dovecot_version') >= \
                account.mail_location.dovecot_version
        super(SingleDbox, self).__init__(account)

    def _doveadm_create(self, mailboxes, subscribe):
        """Wrap around Dovecot's doveadm"""
        cmd_args = [cfg_dget('bin.dovecotpw'), 'mailbox', 'create', '-u',
                    str(self._user.address)]
        if subscribe:
            cmd_args.append('-s')
        cmd_args.extend(mailboxes)
        print '\n -> %r\n' % cmd_args
        process = Popen(cmd_args, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        if process.returncode:
            raise VMMError(stderr.strip(), VMM_ERROR)

    def create(self):
        """Create a dbox INBOX"""
        os.mkdir(self._root, cfg_dget('account.directory_mode'))
        os.chown(self._root, self._user.uid, self._user.gid)
        self._doveadm_create(('INBOX',), False)
        os.chdir(self._root)

    def _add_boxes(self, mailboxes, subscribe):
        self._doveadm_create(mailboxes, subscribe)


class MultiDbox(SingleDbox):
    """
    Class for multi dbox mailboxes.
    See http://wiki.dovecot.org/MailboxFormat/dbox#Multi-dbox for details.
    """

    __slots__ = ()


def __get_mailbox_class(mbfmt):
    if mbfmt == 'maildir':
        return Maildir
    elif mbfmt == 'mdbox':
        return MultiDbox
    elif mbfmt == 'sdbox':
        return SingleDbox
    raise ValueError('unsupported mailbox format: %r' % mbfmt)


def new(account):
    """Create a new Mailbox instance for the given Account."""
    return __get_mailbox_class(account.mail_location.mbformat)(account)

del cfg_dget
