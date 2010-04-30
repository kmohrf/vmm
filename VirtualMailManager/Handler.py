# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""
   VirtualMailManager.Handler

   A wrapper class. It wraps round all other classes and does some
   dependencies checks.

   Additionally it communicates with the PostgreSQL database, creates
   or deletes directories of domains or users.
"""

import os
import re

from shutil import rmtree
from subprocess import Popen, PIPE

from pyPgSQL import PgSQL  # python-pgsql - http://pypgsql.sourceforge.net

import VirtualMailManager.constants.ERROR as ERR
from VirtualMailManager.Account import Account
from VirtualMailManager.Alias import Alias
from VirtualMailManager.AliasDomain import AliasDomain
from VirtualMailManager.common import exec_ok
from VirtualMailManager.Config import Config as Cfg
from VirtualMailManager.Domain import Domain, ace2idna, get_gid
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.errors import VMMError, AliasError, DomainError, \
     RelocatedError
from VirtualMailManager.Relocated import Relocated
from VirtualMailManager.Transport import Transport


RE_DOMAIN_SEARCH = """^[a-z0-9-\.]+$"""
RE_MBOX_NAMES = """^[\x20-\x25\x27-\x7E]*$"""
TYPE_ACCOUNT = 0x1
TYPE_ALIAS = 0x2
TYPE_RELOCATED = 0x4
_ = lambda msg: msg


class Handler(object):
    """Wrapper class to simplify the access on all the stuff from
    VirtualMailManager"""
    __slots__ = ('_Cfg', '_cfgFileName', '_dbh', '__warnings')

    def __init__(self, skip_some_checks=False):
        """Creates a new Handler instance.

        ``skip_some_checks`` : bool
            When a derived class knows how to handle all checks this
            argument may be ``True``. By default it is ``False`` and
            all checks will be performed.

        Throws a NotRootError if your uid is greater 0.
        """
        self._cfgFileName = ''
        self.__warnings = []
        self._Cfg = None
        self._dbh = None

        if os.geteuid():
            raise NotRootError(_(u"You are not root.\n\tGood bye!\n"),
                ERR.CONF_NOPERM)
        if self.__chkCfgFile():
            self._Cfg = Cfg(self._cfgFileName)
            self._Cfg.load()
        if not skip_some_checks:
            self._Cfg.check()
            self._chkenv()

    def __findCfgFile(self):
        for path in ['/root', '/usr/local/etc', '/etc']:
            tmp = os.path.join(path, 'vmm.cfg')
            if os.path.isfile(tmp):
                self._cfgFileName = tmp
                break
        if not len(self._cfgFileName):
            raise VMMError(
                _(u"No “vmm.cfg” found in: /root:/usr/local/etc:/etc"),
                ERR.CONF_NOFILE)

    def __chkCfgFile(self):
        """Checks the configuration file, returns bool"""
        self.__findCfgFile()
        fstat = os.stat(self._cfgFileName)
        fmode = int(oct(fstat.st_mode & 0777))
        if fmode % 100 and fstat.st_uid != fstat.st_gid or \
            fmode % 10 and fstat.st_uid == fstat.st_gid:
                raise PermissionError(_(
                    u'fix permissions (%(perms)s) for “%(file)s”\n\
`chmod 0600 %(file)s` would be great.') % {'file':
                    self._cfgFileName, 'perms': fmode}, ERR.CONF_WRONGPERM)
        else:
            return True

    def _chkenv(self):
        """"""
        basedir = self._Cfg.dget('misc.base_directory')
        if not os.path.exists(basedir):
            old_umask = os.umask(0006)
            os.makedirs(basedir, 0771)
            os.chown(basedir, 0, 0)
            os.umask(old_umask)
        elif not os.path.isdir(basedir):
            raise VMMError(_(u'“%s” is not a directory.\n\
(vmm.cfg: section "misc", option "base_directory")') %
                                 basedir, ERR.NO_SUCH_DIRECTORY)
        for opt, val in self._Cfg.items('bin'):
            try:
                exec_ok(val)
            except VMMError, e:
                if e.code is ERR.NO_SUCH_BINARY:
                    raise VMMError(_(u'“%(binary)s” doesn\'t exist.\n\
(vmm.cfg: section "bin", option "%(option)s")') %
                                       {'binary': val, 'option': opt},
                                       ERR.NO_SUCH_BINARY)
                elif e.code is ERR.NOT_EXECUTABLE:
                    raise VMMError(_(u'“%(binary)s” is not executable.\
\n(vmm.cfg: section "bin", option "%(option)s")') %
                                       {'binary': val, 'option': opt},
                                       ERR.NOT_EXECUTABLE)
                else:
                    raise

    def __dbConnect(self):
        """Creates a pyPgSQL.PgSQL.connection instance."""
        if self._dbh is None or (isinstance(self._dbh, PgSQL.Connection) and
                                  not self._dbh._isOpen):
            try:
                self._dbh = PgSQL.connect(
                        database=self._Cfg.dget('database.name'),
                        user=self._Cfg.pget('database.user'),
                        host=self._Cfg.dget('database.host'),
                        password=self._Cfg.pget('database.pass'),
                        client_encoding='utf8', unicode_results=True)
                dbc = self._dbh.cursor()
                dbc.execute("SET NAMES 'UTF8'")
                dbc.close()
            except PgSQL.libpq.DatabaseError, e:
                raise VMMError(str(e), ERR.DATABASE_ERROR)

    def _chk_other_address_types(self, address, exclude):
        """Checks if the EmailAddress *address* is known as `TYPE_ACCOUNT`,
        `TYPE_ALIAS` or `TYPE_RELOCATED`, but not as the `TYPE_*` specified
        by *exclude*.  If the *address* is known as one of the `TYPE_*`s
        the according `TYPE_*` constant will be returned.  Otherwise 0 will
        be returned."""
        assert exclude in (TYPE_ACCOUNT, TYPE_ALIAS, TYPE_RELOCATED) and \
                isinstance(address, EmailAddress)
        if exclude is not TYPE_ACCOUNT:
            account = Account(self._dbh, address)
            if account.uid > 0:
                return TYPE_ACCOUNT
        if exclude is not TYPE_ALIAS:
            alias = Alias(self._dbh, address)
            if alias:
                return TYPE_ALIAS
        if exclude is not TYPE_RELOCATED:
            relocated = Relocated(self._dbh, address)
            if relocated:
                return TYPE_RELOCATED
        return 0

    def __getAccount(self, address):
        address = EmailAddress(address)
        self.__dbConnect()
        return Account(self._dbh, address)

    def __getAlias(self, address):
        address = EmailAddress(address)
        self.__dbConnect()
        return Alias(self._dbh, address)

    def __getRelocated(self, address):
        address = EmailAddress(address)
        self.__dbConnect()
        return Relocated(self._dbh, address)

    def __getDomain(self, domainname):
        self.__dbConnect()
        return Domain(self._dbh, domainname)

    def __getDiskUsage(self, directory):
        """Estimate file space usage for the given directory.

        Keyword arguments:
        directory -- the directory to summarize recursively disk usage for
        """
        if self.__isdir(directory):
            return Popen([self._Cfg.dget('bin.du'), "-hs", directory],
                stdout=PIPE).communicate()[0].split('\t')[0]
        else:
            return 0

    def __isdir(self, directory):
        isdir = os.path.isdir(directory)
        if not isdir:
            self.__warnings.append(_('No such directory: %s') % directory)
        return isdir

    def __makedir(self, directory, mode=None, uid=None, gid=None):
        if mode is None:
            mode = self._Cfg.dget('account.directory_mode')
        if uid is None:
            uid = 0
        if gid is None:
            gid = 0
        os.makedirs(directory, mode)
        os.chown(directory, uid, gid)

    def __domDirMake(self, domdir, gid):
        #TODO: clenaup!
        os.umask(0006)
        oldpwd = os.getcwd()
        basedir = self._Cfg.dget('misc.base_directory')
        domdirdirs = domdir.replace(basedir + '/', '').split('/')

        os.chdir(basedir)
        if not os.path.isdir(domdirdirs[0]):
            self.__makedir(domdirdirs[0], 489, 0, 0)
        os.chdir(domdirdirs[0])
        os.umask(0007)
        self.__makedir(domdirdirs[1], self._Cfg.dget('domain.directory_mode'),
                       0, gid)
        os.chdir(oldpwd)

    def __subscribe(self, folderlist, uid, gid):
        """Creates a subscriptions file with the mailboxes from `folderlist`"""
        fname = os.path.join(self._Cfg.dget('maildir.name'), 'subscriptions')
        sf = open(fname, 'w')
        sf.write('\n'.join(folderlist))
        sf.write('\n')
        sf.flush()
        sf.close()
        os.chown(fname, uid, gid)
        os.chmod(fname, 384)

    def __mailDirMake(self, domdir, uid, gid):
        """Creates maildirs and maildir subfolders.

        Keyword arguments:
        domdir -- the path to the domain directory
        uid -- user id from the account
        gid -- group id from the account
        """
        #  obsolete -> (mailbox / maillocation)
        return
        os.umask(0007)
        oldpwd = os.getcwd()
        os.chdir(domdir)

        maildir = self._Cfg.dget('maildir.name')
        folders = [maildir]
        append = folders.append
        for folder in self._Cfg.dget('maildir.folders').split(':'):
            folder = folder.strip()
            if len(folder) and not folder.count('..'):
                if re.match(RE_MBOX_NAMES, folder):
                    append('%s/.%s' % (maildir, folder))
                else:
                    self.__warnings.append(_('Skipped mailbox folder: %r') %
                                           folder)
            else:
                self.__warnings.append(_('Skipped mailbox folder: %r') %
                                       folder)

        subdirs = ['cur', 'new', 'tmp']
        mode = self._Cfg.dget('account.directory_mode')

        self.__makedir('%s' % uid, mode, uid, gid)
        os.chdir('%s' % uid)
        for folder in folders:
            self.__makedir(folder, mode, uid, gid)
            for subdir in subdirs:
                self.__makedir(os.path.join(folder, subdir), mode, uid, gid)
        self.__subscribe((f.replace(maildir + '/.', '') for f in folders[1:]),
                         uid, gid)
        os.chdir(oldpwd)

    def __userDirDelete(self, domdir, uid, gid):
        if uid > 0 and gid > 0:
            userdir = '%s' % uid
            if userdir.count('..') or domdir.count('..'):
                raise VMMError(_(u'Found ".." in home directory path.'),
                                   ERR.FOUND_DOTS_IN_PATH)
            if os.path.isdir(domdir):
                os.chdir(domdir)
                if os.path.isdir(userdir):
                    mdstat = os.stat(userdir)
                    if (mdstat.st_uid, mdstat.st_gid) != (uid, gid):
                        raise VMMError(_(
                          u'Detected owner/group mismatch in home directory.'),
                          ERR.MAILDIR_PERM_MISMATCH)
                    rmtree(userdir, ignore_errors=True)
                else:
                    raise VMMError(_(u"No such directory: %s") %
                        os.path.join(domdir, userdir), ERR.NO_SUCH_DIRECTORY)

    def __domDirDelete(self, domdir, gid):
        if gid > 0:
            if not self.__isdir(domdir):
                return
            basedir = self._Cfg.dget('misc.base_directory')
            domdirdirs = domdir.replace(basedir + '/', '').split('/')
            domdirparent = os.path.join(basedir, domdirdirs[0])
            if basedir.count('..') or domdir.count('..'):
                raise VMMError(_(u'Found ".." in domain directory path.'),
                        ERR.FOUND_DOTS_IN_PATH)
            if os.path.isdir(domdirparent):
                os.chdir(domdirparent)
                if os.lstat(domdirdirs[1]).st_gid != gid:
                    raise VMMError(_(
                        u'Detected group mismatch in domain directory.'),
                        ERR.DOMAINDIR_GROUP_MISMATCH)
                rmtree(domdirdirs[1], ignore_errors=True)

    def hasWarnings(self):
        """Checks if warnings are present, returns bool."""
        return bool(len(self.__warnings))

    def getWarnings(self):
        """Returns a list with all available warnings and resets all
        warnings.

        """
        ret_val = self.__warnings[:]
        del self.__warnings[:]
        return ret_val

    def cfg_dget(self, option):
        """Get the configured value of the *option* (section.option).
        When the option was not configured its default value will be
        returned."""
        return self._Cfg.dget(option)

    def cfg_pget(self, option):
        """Get the configured value of the *option* (section.option)."""
        return self._Cfg.pget(option)

    def cfg_install(self):
        """Installs the cfg_dget method as ``cfg_dget`` into the built-in
        namespace."""
        import __builtin__
        assert 'cfg_dget' not in __builtin__.__dict__
        __builtin__.__dict__['cfg_dget'] = self._Cfg.dget

    def domainAdd(self, domainname, transport=None):
        dom = self.__getDomain(domainname)
        if transport is None:
            dom.set_transport(Transport(self._dbh,
                              transport=self._Cfg.dget('misc.transport')))
        else:
            dom.set_transport(Transport(self._dbh, transport=transport))
        dom.set_directory(self._Cfg.dget('misc.base_directory'))
        dom.save()
        self.__domDirMake(dom.directory, dom.gid)

    def domainTransport(self, domainname, transport, force=None):
        if force is not None and force != 'force':
            raise DomainError(_(u"Invalid argument: “%s”") % force,
                ERR.INVALID_OPTION)
        dom = self.__getDomain(domainname)
        trsp = Transport(self._dbh, transport=transport)
        if force is None:
            dom.update_transport(trsp)
        else:
            dom.update_transport(trsp, force=True)

    def domainDelete(self, domainname, force=None):
        if not force is None and force not in ['deluser', 'delalias',
                                               'delall']:
                raise DomainError(_(u'Invalid argument: “%s”') %
                                         force, ERR.INVALID_OPTION)
        dom = self.__getDomain(domainname)
        gid = dom.gid
        domdir = dom.directory
        if self._Cfg.dget('domain.force_deletion') or force == 'delall':
            dom.delete(True, True)
        elif force == 'deluser':
            dom.delete(deluser=True)
        elif force == 'delalias':
            dom.delete(delalias=True)
        else:
            dom.delete()
        if self._Cfg.dget('domain.delete_directory'):
            self.__domDirDelete(domdir, gid)

    def domainInfo(self, domainname, details=None):
        if details not in [None, 'accounts', 'aliasdomains', 'aliases', 'full',
                           'relocated']:
            raise VMMError(_(u'Invalid argument: “%s”') % details,
                               ERR.INVALID_AGUMENT)
        dom = self.__getDomain(domainname)
        dominfo = dom.get_info()
        if dominfo['domainname'].startswith('xn--'):
            dominfo['domainname'] += ' (%s)' % ace2idna(dominfo['domainname'])
        if details is None:
            return dominfo
        elif details == 'accounts':
            return (dominfo, dom.get_accounts())
        elif details == 'aliasdomains':
            return (dominfo, dom.get_aliase_names())
        elif details == 'aliases':
            return (dominfo, dom.get_aliases())
        elif details == 'relocated':
            return(dominfo, dom.get_relocated())
        else:
            return (dominfo, dom.get_aliase_names(), dom.get_accounts(),
                    dom.get_aliases(), dom.get_relocated())

    def aliasDomainAdd(self, aliasname, domainname):
        """Adds an alias domain to the domain.

        Arguments:

        `aliasname` : basestring
          The name of the alias domain
        `domainname` : basestring
          The name of the target domain
        """
        dom = self.__getDomain(domainname)
        aliasDom = AliasDomain(self._dbh, aliasname)
        aliasDom.set_destination(dom)
        aliasDom.save()

    def aliasDomainInfo(self, aliasname):
        """Returns a dict (keys: "alias" and "domain") with the names of
        the alias domain and its primary domain."""
        self.__dbConnect()
        aliasDom = AliasDomain(self._dbh, aliasname)
        return aliasDom.info()

    def aliasDomainSwitch(self, aliasname, domainname):
        """Modifies the target domain of an existing alias domain.

        Arguments:

        `aliasname` : basestring
          The name of the alias domain
        `domainname` : basestring
          The name of the new target domain
        """
        dom = self.__getDomain(domainname)
        aliasDom = AliasDomain(self._dbh, aliasname)
        aliasDom.set_destination(dom)
        aliasDom.switch()

    def aliasDomainDelete(self, aliasname):
        """Deletes the given alias domain.

        Argument:

        `aliasname` : basestring
          The name of the alias domain
        """
        self.__dbConnect()
        aliasDom = AliasDomain(self._dbh, aliasname)
        aliasDom.delete()

    def domainList(self, pattern=None):
        from VirtualMailManager.Domain import search
        like = False
        if pattern and (pattern.startswith('%') or pattern.endswith('%')):
            like = True
            if not re.match(RE_DOMAIN_SEARCH, pattern.strip('%')):
                raise VMMError(
                        _(u"The pattern '%s' contains invalid characters.") %
                               pattern, ERR.DOMAIN_INVALID)
        self.__dbConnect()
        return search(self._dbh, pattern=pattern, like=like)

    def user_add(self, emailaddress, password):
        """Wrapper around Account.set_password() and Account.save()."""
        acc = self.__getAccount(emailaddress)
        acc.set_password(password)
        acc.save()
        #  depends on modules mailbox and maillocation
        #  self.__mailDirMake(acc.domain_directory, acc.uid, acc.gid)

    def aliasAdd(self, aliasaddress, *targetaddresses):
        """Creates a new `Alias` entry for the given *aliasaddress* with
        the given *targetaddresses*."""
        alias = self.__getAlias(aliasaddress)
        destinations = [EmailAddress(address) for address in targetaddresses]
        warnings = []
        destinations = alias.add_destinations(destinations, warnings)
        if warnings:
            self.__warnings.append(_('Ignored destination addresses:'))
            self.__warnings.extend(('  * %s' % w for w in warnings))
        for destination in destinations:
            gid = get_gid(self._dbh, destination.domainname)
            if gid and (not Handler.accountExists(self._dbh, destination) and
                        not Handler.aliasExists(self._dbh, destination)):
                self.__warnings.append(
                    _(u"The destination account/alias %r doesn't exist.") %
                                       str(destination))

    def user_delete(self, emailaddress, force=None):
        """Wrapper around Account.delete(...)"""
        if force not in (None, 'delalias'):
            raise VMMError(_(u"Invalid argument: '%s'") % force,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        uid = acc.uid
        gid = acc.gid
        dom_dir = acc.domain_directory
        acc_dir = acc.home
        acc.delete(bool(force))
        if self._Cfg.dget('account.delete_directory'):
            try:
                self.__userDirDelete(dom_dir, uid, gid)
            except VMMError, err:
                if err.code in (ERR.FOUND_DOTS_IN_PATH,
                        ERR.MAILDIR_PERM_MISMATCH, ERR.NO_SUCH_DIRECTORY):
                    warning = _(u"""\
