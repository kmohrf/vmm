# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""The main class for vmm."""


from encodings.idna import ToASCII, ToUnicode
from getpass import getpass
from shutil import rmtree
from subprocess import Popen, PIPE

from pyPgSQL import PgSQL # python-pgsql - http://pypgsql.sourceforge.net

from __main__ import os, re, ENCODING, ERR, w_std
from ext.Postconf import Postconf
from Account import Account
from Alias import Alias
from AliasDomain import AliasDomain
from Config import Config as Cfg
from Domain import Domain
from EmailAddress import EmailAddress
from Exceptions import *
from Relocated import Relocated

SALTCHARS = './0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
RE_ASCII_CHARS = """^[\x20-\x7E]*$"""
RE_DOMAIN = """^(?:[a-z0-9-]{1,63}\.){1,}[a-z]{2,6}$"""
RE_DOMAIN_SRCH = """^[a-z0-9-\.]+$"""
RE_LOCALPART = """[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]"""
RE_MBOX_NAMES = """^[\x20-\x25\x27-\x7E]*$"""

class VirtualMailManager(object):
    """The main class for vmm"""
    __slots__ = ('__Cfg', '__cfgFileName', '__cfgSections', '__dbh', '__scheme',
            '__warnings', '_postconf')
    def __init__(self):
        """Creates a new VirtualMailManager instance.
        Throws a VMMNotRootException if your uid is greater 0.
        """
        self.__cfgFileName = ''
        self.__warnings = []
        self.__Cfg = None
        self.__dbh = None

        if os.geteuid():
            raise VMMNotRootException(_(u"You are not root.\n\tGood bye!\n"),
                ERR.CONF_NOPERM)
        if self.__chkCfgFile():
            self.__Cfg = Cfg(self.__cfgFileName)
            self.__Cfg.load()
            self.__Cfg.check()
            self.__cfgSections = self.__Cfg.getsections()
            self.__scheme = self.__Cfg.get('misc', 'passwdscheme')
            self._postconf = Postconf(self.__Cfg.get('bin', 'postconf'))
        if not os.sys.argv[1] in ['cf', 'configure']:
            self.__chkenv()

    def __findCfgFile(self):
        for path in ['/root', '/usr/local/etc', '/etc']:
            tmp = os.path.join(path, 'vmm.cfg')
            if os.path.isfile(tmp):
                self.__cfgFileName = tmp
                break
        if not len(self.__cfgFileName):
            raise VMMException(
                _(u"No “vmm.cfg” found in: /root:/usr/local/etc:/etc"),
                ERR.CONF_NOFILE)

    def __chkCfgFile(self):
        """Checks the configuration file, returns bool"""
        self.__findCfgFile()
        fstat = os.stat(self.__cfgFileName)
        fmode = int(oct(fstat.st_mode & 0777))
        if fmode % 100 and fstat.st_uid != fstat.st_gid \
        or fmode % 10 and fstat.st_uid == fstat.st_gid:
            raise VMMPermException(_(
                u'fix permissions (%(perms)s) for “%(file)s”\n\
`chmod 0600 %(file)s` would be great.') % {'file':
                self.__cfgFileName, 'perms': fmode}, ERR.CONF_WRONGPERM)
        else:
            return True

    def __chkenv(self):
        """"""
        if not os.path.exists(self.__Cfg.get('domdir', 'base')):
            old_umask = os.umask(0006)
            os.makedirs(self.__Cfg.get('domdir', 'base'), 0771)
            os.chown(self.__Cfg.get('domdir', 'base'), 0,
                    self.__Cfg.getint('misc', 'gid_mail'))
            os.umask(old_umask)
        elif not os.path.isdir(self.__Cfg.get('domdir', 'base')):
            raise VMMException(_(u'“%s” is not a directory.\n\
(vmm.cfg: section "domdir", option "base")') %
                self.__Cfg.get('domdir', 'base'), ERR.NO_SUCH_DIRECTORY)
        for opt, val in self.__Cfg.items('bin'):
            if not os.path.exists(val):
                raise VMMException(_(u'“%(binary)s” doesn\'t exist.\n\
(vmm.cfg: section "bin", option "%(option)s")') %{'binary': val,'option': opt},
                    ERR.NO_SUCH_BINARY)
            elif not os.access(val, os.X_OK):
                raise VMMException(_(u'“%(binary)s” is not executable.\n\
(vmm.cfg: section "bin", option "%(option)s")') %{'binary': val,'option': opt},
                    ERR.NOT_EXECUTABLE)

    def __dbConnect(self):
        """Creates a pyPgSQL.PgSQL.connection instance."""
        if self.__dbh is None or not self.__dbh._isOpen:
            try:
                self.__dbh = PgSQL.connect(
                        database=self.__Cfg.get('database', 'name'),
                        user=self.__Cfg.get('database', 'user'),
                        host=self.__Cfg.get('database', 'host'),
                        password=self.__Cfg.get('database', 'pass'),
                        client_encoding='utf8', unicode_results=True)
                dbc = self.__dbh.cursor()
                dbc.execute("SET NAMES 'UTF8'")
                dbc.close()
            except PgSQL.libpq.DatabaseError, e:
                raise VMMException(str(e), ERR.DATABASE_ERROR)

    def idn2ascii(domainname):
        """Converts an idn domainname in punycode.

        Arguments:
        domainname -- the domainname to convert (unicode)
        """
        return '.'.join([ToASCII(lbl) for lbl in domainname.split('.') if lbl])
    idn2ascii = staticmethod(idn2ascii)

    def ace2idna(domainname):
        """Convertis a domainname from ACE according to IDNA

        Arguments:
        domainname -- the domainname to convert (str)
        """
        return u'.'.join([ToUnicode(lbl) for lbl in domainname.split('.')\
                if lbl])
    ace2idna = staticmethod(ace2idna)

    def chkDomainname(domainname):
        """Validates the domain name of an e-mail address.

        Keyword arguments:
        domainname -- the domain name that should be validated
        """
        if not re.match(RE_ASCII_CHARS, domainname):
            domainname = VirtualMailManager.idn2ascii(domainname)
        if len(domainname) > 255:
            raise VMMException(_(u'The domain name is too long.'),
                ERR.DOMAIN_TOO_LONG)
        if not re.match(RE_DOMAIN, domainname):
            raise VMMException(_(u'The domain name “%s” is invalid.') %\
                    domainname, ERR.DOMAIN_INVALID)
        return domainname
    chkDomainname = staticmethod(chkDomainname)

    def _exists(dbh, query):
        dbc = dbh.cursor()
        dbc.execute(query)
        gid = dbc.fetchone()
        dbc.close()
        if gid is None:
            return False
        else:
            return True
    _exists = staticmethod(_exists)

    def accountExists(dbh, address):
        sql = "SELECT gid FROM users WHERE gid = (SELECT gid FROM domain_name\
 WHERE domainname = '%s') AND local_part = '%s'" % (address._domainname,
            address._localpart)
        return VirtualMailManager._exists(dbh, sql)
    accountExists = staticmethod(accountExists)

    def aliasExists(dbh, address):
        sql = "SELECT DISTINCT gid FROM alias WHERE gid = (SELECT gid FROM\
 domain_name WHERE domainname = '%s') AND address = '%s'" %\
            (address._domainname, address._localpart)
        return VirtualMailManager._exists(dbh, sql)
    aliasExists = staticmethod(aliasExists)

    def relocatedExists(dbh, address):
        sql = "SELECT gid FROM relocated WHERE gid = (SELECT gid FROM\
 domain_name WHERE domainname = '%s') AND address = '%s'" %\
            (address._domainname, address._localpart)
        return VirtualMailManager._exists(dbh, sql)
    relocatedExists = staticmethod(relocatedExists)

    def _readpass(self):
        # TP: Please preserve the trailing space.
        readp_msg0 = _(u'Enter new password: ').encode(ENCODING, 'replace')
        # TP: Please preserve the trailing space.
        readp_msg1 = _(u'Retype new password: ').encode(ENCODING, 'replace')
        mismatched = True
        flrs = 0
        while mismatched:
            if flrs > 2:
                raise VMMException(_(u'Too many failures - try again later.'),
                        ERR.VMM_TOO_MANY_FAILURES)
            clear0 = getpass(prompt=readp_msg0)
            clear1 = getpass(prompt=readp_msg1)
            if clear0 != clear1:
                flrs += 1
                w_std(_(u'Sorry, passwords do not match'))
                continue
            if len(clear0) < 1:
                flrs += 1
                w_std(_(u'Sorry, empty passwords are not permitted'))
                continue
            mismatched = False
        return clear0

    def __getAccount(self, address, password=None):
        self.__dbConnect()
        address = EmailAddress(address)
        if not password is None:
            password = self.__pwhash(password)
        return Account(self.__dbh, address, password)

    def __getAlias(self, address, destination=None):
        self.__dbConnect()
        address = EmailAddress(address)
        if destination is not None:
            destination = EmailAddress(destination)
        return Alias(self.__dbh, address, destination)

    def __getRelocated(self,address, destination=None):
        self.__dbConnect()
        address = EmailAddress(address)
        if destination is not None:
            destination = EmailAddress(destination)
        return Relocated(self.__dbh, address, destination)

    def __getDomain(self, domainname, transport=None):
        if transport is None:
            transport = self.__Cfg.get('misc', 'transport')
        self.__dbConnect()
        return Domain(self.__dbh, domainname,
                self.__Cfg.get('domdir', 'base'), transport)

    def __getDiskUsage(self, directory):
        """Estimate file space usage for the given directory.

        Keyword arguments:
        directory -- the directory to summarize recursively disk usage for
        """
        if self.__isdir(directory):
            return Popen([self.__Cfg.get('bin', 'du'), "-hs", directory],
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
            mode = self.__Cfg.getint('maildir', 'mode')
        if uid is None:
            uid = 0
        if gid is None:
            gid = 0
        os.makedirs(directory, mode)
        os.chown(directory, uid, gid)

    def __domDirMake(self, domdir, gid):
        os.umask(0006)
        oldpwd = os.getcwd()
        basedir = self.__Cfg.get('domdir', 'base')
        domdirdirs = domdir.replace(basedir+'/', '').split('/')

        os.chdir(basedir)
        if not os.path.isdir(domdirdirs[0]):
            self.__makedir(domdirdirs[0], 489, 0,
                    self.__Cfg.getint('misc', 'gid_mail'))
        os.chdir(domdirdirs[0])
        os.umask(0007)
        self.__makedir(domdirdirs[1], self.__Cfg.getint('domdir', 'mode'), 0,
                gid)
        os.chdir(oldpwd)

    def __subscribeFL(self, folderlist, uid, gid):
        fname = os.path.join(self.__Cfg.get('maildir','name'), 'subscriptions')
        sf = file(fname, 'w')
        for f in folderlist:
            sf.write(f+'\n')
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
        os.umask(0007)
        oldpwd = os.getcwd()
        os.chdir(domdir)

        maildir = self.__Cfg.get('maildir', 'name')
        folders = [maildir]
        for folder in self.__Cfg.get('maildir', 'folders').split(':'):
            folder = folder.strip()
            if len(folder) and not folder.count('..')\
            and re.match(RE_MBOX_NAMES, folder):
                folders.append('%s/.%s' % (maildir, folder))
        subdirs = ['cur', 'new', 'tmp']
        mode = self.__Cfg.getint('maildir', 'mode')

        self.__makedir('%s' % uid, mode, uid, gid)
        os.chdir('%s' % uid)
        for folder in folders:
            self.__makedir(folder, mode, uid, gid)
            for subdir in subdirs:
                self.__makedir(os.path.join(folder, subdir), mode, uid, gid)
        self.__subscribeFL([f.replace(maildir+'/.', '') for f in folders[1:]],
                uid, gid)
        os.chdir(oldpwd)

    def __userDirDelete(self, domdir, uid, gid):
        if uid > 0 and gid > 0:
            userdir = '%s' % uid
            if userdir.count('..') or domdir.count('..'):
                raise VMMException(_(u'Found ".." in home directory path.'),
                    ERR.FOUND_DOTS_IN_PATH)
            if os.path.isdir(domdir):
                os.chdir(domdir)
                if os.path.isdir(userdir):
                    mdstat = os.stat(userdir)
                    if (mdstat.st_uid, mdstat.st_gid) != (uid, gid):
                        raise VMMException(
                         _(u'Detected owner/group mismatch in home directory.'),
                         ERR.MAILDIR_PERM_MISMATCH)
                    rmtree(userdir, ignore_errors=True)
                else:
                    raise VMMException(_(u"No such directory: %s") %
                        os.path.join(domdir, userdir), ERR.NO_SUCH_DIRECTORY)

    def __domDirDelete(self, domdir, gid):
        if gid > 0:
            if not self.__isdir(domdir):
                return
            basedir = self.__Cfg.get('domdir', 'base')
            domdirdirs = domdir.replace(basedir+'/', '').split('/')
            domdirparent = os.path.join(basedir, domdirdirs[0])
            if basedir.count('..') or domdir.count('..'):
                raise VMMException(_(u'Found ".." in domain directory path.'),
                        ERR.FOUND_DOTS_IN_PATH)
            if os.path.isdir(domdirparent):
                os.chdir(domdirparent)
                if os.lstat(domdirdirs[1]).st_gid != gid:
                    raise VMMException(_(
                        u'Detected group mismatch in domain directory.'),
                        ERR.DOMAINDIR_GROUP_MISMATCH)
                rmtree(domdirdirs[1], ignore_errors=True)

    def __getSalt(self):
        from random import choice
        salt = None
        if self.__scheme == 'CRYPT':
            salt = '%s%s' % (choice(SALTCHARS), choice(SALTCHARS))
        elif self.__scheme in ['MD5', 'MD5-CRYPT']:
            salt = '$1$%s$' % ''.join([choice(SALTCHARS) for x in xrange(8)])
        return salt

    def __pwCrypt(self, password):
        # for: CRYPT, MD5 and MD5-CRYPT
        from crypt import crypt
        return crypt(password, self.__getSalt())

    def __pwSHA1(self, password):
        # for: SHA/SHA1
        import sha
        from base64 import standard_b64encode
        sha1 = sha.new(password)
        return standard_b64encode(sha1.digest())

    def __pwMD5(self, password, emailaddress=None):
        import md5
        _md5 = md5.new(password)
        if self.__scheme == 'LDAP-MD5':
            from base64 import standard_b64encode
            return standard_b64encode(_md5.digest())
        elif self.__scheme == 'PLAIN-MD5':
            return _md5.hexdigest()
        elif self.__scheme == 'DIGEST-MD5' and emailaddress is not None:
            # use an empty realm - works better with usenames like user@dom
            _md5 = md5.new('%s::%s' % (emailaddress, password))
            return _md5.hexdigest()

    def __pwMD4(self, password):
        # for: PLAIN-MD4
        from Crypto.Hash import MD4
        _md4 = MD4.new(password)
        return _md4.hexdigest()

    def __pwhash(self, password, scheme=None, user=None):
        if scheme is not None:
            self.__scheme = scheme
        if self.__scheme in ['CRYPT', 'MD5', 'MD5-CRYPT']:
            return '{%s}%s' % (self.__scheme, self.__pwCrypt(password))
        elif self.__scheme in ['SHA', 'SHA1']:
            return '{%s}%s' % (self.__scheme, self.__pwSHA1(password))
        elif self.__scheme in ['PLAIN-MD5', 'LDAP-MD5', 'DIGEST-MD5']:
            return '{%s}%s' % (self.__scheme, self.__pwMD5(password, user))
        elif self.__scheme == 'PLAIN-MD4':
            return '{%s}%s' % (self.__scheme, self.__pwMD4(password))
        elif self.__scheme in ['SMD5', 'SSHA', 'CRAM-MD5', 'HMAC-MD5',
                'LANMAN', 'NTLM', 'RPA']:
            cmd_args = [self.__Cfg.get('bin', 'dovecotpw'), '-s',
                        self.__scheme, '-p', password]
            if self.__Cfg.getint('misc', 'dovecotvers') >= 20:
                cmd_args.insert(1, 'pw')
            return Popen(cmd_args, stdout=PIPE).communicate()[0][:-1]
        else:
            return '{%s}%s' % (self.__scheme, password)

    def hasWarnings(self):
        """Checks if warnings are present, returns bool."""
        return bool(len(self.__warnings))

    def getWarnings(self):
        """Returns a list with all available warnings."""
        return self.__warnings

    def cfgGetBoolean(self, section, option):
        return self.__Cfg.getboolean(section, option)

    def cfgGetInt(self, section, option):
        return self.__Cfg.getint(section, option)

    def cfgGetString(self, section, option):
        return self.__Cfg.get(section, option)

    def setupIsDone(self):
        """Checks if vmm is configured, returns bool"""
        try:
            return self.__Cfg.getboolean('config', 'done')
        except ValueError, e:
            raise VMMConfigException(_(u"""Configuration error: "%s"
(in section "config", option "done") see also: vmm.cfg(5)\n""") % str(e),
                  ERR.CONF_ERROR)

    def configure(self, section=None):
        """Starts interactive configuration.

        Configures in interactive mode options in the given section.
        If no section is given (default) all options from all sections
        will be prompted.

        Keyword arguments:
        section -- the section to configure (default None):
            'database', 'maildir', 'bin' or 'misc'
        """
        if section is None:
            self.__Cfg.configure(self.__cfgSections)
        elif section in self.__cfgSections:
            self.__Cfg.configure([section])
        else:
            raise VMMException(_(u"Invalid section: “%s”") % section,
                ERR.INVALID_SECTION)

    def domainAdd(self, domainname, transport=None):
        dom = self.__getDomain(domainname, transport)
        dom.save()
        self.__domDirMake(dom.getDir(), dom.getID())

    def domainTransport(self, domainname, transport, force=None):
        if force is not None and force != 'force':
            raise VMMDomainException(_(u"Invalid argument: “%s”") % force,
                ERR.INVALID_OPTION)
        dom = self.__getDomain(domainname, None)
        if force is None:
            dom.updateTransport(transport)
        else:
            dom.updateTransport(transport, force=True)

    def domainDelete(self, domainname, force=None):
        if not force is None and force not in ['deluser','delalias','delall']:
            raise VMMDomainException(_(u"Invalid argument: “%s”") % force,
                ERR.INVALID_OPTION)
        dom = self.__getDomain(domainname)
        gid = dom.getID()
        domdir = dom.getDir()
        if self.__Cfg.getboolean('misc', 'forcedel') or force == 'delall':
            dom.delete(True, True)
        elif force == 'deluser':
            dom.delete(delUser=True)
        elif force == 'delalias':
            dom.delete(delAlias=True)
        else:
            dom.delete()
        if self.__Cfg.getboolean('domdir', 'delete'):
            self.__domDirDelete(domdir, gid)

    def domainInfo(self, domainname, details=None):
        if details not in [None, 'accounts', 'aliasdomains', 'aliases', 'full',
                'relocated', 'detailed']:
            raise VMMException(_(u'Invalid argument: “%s”') % details,
                    ERR.INVALID_AGUMENT)
        if details == 'detailed':
            details = 'full'
            self.__warnings.append(_(u'\
The keyword “detailed” is deprecated and will be removed in a future release.\n\
   Please use the keyword “full” to get full details.'))
        dom = self.__getDomain(domainname)
        dominfo = dom.getInfo()
        if dominfo['domainname'].startswith('xn--'):
            dominfo['domainname'] += ' (%s)'\
                % VirtualMailManager.ace2idna(dominfo['domainname'])
        if details is None:
            return dominfo
        elif details == 'accounts':
            return (dominfo, dom.getAccounts())
        elif details == 'aliasdomains':
            return (dominfo, dom.getAliaseNames())
        elif details == 'aliases':
            return (dominfo, dom.getAliases())
        elif details == 'relocated':
            return(dominfo, dom.getRelocated())
        else:
            return (dominfo, dom.getAliaseNames(), dom.getAccounts(),
                    dom.getAliases(), dom.getRelocated())

    def aliasDomainAdd(self, aliasname, domainname):
        """Adds an alias domain to the domain.

        Keyword arguments:
        aliasname -- the name of the alias domain (str)
        domainname -- name of the target domain (str)
        """
        dom = self.__getDomain(domainname)
        aliasDom = AliasDomain(self.__dbh, aliasname, dom)
        aliasDom.save()

    def aliasDomainInfo(self, aliasname):
        self.__dbConnect()
        aliasDom = AliasDomain(self.__dbh, aliasname, None)
        return aliasDom.info()

    def aliasDomainSwitch(self, aliasname, domainname):
        """Modifies the target domain of an existing alias domain.

        Keyword arguments:
        aliasname -- the name of the alias domain (str)
        domainname -- name of the new target domain (str)
        """
        dom = self.__getDomain(domainname)
        aliasDom = AliasDomain(self.__dbh, aliasname, dom)
        aliasDom.switch()

    def aliasDomainDelete(self, aliasname):
        """Deletes the specified alias domain.

        Keyword arguments:
        aliasname -- the name of the alias domain (str)
        """
        self.__dbConnect()
        aliasDom = AliasDomain(self.__dbh, aliasname, None)
        aliasDom.delete()

    def domainList(self, pattern=None):
        from Domain import search
        like = False
        if pattern is not None:
            if pattern.startswith('%') or pattern.endswith('%'):
                like = True
                domain = pattern.strip('%')
                if not re.match(RE_DOMAIN_SRCH, domain):
                    raise VMMException(
                    _(u"The pattern “%s” contains invalid characters.") %
                    pattern, ERR.DOMAIN_INVALID)
        self.__dbConnect()
        return search(self.__dbh, pattern=pattern, like=like)

    def userAdd(self, emailaddress, password):
        acc = self.__getAccount(emailaddress, password)
        if password is None:
            password = self._readpass()
            acc.setPassword(self.__pwhash(password))
        acc.save(self.__Cfg.get('maildir', 'name'),
                self.__Cfg.getint('misc', 'dovecotvers'),
                self.__Cfg.getboolean('services', 'smtp'),
                self.__Cfg.getboolean('services', 'pop3'),
                self.__Cfg.getboolean('services', 'imap'),
                self.__Cfg.getboolean('services', 'sieve'))
        self.__mailDirMake(acc.getDir('domain'), acc.getUID(), acc.getGID())

    def aliasAdd(self, aliasaddress, targetaddress):
        alias = self.__getAlias(aliasaddress, targetaddress)
        alias.save(long(self._postconf.read('virtual_alias_expansion_limit')))
        gid = self.__getDomain(alias._dest._domainname).getID()
        if gid > 0 and not VirtualMailManager.accountExists(self.__dbh,
        alias._dest) and not VirtualMailManager.aliasExists(self.__dbh,
        alias._dest):
            self.__warnings.append(
                _(u"The destination account/alias “%s” doesn't exist.")%\
                        alias._dest)

    def userDelete(self, emailaddress, force=None):
        if force not in [None, 'delalias']:
            raise VMMException(_(u"Invalid argument: “%s”") % force,
                    ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        uid = acc.getUID()
        gid = acc.getGID()
        acc.delete(force)
        if self.__Cfg.getboolean('maildir', 'delete'):
            try:
                self.__userDirDelete(acc.getDir('domain'), uid, gid)
            except VMMException, e:
                if e.code() in [ERR.FOUND_DOTS_IN_PATH,
                        ERR.MAILDIR_PERM_MISMATCH, ERR.NO_SUCH_DIRECTORY]:
                    warning = _(u"""\
The account has been successfully deleted from the database.
    But an error occurred while deleting the following directory:
    “%(directory)s”
    Reason: %(reason)s""") % {'directory': acc.getDir('home'),'reason': e.msg()}
                    self.__warnings.append(warning)
                else:
                    raise e

    def aliasInfo(self, aliasaddress):
        alias = self.__getAlias(aliasaddress)
        return alias.getInfo()

    def aliasDelete(self, aliasaddress, targetaddress=None):
        alias = self.__getAlias(aliasaddress, targetaddress)
        alias.delete()

    def userInfo(self, emailaddress, details=None):
        if details not in [None, 'du', 'aliases', 'full']:
            raise VMMException(_(u'Invalid argument: “%s”') % details,
                    ERR.INVALID_AGUMENT)
        acc = self.__getAccount(emailaddress)
        info = acc.getInfo(self.__Cfg.getint('misc', 'dovecotvers'))
        if self.__Cfg.getboolean('maildir', 'diskusage')\
        or details in ['du', 'full']:
            info['disk usage'] = self.__getDiskUsage('%(maildir)s' % info)
            if details in [None, 'du']:
                return info
        if details in ['aliases', 'full']:
            return (info, acc.getAliases())
        return info

    def userByID(self, uid):
        from Account import getAccountByID
        self.__dbConnect()
        return getAccountByID(uid, self.__dbh)

    def userPassword(self, emailaddress, password):
        acc = self.__getAccount(emailaddress)
        if acc.getUID() == 0:
           raise VMMException(_(u"Account doesn't exist"), ERR.NO_SUCH_ACCOUNT)
        if password is None:
            password = self._readpass()
        acc.modify('password', self.__pwhash(password, user=emailaddress))

    def userName(self, emailaddress, name):
        acc = self.__getAccount(emailaddress)
        acc.modify('name', name)

    def userTransport(self, emailaddress, transport):
        acc = self.__getAccount(emailaddress)
        acc.modify('transport', transport)

    def userDisable(self, emailaddress, service=None):
        if service == 'managesieve':
            service = 'sieve'
            self.__warnings.append(_(u'\
The service name “managesieve” is deprecated and will be removed\n\
   in a future release.\n\
   Please use the service name “sieve” instead.'))
        acc = self.__getAccount(emailaddress)
        acc.disable(self.__Cfg.getint('misc', 'dovecotvers'), service)

    def userEnable(self, emailaddress, service=None):
        if service == 'managesieve':
            service = 'sieve'
            self.__warnings.append(_(u'\
The service name “managesieve” is deprecated and will be removed\n\
   in a future release.\n\
   Please use the service name “sieve” instead.'))
        acc = self.__getAccount(emailaddress)
        acc.enable(self.__Cfg.getint('misc', 'dovecotvers'), service)

    def relocatedAdd(self, emailaddress, targetaddress):
        relocated = self.__getRelocated(emailaddress, targetaddress)
        relocated.save()

    def relocatedInfo(self, emailaddress):
        relocated = self.__getRelocated(emailaddress)
        return relocated.getInfo()

    def relocatedDelete(self, emailaddress):
        relocated = self.__getRelocated(emailaddress)
        relocated.delete()

    def __del__(self):
        if not self.__dbh is None and self.__dbh._isOpen:
            self.__dbh.close()
