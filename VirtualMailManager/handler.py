# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.
"""
   VirtualMailManager.handler
   ~~~~~~~~~~~~~~~~~~~~~~~~~~

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

from VirtualMailManager.account import Account
from VirtualMailManager.alias import Alias
from VirtualMailManager.aliasdomain import AliasDomain
from VirtualMailManager.common import exec_ok, lisdir
from VirtualMailManager.config import Config as Cfg
from VirtualMailManager.constants import MIN_GID, MIN_UID, \
     ACCOUNT_EXISTS, ALIAS_EXISTS, CONF_NOFILE, CONF_NOPERM, CONF_WRONGPERM, \
     DATABASE_ERROR, DOMAINDIR_GROUP_MISMATCH, DOMAIN_INVALID, \
     FOUND_DOTS_IN_PATH, INVALID_ARGUMENT, MAILDIR_PERM_MISMATCH, \
     NOT_EXECUTABLE, NO_SUCH_ACCOUNT, NO_SUCH_ALIAS, NO_SUCH_BINARY, \
     NO_SUCH_DIRECTORY, NO_SUCH_RELOCATED, RELOCATED_EXISTS
from VirtualMailManager.domain import Domain, get_gid
from VirtualMailManager.emailaddress import EmailAddress
from VirtualMailManager.errors import \
     DomainError, NotRootError, PermissionError, VMMError
from VirtualMailManager.mailbox import new as new_mailbox
from VirtualMailManager.pycompat import all, any
from VirtualMailManager.relocated import Relocated
from VirtualMailManager.transport import Transport


_ = lambda msg: msg

CFG_FILE = 'vmm.cfg'
CFG_PATH = '/root:/usr/local/etc:/etc'
RE_DOMAIN_SEARCH = """^[a-z0-9-\.]+$"""
TYPE_ACCOUNT = 0x1
TYPE_ALIAS = 0x2
TYPE_RELOCATED = 0x4
OTHER_TYPES = {
    TYPE_ACCOUNT: (_(u'an account'), ACCOUNT_EXISTS),
    TYPE_ALIAS: (_(u'an alias'), ALIAS_EXISTS),
    TYPE_RELOCATED: (_(u'a relocated user'), RELOCATED_EXISTS),
}


class Handler(object):
    """Wrapper class to simplify the access on all the stuff from
    VirtualMailManager"""
    __slots__ = ('_cfg', '_cfg_fname', '_dbh', '_warnings')

    def __init__(self, skip_some_checks=False):
        """Creates a new Handler instance.

        ``skip_some_checks`` : bool
            When a derived class knows how to handle all checks this
            argument may be ``True``. By default it is ``False`` and
            all checks will be performed.

        Throws a NotRootError if your uid is greater 0.
        """
        self._cfg_fname = ''
        self._warnings = []
        self._cfg = None
        self._dbh = None

        if os.geteuid():
            raise NotRootError(_(u"You are not root.\n\tGood bye!\n"),
                               CONF_NOPERM)
        if self._check_cfg_file():
            self._cfg = Cfg(self._cfg_fname)
            self._cfg.load()
        if not skip_some_checks:
            self._cfg.check()
            self._chkenv()

    def _find_cfg_file(self):
        """Search the CFG_FILE in CFG_PATH.
        Raise a VMMError when no vmm.cfg could be found.
        """
        for path in CFG_PATH.split(':'):
            tmp = os.path.join(path, CFG_FILE)
            if os.path.isfile(tmp):
                self._cfg_fname = tmp
                break
        if not self._cfg_fname:
            raise VMMError(_(u"Could not find '%(cfg_file)s' in: "
                             u"'%(cfg_path)s'") % {'cfg_file': CFG_FILE,
                           'cfg_path': CFG_PATH}, CONF_NOFILE)

    def _check_cfg_file(self):
        """Checks the configuration file, returns bool"""
        self._find_cfg_file()
        fstat = os.stat(self._cfg_fname)
        fmode = int(oct(fstat.st_mode & 0777))
        if fmode % 100 and fstat.st_uid != fstat.st_gid or \
           fmode % 10 and fstat.st_uid == fstat.st_gid:
            raise PermissionError(_(u"wrong permissions for '%(file)s': "
                                    u"%(perms)s\n`chmod 0600 %(file)s` would "
                                    u"be great.") % {'file': self._cfg_fname,
                                  'perms': fmode}, CONF_WRONGPERM)
        else:
            return True

    def _chkenv(self):
        """Make sure our base_directory is a directory and that all
        required executables exists and are executable.
        If not, a VMMError will be raised"""
        dir_created = False
        basedir = self._cfg.dget('misc.base_directory')
        if not os.path.exists(basedir):
            old_umask = os.umask(0006)
            os.makedirs(basedir, 0771)
            os.chown(basedir, 0, 0)
            os.umask(old_umask)
            dir_created = True
        if not dir_created and not lisdir(basedir):
            raise VMMError(_(u"'%(path)s' is not a directory.\n(%(cfg_file)s: "
                             u"section 'misc', option 'base_directory')") %
                           {'path': basedir, 'cfg_file': self._cfg_fname},
                           NO_SUCH_DIRECTORY)
        for opt, val in self._cfg.items('bin'):
            try:
                exec_ok(val)
            except VMMError, err:
                if err.code is NO_SUCH_BINARY:
                    raise VMMError(_(u"'%(binary)s' doesn't exist.\n"
                                     u"(%(cfg_file)s: section 'bin', option "
                                     u"'%(option)s')") % {'binary': val,
                                   'cfg_file': self._cfg_fname, 'option': opt},
                                   err.code)
                elif err.code is NOT_EXECUTABLE:
                    raise VMMError(_(u"'%(binary)s' is not executable.\n"
                                     u"(%(cfg_file)s: section 'bin', option "
                                     u"'%(option)s')") % {'binary': val,
                                   'cfg_file': self._cfg_fname, 'option': opt},
                                   err.code)
                else:
                    raise

    def _db_connect(self):
        """Creates a pyPgSQL.PgSQL.connection instance."""
        if self._dbh is None or (isinstance(self._dbh, PgSQL.Connection) and
                                  not self._dbh._isOpen):
            try:
                self._dbh = PgSQL.connect(
                        database=self._cfg.dget('database.name'),
                        user=self._cfg.pget('database.user'),
                        host=self._cfg.dget('database.host'),
                        password=self._cfg.pget('database.pass'),
                        client_encoding='utf8', unicode_results=True)
                dbc = self._dbh.cursor()
                dbc.execute("SET NAMES 'UTF8'")
                dbc.close()
            except PgSQL.libpq.DatabaseError, err:
                raise VMMError(str(err), DATABASE_ERROR)

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
            if account:
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

    def _is_other_address(self, address, exclude):
        """Checks if *address* is known for an Account (TYPE_ACCOUNT),
        Alias (TYPE_ALIAS) or Relocated (TYPE_RELOCATED), except for
        *exclude*.  Returns `False` if the address is not known for other
        types.

        Raises a `VMMError` if the address is known.
        """
        other = self._chk_other_address_types(address, exclude)
        if not other:
            return False
        # TP: %(a_type)s will be one of: 'an account', 'an alias' or
        # 'a relocated user'
        msg = _(u"There is already %(a_type)s with the address '%(address)s'.")
        raise VMMError(msg % {'a_type': OTHER_TYPES[other][0],
                              'address': address}, OTHER_TYPES[other][1])

    def _get_account(self, address):
        """Return an Account instances for the given address (str)."""
        address = EmailAddress(address)
        self._db_connect()
        return Account(self._dbh, address)

    def _get_alias(self, address):
        """Return an Alias instances for the given address (str)."""
        address = EmailAddress(address)
        self._db_connect()
        return Alias(self._dbh, address)

    def _get_relocated(self, address):
        """Return a Relocated instances for the given address (str)."""
        address = EmailAddress(address)
        self._db_connect()
        return Relocated(self._dbh, address)

    def _get_domain(self, domainname):
        """Return a Domain instances for the given domain name (str)."""
        self._db_connect()
        return Domain(self._dbh, domainname)

    def _get_disk_usage(self, directory):
        """Estimate file space usage for the given directory.

        Arguments:

        `directory` : basestring
          The directory to summarize recursively disk usage for
        """
        if lisdir(directory):
            return Popen([self._cfg.dget('bin.du'), "-hs", directory],
                         stdout=PIPE).communicate()[0].split('\t')[0]
        else:
            self._warnings.append(_('No such directory: %s') % directory)
            return 0

    def _make_domain_dir(self, domain):
        """Create a directory for the `domain` and its accounts."""
        cwd = os.getcwd()
        hashdir, domdir = domain.directory.split(os.path.sep)[-2:]
        dir_created = False
        os.chdir(self._cfg.dget('misc.base_directory'))
        if not os.path.exists(hashdir):
            os.mkdir(hashdir, 0711)
            os.chown(hashdir, 0, 0)
            dir_created = True
        if not dir_created and not lisdir(hashdir):
            raise VMMError(_(u"'%s' is not a directory.") % hashdir,
                           NO_SUCH_DIRECTORY)
        os.mkdir(os.path.join(hashdir, domdir),
                 self._cfg.dget('domain.directory_mode'))
        os.chown(domain.directory, 0, domain.gid)
        os.chdir(cwd)

    def _make_home(self, account):
        """Create a home directory for the new Account *account*."""
        domdir = account.domain.directory
        if not lisdir(domdir):
            self._make_domain_dir(account.domain)
        os.umask(0007)
        uid = account.uid
        os.chdir(domdir)
        os.mkdir('%s' % uid, self._cfg.dget('account.directory_mode'))
        os.chown('%s' % uid, uid, account.gid)

    def _make_account_dirs(self, account):
        """Create all necessary directories for the account."""
        oldpwd = os.getcwd()
        self._make_home(account)
        mailbox = new_mailbox(account)
        mailbox.create()
        folders = self._cfg.dget('mailbox.folders').split(':')
        if any(folders):
            bad = mailbox.add_boxes(folders,
                                    self._cfg.dget('mailbox.subscribe'))
            if bad:
                self._warnings.append(_(u"Skipped mailbox folders:") +
                                      '\n\t- ' + '\n\t- '.join(bad))
        os.chdir(oldpwd)

    def _delete_home(self, domdir, uid, gid):
        """Delete a user's home directory.

        Arguments:

        `domdir` : basestring
          The directory of the domain the user belongs to
          (commonly AccountObj.domain.directory)
        `uid` : int/long
          The user's UID (commonly AccountObj.uid)
        `gid` : int/long
          The user's GID (commonly AccountObj.gid)
        """
        assert all(isinstance(xid, (long, int)) for xid in (uid, gid)) and \
                isinstance(domdir, basestring)
        if uid < MIN_UID or gid < MIN_GID:
            raise VMMError(_(u"UID '%(uid)u' and/or GID '%(gid)u' are less "
                             u"than %(min_uid)u/%(min_gid)u.") % {'uid': uid,
                           'gid': gid, 'min_gid': MIN_GID, 'min_uid': MIN_UID},
                           MAILDIR_PERM_MISMATCH)
        if domdir.count('..'):
            raise VMMError(_(u'Found ".." in domain directory path: %s') %
                           domdir, FOUND_DOTS_IN_PATH)
        if not lisdir(domdir):
            raise VMMError(_(u"No such directory: %s") % domdir,
                           NO_SUCH_DIRECTORY)
        os.chdir(domdir)
        userdir = '%s' % uid
        if not lisdir(userdir):
            self._warnings.append(_(u"No such directory: %s") %
                                  os.path.join(domdir, userdir))
            return
        mdstat = os.lstat(userdir)
        if (mdstat.st_uid, mdstat.st_gid) != (uid, gid):
            raise VMMError(_(u'Detected owner/group mismatch in home '
                             u'directory.'), MAILDIR_PERM_MISMATCH)
        rmtree(userdir, ignore_errors=True)

    def _delete_domain_dir(self, domdir, gid):
        """Delete a domain's directory.

        Arguments:

        `domdir` : basestring
          The domain's directory (commonly DomainObj.directory)
        `gid` : int/long
          The domain's GID (commonly DomainObj.gid)
        """
        assert isinstance(domdir, basestring) and isinstance(gid, (long, int))
        if gid < MIN_GID:
            raise VMMError(_(u"GID '%(gid)u' is less than '%(min_gid)u'.") %
                           {'gid': gid, 'min_gid': MIN_GID},
                           DOMAINDIR_GROUP_MISMATCH)
        if domdir.count('..'):
            raise VMMError(_(u'Found ".." in domain directory path: %s') %
                           domdir, FOUND_DOTS_IN_PATH)
        if not lisdir(domdir):
            self._warnings.append(_('No such directory: %s') % domdir)
            return
        dirst = os.lstat(domdir)
        if dirst.st_gid != gid:
            raise VMMError(_(u'Detected group mismatch in domain directory: '
                             u'%s') % domdir, DOMAINDIR_GROUP_MISMATCH)
        rmtree(domdir, ignore_errors=True)

    def has_warnings(self):
        """Checks if warnings are present, returns bool."""
        return bool(len(self._warnings))

    def get_warnings(self):
        """Returns a list with all available warnings and resets all
        warnings.
        """
        ret_val = self._warnings[:]
        del self._warnings[:]
        return ret_val

    def cfg_dget(self, option):
        """Get the configured value of the *option* (section.option).
        When the option was not configured its default value will be
        returned."""
        return self._cfg.dget(option)

    def cfg_pget(self, option):
        """Get the configured value of the *option* (section.option)."""
        return self._cfg.pget(option)

    def cfg_install(self):
        """Installs the cfg_dget method as ``cfg_dget`` into the built-in
        namespace."""
        import __builtin__
        assert 'cfg_dget' not in __builtin__.__dict__
        __builtin__.__dict__['cfg_dget'] = self._cfg.dget

    def domain_add(self, domainname, transport=None):
        """Wrapper around Domain.set_transport() and Domain.save()"""
        dom = self._get_domain(domainname)
        if transport is None:
            dom.set_transport(Transport(self._dbh,
                              transport=self._cfg.dget('misc.transport')))
        else:
            dom.set_transport(Transport(self._dbh, transport=transport))
        dom.set_directory(self._cfg.dget('misc.base_directory'))
        dom.save()
        self._make_domain_dir(dom)

    def domain_transport(self, domainname, transport, force=None):
        """Wrapper around Domain.update_transport()"""
        if force is not None and force != 'force':
            raise DomainError(_(u"Invalid argument: '%s'") % force,
                              INVALID_ARGUMENT)
        dom = self._get_domain(domainname)
        trsp = Transport(self._dbh, transport=transport)
        if force is None:
            dom.update_transport(trsp)
        else:
            dom.update_transport(trsp, force=True)

    def domain_delete(self, domainname, force=False):
        """Wrapper around Domain.delete()"""
        if not isinstance(force, bool):
            raise TypeError('force must be a bool')
        dom = self._get_domain(domainname)
        gid = dom.gid
        domdir = dom.directory
        if self._cfg.dget('domain.force_deletion') or force:
            dom.delete(True)
        else:
            dom.delete(False)
        if self._cfg.dget('domain.delete_directory'):
            self._delete_domain_dir(domdir, gid)

    def domain_info(self, domainname, details=None):
        """Wrapper around Domain.get_info(), Domain.get_accounts(),
        Domain.get_aliase_names(), Domain.get_aliases() and
        Domain.get_relocated."""
        if details not in [None, 'accounts', 'aliasdomains', 'aliases', 'full',
                           'relocated']:
            raise VMMError(_(u"Invalid argument: '%s'") % details,
                           INVALID_ARGUMENT)
        dom = self._get_domain(domainname)
        dominfo = dom.get_info()
        if dominfo['domainname'].startswith('xn--'):
            dominfo['domainname'] += ' (%s)' % \
                                     dominfo['domainname'].decode('idna')
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

    def aliasdomain_add(self, aliasname, domainname):
        """Adds an alias domain to the domain.

        Arguments:

        `aliasname` : basestring
          The name of the alias domain
        `domainname` : basestring
          The name of the target domain
        """
        dom = self._get_domain(domainname)
        alias_dom = AliasDomain(self._dbh, aliasname)
        alias_dom.set_destination(dom)
        alias_dom.save()

    def aliasdomain_info(self, aliasname):
        """Returns a dict (keys: "alias" and "domain") with the names of
        the alias domain and its primary domain."""
        self._db_connect()
        alias_dom = AliasDomain(self._dbh, aliasname)
        return alias_dom.info()

    def aliasdomain_switch(self, aliasname, domainname):
        """Modifies the target domain of an existing alias domain.

        Arguments:

        `aliasname` : basestring
          The name of the alias domain
        `domainname` : basestring
          The name of the new target domain
        """
        dom = self._get_domain(domainname)
        alias_dom = AliasDomain(self._dbh, aliasname)
        alias_dom.set_destination(dom)
        alias_dom.switch()

    def aliasdomain_delete(self, aliasname):
        """Deletes the given alias domain.

        Argument:

        `aliasname` : basestring
          The name of the alias domain
        """
        self._db_connect()
        alias_dom = AliasDomain(self._dbh, aliasname)
        alias_dom.delete()

    def domain_list(self, pattern=None):
        """Wrapper around function search() from module Domain."""
        from VirtualMailManager.domain import search
        like = False
        if pattern and (pattern.startswith('%') or pattern.endswith('%')):
            like = True
            if not re.match(RE_DOMAIN_SEARCH, pattern.strip('%')):
                raise VMMError(_(u"The pattern '%s' contains invalid "
                                 u"characters.") % pattern, DOMAIN_INVALID)
        self._db_connect()
        return search(self._dbh, pattern=pattern, like=like)

    def user_add(self, emailaddress, password):
        """Wrapper around Account.set_password() and Account.save()."""
        acc = self._get_account(emailaddress)
        if acc:
            raise VMMError(_(u"The account '%s' already exists.") %
                           acc.address, ACCOUNT_EXISTS)
        acc.set_password(password)
        acc.save()
        self._make_account_dirs(acc)

    def alias_add(self, aliasaddress, *targetaddresses):
        """Creates a new `Alias` entry for the given *aliasaddress* with
        the given *targetaddresses*."""
        alias = self._get_alias(aliasaddress)
        destinations = [EmailAddress(address) for address in targetaddresses]
        warnings = []
        destinations = alias.add_destinations(destinations, warnings)
        if warnings:
            self._warnings.append(_('Ignored destination addresses:'))
            self._warnings.extend(('  * %s' % w for w in warnings))
        for destination in destinations:
            if get_gid(self._dbh, destination.domainname) and \
               not self._chk_other_address_types(destination, TYPE_RELOCATED):
                self._warnings.append(_(u"The destination account/alias '%s' "
                                        u"doesn't exist.") % destination)

    def user_delete(self, emailaddress, force=False):
        """Wrapper around Account.delete(...)"""
        if not isinstance(force, bool):
            raise TypeError('force must be a bool')
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, NO_SUCH_ACCOUNT)
        uid = acc.uid
        gid = acc.gid
        dom_dir = acc.domain.directory
        acc_dir = acc.home
        acc.delete(force)
        if self._cfg.dget('account.delete_directory'):
            try:
                self._delete_home(dom_dir, uid, gid)
            except VMMError, err:
                if err.code in (FOUND_DOTS_IN_PATH, MAILDIR_PERM_MISMATCH,
                                NO_SUCH_DIRECTORY):
                    warning = _(u"""\