The account has been successfully deleted from the database.
    But an error occurred while deleting the following directory:
    “%(directory)s”
    Reason: %(reason)s""") % \
                                {'directory': acc_dir, 'reason': err.msg}
                    self.__warnings.append(warning)
                else:
                    raise

    def aliasInfo(self, aliasaddress):
        """Returns an iterator object for all destinations (`EmailAddress`
        instances) for the `Alias` with the given *aliasaddress*."""
        alias = self.__getAlias(aliasaddress)
        try:
            return alias.get_destinations()
        except AliasError, err:
            if err.code == ERR.NO_SUCH_ALIAS:
                other = self._chk_other_address_types(alias.address,
                                                      TYPE_ALIAS)
                if other is TYPE_ACCOUNT:
                    raise VMMError(_(u"There is already an account with the \
address '%s'.") %
                                   alias.address, ERR.ACCOUNT_EXISTS)
                elif other is TYPE_RELOCATED:
                    raise VMMError(_(u"There is already a relocated user \
with the address '%s'.") %
                                   alias.address, ERR.RELOCATED_EXISTS)
                else:  # unknown address
                    raise
            else:  # something other went wrong
                raise

    def aliasDelete(self, aliasaddress, targetaddress=None):
        """Deletes the `Alias` *aliasaddress* with all its destinations from
        the database. If *targetaddress* is not ``None``, only this
        destination will be removed from the alias."""
        alias = self.__getAlias(aliasaddress)
        if targetaddress is None:
            alias.delete()
        else:
            alias.del_destination(EmailAddress(targetaddress))

    def user_info(self, emailaddress, details=None):
        """Wrapper around Account.get_info(...)"""
        if details not in (None, 'du', 'aliases', 'full'):
            raise VMMError(_(u"Invalid argument: '%s'") % details,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        info = acc.get_info()
        if self._Cfg.dget('account.disk_usage') or details in ('du', 'full'):
            path = os.path.join(acc.home, info['mail_location'].split('/')[-1])
            info['disk usage'] = self.__getDiskUsage(path)
            if details in (None, 'du'):
                return info
        if details in ('aliases', 'full'):
            return (info, acc.get_aliases())
        return info

    def user_by_uid(self, uid):
        """Search for an Account by its *uid*.
        Returns a dict (address, uid and gid) if a user could be found."""
        from VirtualMailManager.Account import get_account_by_uid
        self.__dbConnect()
        return get_account_by_uid(uid, self._dbh)

    def user_password(self, emailaddress, password):
        """Wrapper for Account.modify('password' ...)."""
        if not isinstance(password, basestring) or not password:
            raise VMMError(_(u"Could not accept password: '%s'") % password,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        acc.modify('password', password)

    def user_name(self, emailaddress, name):
        """Wrapper for Account.modify('name', ...)."""
        if not isinstance(name, basestring) or not name:
            raise VMMError(_(u"Could not accept name: '%s'") % name,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        acc.modify('name', name)

    def user_transport(self, emailaddress, transport):
        """Wrapper for Account.modify('transport', ...)."""
        if not isinstance(transport, basestring) or not transport:
            raise VMMError(_(u"Could not accept transport: '%s'") % transport,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        acc.modify('transport', transport)

    def user_disable(self, emailaddress, service=None):
        """Wrapper for Account.disable(service)"""
        if service not in (None, 'all', 'imap', 'pop3', 'smtp', 'sieve'):
            raise VMMError(_(u"Could not accept service: '%s'") % service,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        acc.disable(service)

    def user_enable(self, emailaddress, service=None):
        """Wrapper for Account.enable(service)"""
        if service not in (None, 'all', 'imap', 'pop3', 'smtp', 'sieve'):
            raise VMMError(_(u"could not accept service: '%s'") % service,
                           ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, ERR.NO_SUCH_ACCOUNT)
        acc.enable(service)

    def relocatedAdd(self, emailaddress, targetaddress):
        """Creates a new `Relocated` entry in the database. If there is
        already a relocated user with the given *emailaddress*, only the
        *targetaddress* for the relocated user will be updated."""
        relocated = self.__getRelocated(emailaddress)
        relocated.set_destination(EmailAddress(targetaddress))

    def relocatedInfo(self, emailaddress):
        """Returns the target address of the relocated user with the given
        *emailaddress*."""
        relocated = self.__getRelocated(emailaddress)
        try:
            return relocated.get_info()
        except RelocatedError, err:
            if err.code == ERR.NO_SUCH_RELOCATED:
                other = self._chk_other_address_types(relocated.address,
                                                      TYPE_RELOCATED)
                if other is TYPE_ACCOUNT:
                    raise VMMError(_(u"There is already an account with the \
address '%s'.") %
                                   relocated.address, ERR.ACCOUNT_EXISTS)
                elif other is TYPE_ALIAS:
                    raise VMMError(_(u"There is already an alias with the \
address '%s'.") %
                                   relocated.address, ERR.ALIAS_EXISTS)
                else:  # unknown address
                    raise
            else:  # something other went wrong
                raise

    def relocatedDelete(self, emailaddress):
        """Deletes the relocated user with the given *emailaddress* from
        the database."""
        relocated = self.__getRelocated(emailaddress)
        relocated.delete()

    def __del__(self):
        if isinstance(self._dbh, PgSQL.Connection) and self._dbh._isOpen:
            self._dbh.close()

del _
