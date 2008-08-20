#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""The main class for vmm."""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

import os
import re
import sys
from encodings.idna import ToASCII, ToUnicode
from getpass import getpass
from shutil import rmtree
from subprocess import Popen, PIPE

from pyPgSQL import PgSQL # python-pgsql - http://pypgsql.sourceforge.net

from Exceptions import *
import constants.ERROR as ERR
from Config import Config as Cfg
from Account import Account
from Alias import Alias
from Domain import Domain

SALTCHARS = './0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
RE_ASCII_CHARS = """^[\x20-\x7E]*$"""
RE_DOMAIN = """^(?:[a-z0-9-]{1,63}\.){1,}[a-z]{2,6}$"""
RE_DOMAIN_SRCH = """^[a-z0-9-\.]+$"""
RE_LOCALPART = """[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]"""
RE_MAILLOCATION = """^[\w]{1,20}$"""

class VirtualMailManager:
    """The main class for vmm"""
    def __init__(self):
        """Creates a new VirtualMailManager instance.
        Throws a VMMNotRootException if your uid is greater 0.
        """
        self.__cfgFileName = '/usr/local/etc/vmm.cfg'
        self.__permWarnMsg = _(u"fix permissions for »%(cfgFileName)s«\n\
`chmod 0600 %(cfgFileName)s` would be great.") % {'cfgFileName':
            self.__cfgFileName}
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
        if not sys.argv[1] in ['cf', 'configure']:
            self.__chkenv()

    def __chkCfgFile(self):
        """Checks the configuration file, returns bool"""
        if not os.path.isfile(self.__cfgFileName):
            raise VMMException(_(u"The file »%s« does not exists.") %
                self.__cfgFileName, ERR.CONF_NOFILE)
        fstat = os.stat(self.__cfgFileName)
        fmode = int(oct(fstat.st_mode & 0777))
        if fmode % 100 and fstat.st_uid != fstat.st_gid \
        or fmode % 10 and fstat.st_uid == fstat.st_gid:
            raise VMMPermException(self.__permWarnMsg, ERR.CONF_ERROR)
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
            raise VMMException(_(u'»%s« is not a directory.\n\
(vmm.cfg: section "domdir", option "base")') %
                self.__Cfg.get('domdir', 'base'), ERR.NO_SUCH_DIRECTORY)
        for opt, val in self.__Cfg.items('bin'):
            if not os.path.exists(val):
                raise VMMException(_(u'»%(binary)s« doesn\'t exists.\n\
(vmm.cfg: section "bin", option "%(option)s")') %{'binary': val,'option': opt},
                    ERR.NO_SUCH_BINARY)
            elif not os.access(val, os.X_OK):
                raise VMMException(_(u'»%(binary)s« is not executable.\n\
(vmm.cfg: section "bin", option "%(option)s")') %{'binary': val,'option': opt},
                    ERR.NOT_EXECUTABLE)

    def __dbConnect(self):
        """Creates a pyPgSQL.PgSQL.connection instance."""
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

    def chkLocalpart(localpart):
        """Validates the local part of an e-mail address.
        
        Keyword arguments:
        localpart -- the e-mail address that should be validated (str)
        """
        if len(localpart) < 1:
            raise VMMException(_(u'No localpart specified.'),
                ERR.LOCALPART_INVALID)
        if len(localpart) > 64:
            raise VMMException(_(u'The local part »%s« is too long') %
                localpart, ERR.LOCALPART_TOO_LONG)
        ic = re.compile(RE_LOCALPART).findall(localpart)
        if len(ic):
            ichrs = ''
            for c in set(ic):
                ichrs += u"»%s« " % c
            raise VMMException(_(u"The local part »%(lpart)s« contains invalid\
 characters: %(ichrs)s") % {'lpart': localpart, 'ichrs': ichrs},
                ERR.LOCALPART_INVALID)
        return localpart
    chkLocalpart = staticmethod(chkLocalpart)

    def idn2ascii(domainname):
        """Converts an idn domainname in punycode.
        
        Keyword arguments:
        domainname -- the domainname to convert (str)
        """
        tmp = []
        for label in domainname.split('.'):
            if len(label) == 0:
                continue
            tmp.append(ToASCII(label))
        return '.'.join(tmp)
    idn2ascii = staticmethod(idn2ascii)

    def ace2idna(domainname):
        """Convertis a domainname from ACE according to IDNA
        
        Keyword arguments:
        domainname -- the domainname to convert (str)
        """
        tmp = []
        for label in domainname.split('.'):
            if len(label) == 0:
                continue
            tmp.append(ToUnicode(label))
        return '.'.join(tmp)
    ace2idna = staticmethod(ace2idna)

    def chkDomainname(domainname):
        """Validates the domain name of an e-mail address.
        
        Keyword arguments:
        domainname -- the domain name that should be validated
        """
        re.compile(RE_ASCII_CHARS)
        if not re.match(RE_ASCII_CHARS, domainname):
            domainname = VirtualMailManager.idn2ascii(domainname)
        if len(domainname) > 255:
            raise VMMException(_(u'The domain name is too long.'),
                ERR.DOMAIN_TOO_LONG)
        re.compile(RE_DOMAIN)
        if not re.match(RE_DOMAIN, domainname):
            raise VMMException(_(u'The domain name is invalid.'),
                ERR.DOMAIN_INVALID)
        return domainname
    chkDomainname = staticmethod(chkDomainname)

    def chkEmailAddress(address):
        try:
            localpart, domain = address.split('@')
        except ValueError:
            raise VMMException(_(u"Missing '@' sign in e-mail address »%s«.") %
                address, ERR.INVALID_ADDRESS)
        except AttributeError:
            raise VMMException(_(u"»%s« looks not like an e-mail address.") %
                address, ERR.INVALID_ADDRESS)
        domain = VirtualMailManager.chkDomainname(domain)
        localpart = VirtualMailManager.chkLocalpart(localpart)
        return '%s@%s' % (localpart, domain)
    chkEmailAddress = staticmethod(chkEmailAddress)

    def __getAccount(self, address, password=None):
        self.__dbConnect()
        if not password is None:
            password = self.__pwhash(password)
        return Account(self.__dbh, address, password)

    def _readpass(self):
        clear0 = ''
        clear1 = '1'
        while clear0 != clear1:
            while len(clear0) < 1:
                clear0 = getpass(prompt=_('Enter new password: '))
                if len(clear0) < 1:
                    sys.stderr.write('%s\n'
                            % _('Sorry, empty passwords are not permitted'))
            clear1 = getpass(prompt=_('Retype new password: '))
            if clear0 != clear1:
                clear0 = ''
                sys.stderr.write('%s\n' % _('Sorry, passwords do not match'))
        return clear0

    def __getAlias(self, address, destination=None):
        address = VirtualMailManager.chkEmailAddress(address)
        if not destination is None:
            if destination.count('@'):
                destination = VirtualMailManager.chkEmailAddress(destination)
            else:
                destination = VirtualMailManager.chkLocalpart(destination)
        self.__dbConnect()
        return Alias(self.__dbh, address, destination)

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

    def __domdirmake(self, domdir, gid):
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

    def __maildirmake(self, domdir, uid, gid):
        """Creates maildirs and maildir subfolders.

        Keyword arguments:
        uid -- user id from the account
        gid -- group id from the account
        """
        os.umask(0007)
        oldpwd = os.getcwd()
        os.chdir(domdir)

        maildir = '%s' % self.__Cfg.get('maildir', 'folder')
        folders = [maildir , maildir+'/.Drafts', maildir+'/.Sent',
                maildir+'/.Templates', maildir+'/.Trash']
        subdirs = ['cur', 'new', 'tmp']
        mode = self.__Cfg.getint('maildir', 'mode')

        self.__makedir('%s' % uid, mode, uid, gid)
        os.chdir('%s' % uid)
        for folder in folders:
            self.__makedir(folder, mode, uid, gid)
            for subdir in subdirs:
                self.__makedir(folder+'/'+subdir, mode, uid, gid)
        os.chdir(oldpwd)

    def __userdirdelete(self, domdir, uid, gid):
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
                         _(u'Owner/group mismatch in home directory detected.'),
                         ERR.MAILDIR_PERM_MISMATCH)
                    rmtree(userdir, ignore_errors=True)
                else:
                    raise VMMException(_(u"No such directory: %s") %
                        domdir+'/'+userdir, ERR.NO_SUCH_DIRECTORY)

    def __domdirdelete(self, domdir, gid):
        if gid > 0:
            if not self.__isdir(domdir):
                return
            basedir = '%s' % self.__Cfg.get('domdir', 'base')
            domdirdirs = domdir.replace(basedir+'/', '').split('/')
            if basedir.count('..') or domdir.count('..'):
                raise VMMException(
                        _(u'FATAL: ".." in domain directory path detected.'),
                            ERR.FOUND_DOTS_IN_PATH)
            if os.path.isdir('%s/%s' % (basedir, domdirdirs[0])):
                os.chdir('%s/%s' % (basedir, domdirdirs[0]))
                if os.lstat(domdirdirs[1]).st_gid != gid:
                    raise VMMException(
                    _(u'FATAL: group mismatch in domain directory detected'),
                        ERR.DOMAINDIR_GROUP_MISMATCH)
                rmtree(domdirdirs[1], ignore_errors=True)

    def __getSalt(self):
        from random import choice
        salt = None
        if self.__scheme == 'CRYPT':
            salt = '%s%s' % (choice(SALTCHARS), choice(SALTCHARS))
        elif self.__scheme in ['MD5', 'MD5-CRYPT']:
            salt = '$1$'
            for i in range(8):
                salt += choice(SALTCHARS)
            salt += '$'
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
            _md5 = md5.new('%s:%s:' % tuple(emailaddress.split('@')))
            _md5.update(password)
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
        elif self.__scheme == 'MD4':
            return '{%s}%s' % (self.__scheme, self.__pwMD4(password))
        elif self.__scheme in ['SMD5', 'SSHA', 'CRAM-MD5', 'HMAC-MD5',
                'LANMAN', 'NTLM', 'RPA']:
            return Popen([self.__Cfg.get('bin', 'dovecotpw'), '-s',
                self.__scheme,'-p',password],stdout=PIPE).communicate()[0][:-1]
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
            raise VMMConfigException(_(u"""Configurtion error: "%s"
(in section "connfig", option "done") see also: vmm.cfg(5)\n""") % str(e),
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
            raise VMMException(_(u"Invalid section: '%s'") % section,
                ERR.INVALID_SECTION)

    def domain_add(self, domainname, transport=None):
        dom = self.__getDomain(domainname, transport)
        dom.save()
        self.__domdirmake(dom.getDir(), dom.getID())

    def domain_transport(self, domainname, transport, force=None):
        if force is not None and force != 'force':
            raise VMMDomainException(_(u"Invalid argument: '%s'") % force,
                ERR.INVALID_OPTION)
        dom = self.__getDomain(domainname, None)
        if force is None:
            dom.updateTransport(transport)
        else:
            dom.updateTransport(transport, force=True)

    def domain_delete(self, domainname, force=None):
        if not force is None and force not in ['deluser','delalias','delall']:
            raise VMMDomainException(_(u"Invalid argument: »%s«") % force,
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
            self.__domdirdelete(domdir, gid)

    def domain_info(self, domainname, detailed=None):
        dom = self.__getDomain(domainname)
        dominfo = dom.getInfo()
        if dominfo['domainname'].startswith('xn--'):
            dominfo['domainname'] += ' (%s)'\
                % VirtualMailManager.ace2idna(dominfo['domainname'])
        if dominfo['aliases'] is None:
            dominfo['aliases'] = 0
        if detailed is None:
            return dominfo
        elif detailed == 'detailed':
            return (dominfo, dom.getAliaseNames(), dom.getAccounts(),
                    dom.getAliases())
        else:
            raise VMMDomainException(_(u'Invalid argument: »%s«') % detailed,
                ERR.INVALID_OPTION)

    def domain_alias_add(self, aliasname, domainname):
        """Adds an alias name to the domain.
        
        Keyword arguments:
        aliasname -- the alias name of the domain (str)
        domainname -- name of the target domain (str)
        """
        dom = self.__getDomain(domainname)
        dom.saveAlias(aliasname)

    def domain_alias_delete(self, aliasname):
        """Deletes the specified alias name.
        
        Keyword arguments:
        aliasname -- the alias name of the domain (str)
        """
        from Domain import deleteAlias
        self.__dbConnect()
        deleteAlias(self.__dbh, aliasname)

    def domain_list(self, pattern=None):
        from Domain import search
        like = False
        if pattern is not None:
            if pattern.startswith('%') or pattern.endswith('%'):
                like = True
                if pattern.startswith('%') and pattern.endswith('%'):
                    domain = pattern[1:-1]
                elif pattern.startswith('%'):
                    domain = pattern[1:]
                elif pattern.endswith('%'):
                    domain = pattern[:-1]
                re.compile(RE_DOMAIN_SRCH)
                if not re.match(RE_DOMAIN_SRCH, domain):
                    raise VMMException(
                    _(u"The pattern »%s« contains invalid characters.") %
                    pattern, ERR.DOMAIN_INVALID)
        self.__dbConnect()
        return search(self.__dbh, pattern=pattern, like=like)

    def user_add(self, emailaddress, password):
        acc = self.__getAccount(emailaddress, password)
        if password is None:
            password = self._readpass()
            acc.setPassword(self.__pwhash(password))
        acc.save(self.__Cfg.get('maildir', 'folder'),
                self.__Cfg.getboolean('services', 'smtp'),
                self.__Cfg.getboolean('services', 'pop3'),
                self.__Cfg.getboolean('services', 'imap'),
                self.__Cfg.getboolean('services', 'managesieve'))
        self.__maildirmake(acc.getDir('domain'), acc.getUID(), acc.getGID())

    def alias_add(self, aliasaddress, targetaddress):
        alias = self.__getAlias(aliasaddress, targetaddress)
        alias.save()

    def user_delete(self, emailaddress):
        acc = self.__getAccount(emailaddress)
        uid = acc.getUID()
        gid = acc.getGID()
        acc.delete()
        if self.__Cfg.getboolean('maildir', 'delete'):
            try:
                self.__userdirdelete(acc.getDir('domain'), uid, gid)
            except VMMException, e:
                if e.code() in [ERR.FOUND_DOTS_IN_PATH,
                        ERR.MAILDIR_PERM_MISMATCH, ERR.NO_SUCH_DIRECTORY]:
                    warning = _(u"""\
The account has been successfully deleted from the database.
    But an error occurred while deleting the following directory:
    »%(directory)s«
    Reason: %(raeson)s""") % {'directory': acc.getDir('home'),'raeson': e.msg()}
                    self.__warnings.append(warning)
                else:
                    raise e

    def alias_info(self, aliasaddress):
        alias = self.__getAlias(aliasaddress)
        return alias.getInfo()

    def alias_delete(self, aliasaddress, targetaddress=None):
        alias = self.__getAlias(aliasaddress, targetaddress)
        alias.delete()

    def user_info(self, emailaddress, diskusage=False):
        acc = self.__getAccount(emailaddress)
        info = acc.getInfo()
        if self.__Cfg.getboolean('maildir', 'diskusage') or diskusage:
            info['disk usage'] = self.__getDiskUsage('%(maildir)s' % info)
        return info

    def user_byID(self, uid):
        from Account import getAccountByID
        self.__dbConnect()
        return getAccountByID(uid, self.__dbh)

    def user_password(self, emailaddress, password):
        acc = self.__getAccount(emailaddress)
        if acc.getUID() == 0:
           raise VMMException(_(u"Account doesn't exists"),
               ERR.NO_SUCH_ACCOUNT)
        if password is None:
            password = self._readpass()
        acc.modify('password', self.__pwhash(password))

    def user_name(self, emailaddress, name):
        acc = self.__getAccount(emailaddress)
        acc.modify('name', name)

    def user_transport(self, emailaddress, transport):
        acc = self.__getAccount(emailaddress)
        acc.modify('transport', transport)

    def user_disable(self, emailaddress, service=None):
        acc = self.__getAccount(emailaddress)
        acc.disable(service)

    def user_enable(self, emailaddress, service=None):
        acc = self.__getAccount(emailaddress)
        acc.enable(service)

    def __del__(self):
        if not self.__dbh is None and self.__dbh._isOpen:
            self.__dbh.close()