The account has been successfully deleted from the database.
    But an error occurred while deleting the following directory:
    '%(directory)s'
    Reason: %(reason)s""") % {'directory': acc_dir, 'reason': err.msg}
                    self._warnings.append(warning)
                else:
                    raise

    def alias_info(self, aliasaddress):
        """Returns an iterator object for all destinations (`EmailAddress`
        instances) for the `Alias` with the given *aliasaddress*."""
        alias = self._get_alias(aliasaddress)
        if alias:
            return alias.get_destinations()
        if not self._is_other_address(alias.address, TYPE_ALIAS):
            raise VMMError(_(u"The alias '%s' doesn't exist.") %
                           alias.address, NO_SUCH_ALIAS)

    def alias_delete(self, aliasaddress, targetaddress=None):
        """Deletes the `Alias` *aliasaddress* with all its destinations from
        the database. If *targetaddress* is not ``None``, only this
        destination will be removed from the alias."""
        alias = self._get_alias(aliasaddress)
        if targetaddress is None:
            alias.delete()
        else:
            alias.del_destination(EmailAddress(targetaddress))

    def user_info(self, emailaddress, details=None):
        """Wrapper around Account.get_info(...)"""
        if details not in (None, 'du', 'aliases', 'full'):
            raise VMMError(_(u"Invalid argument: '%s'") % details,
                           INVALID_ARGUMENT)
        acc = self._get_account(emailaddress)
        if not acc:
            if not self._is_other_address(acc.address, TYPE_ACCOUNT):
                raise VMMError(_(u"The account '%s' doesn't exist.") %
                               acc.address, NO_SUCH_ACCOUNT)
        info = acc.get_info()
        if self._cfg.dget('account.disk_usage') or details in ('du', 'full'):
            path = os.path.join(acc.home, acc.mail_location.directory)
            info['disk usage'] = self._get_disk_usage(path)
            if details in (None, 'du'):
                return info
        if details in ('aliases', 'full'):
            return (info, acc.get_aliases())
        return info

    def user_by_uid(self, uid):
        """Search for an Account by its *uid*.
        Returns a dict (address, uid and gid) if a user could be found."""
        from VirtualMailManager.account import get_account_by_uid
        self._db_connect()
        return get_account_by_uid(uid, self._dbh)

    def user_password(self, emailaddress, password):
        """Wrapper for Account.modify('password' ...)."""
        if not isinstance(password, basestring) or not password:
            raise VMMError(_(u"Could not accept password: '%s'") % password,
                           INVALID_ARGUMENT)
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, NO_SUCH_ACCOUNT)
        acc.modify('password', password)

    def user_name(self, emailaddress, name):
        """Wrapper for Account.modify('name', ...)."""
        if not isinstance(name, basestring) or not name:
            raise VMMError(_(u"Could not accept name: '%s'") % name,
                           INVALID_ARGUMENT)
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, NO_SUCH_ACCOUNT)
        acc.modify('name', name)

    def user_transport(self, emailaddress, transport):
        """Wrapper for Account.modify('transport', ...)."""
        if not isinstance(transport, basestring) or not transport:
            raise VMMError(_(u"Could not accept transport: '%s'") % transport,
                           INVALID_ARGUMENT)
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") %
                           acc.address, NO_SUCH_ACCOUNT)
        acc.modify('transport', transport)

    def user_disable(self, emailaddress, services=None):
        """Wrapper for Account.disable(*services)"""
        if services is None:
            services = []
        else:
            assert isinstance(services, list)
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") % acc.address,
                           NO_SUCH_ACCOUNT)
        acc.disable(*services)

    def user_enable(self, emailaddress, services=None):
        """Wrapper for Account.enable(*services)"""
        if services is None:
            services = []
        else:
            assert isinstance(services, list)
        acc = self._get_account(emailaddress)
        if not acc:
            raise VMMError(_(u"The account '%s' doesn't exist.") % acc.address,
                           NO_SUCH_ACCOUNT)
        acc.enable(*services)

    def relocated_add(self, emailaddress, targetaddress):
        """Creates a new `Relocated` entry in the database. If there is
        already a relocated user with the given *emailaddress*, only the
        *targetaddress* for the relocated user will be updated."""
        relocated = self._get_relocated(emailaddress)
        relocated.set_destination(EmailAddress(targetaddress))

    def relocated_info(self, emailaddress):
        """Returns the target address of the relocated user with the given
        *emailaddress*."""
        relocated = self._get_relocated(emailaddress)
        if relocated:
            return relocated.get_info()
        if not self._is_other_address(relocated.address, TYPE_RELOCATED):
            raise VMMError(_(u"The relocated user '%s' doesn't exist.") %
                           relocated.address, NO_SUCH_RELOCATED)

    def relocated_delete(self, emailaddress):
        """Deletes the relocated user with the given *emailaddress* from
        the database."""
        relocated = self._get_relocated(emailaddress)
        relocated.delete()

del _
