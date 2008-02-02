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
from shutil import rmtree
from subprocess import Popen, PIPE

from pyPgSQL import PgSQL # python-pgsql - http://pypgsql.sourceforge.net

from Exceptions import *
import constants.ERROR as ERR
from Config import VMMConfig as Cfg
from Account import Account
from Alias import Alias
from Domain import Domain

RE_ASCII_CHARS = """^[\x20-\x7E]*$"""
RE_DOMAIN = """^(?:[a-z0-9-]{1,63}\.){1,}[a-z]{2,6}$"""
RE_LOCALPART = """[^\w!#$%&'\*\+-\.\/=?^_`{\|}~]"""
RE_MAILLOCATION = """^[\w]{1,20}$"""
re.compile(RE_ASCII_CHARS)
re.compile(RE_DOMAIN)

ENCODING_IN = sys.getfilesystemencoding()
ENCODING_OUT = sys.stdout.encoding or sys.getfilesystemencoding()

class VirtualMailManager:
    """The main class for vmm"""
    def __init__(self):
        """Creates a new VirtualMailManager instance.
        Throws a VMMNotRootException if your uid is greater 0.
        """
        self.__cfgFileName = '/usr/local/etc/vmm.cfg'
        self.__permWarnMsg = "fix permissions for '%s'\n`chmod 0600 %s` would\
 be great." % (self.__cfgFileName, self.__cfgFileName)
        self.__warnings = []
        self.__Cfg = None
        self.__dbh = None

        if os.geteuid():
            raise VMMNotRootException(("You are not root.\n\tGood bye!\n",
                ERR.CONF_NOPERM))
        if self.__chkCfgFile():
            self.__Cfg = Cfg(self.__cfgFileName)
            self.__Cfg.load()
            self.__Cfg.check()
            self.__cfgSections = self.__Cfg.getsections()
        self.__chkenv()

    def __chkCfgFile(self):
        """Checks the configuration file, returns bool"""
        if not os.path.isfile(self.__cfgFileName):
            raise VMMException(("The file »%s« does not exists." %
                self.__cfgFileName, ERR.CONF_NOFILE))
        fstat = os.stat(self.__cfgFileName)
        try:
            fmode = self.__getFileMode()
        except:
            raise
        if fmode % 100 and fstat.st_uid != fstat.st_gid \
        or fmode % 10 and fstat.st_uid == fstat.st_gid:
            raise VMMPermException((self.__permWarnMsg, ERR.CONF_ERROR))
        else:
            return True

    def __chkenv(self):
        """"""
        if not os.path.exists(self.__Cfg.get('maildir', 'base')):
            old_umask = os.umask(0007)
            os.makedirs(self.__Cfg.get('maildir', 'base'), 0770)
            os.umask(old_umask)
        elif not os.path.isdir(self.__Cfg.get('maildir', 'base')):
            raise VMMException(('%s is not a directory' %
                self.__Cfg.get('maildir', 'base'), ERR.NO_SUCH_DIRECTORY))
        for opt, val in self.__Cfg.items('bin'):
            if not os.path.exists(val):
                raise VMMException(("%s doesn't exists.", ERR.NO_SUCH_BINARY))
            elif not os.access(val, os.X_OK):
                raise VMMException(("%s is not executable.", ERR.NOT_EXECUTABLE))

    def __getFileMode(self):
        """Determines the file access mode from file __cfgFileName,
        returns int.
        """
        try:
            return int(oct(os.stat(self.__cfgFileName).st_mode & 0777))
        except:
            raise

    def __dbConnect(self):
        """Creates a pyPgSQL.PgSQL.connection instance."""
        try:
            self.__dbh =  PgSQL.connect(
                    database=self.__Cfg.get('database', 'name'),
                    user=self.__Cfg.get('database', 'user'),
                    host=self.__Cfg.get('database', 'host'),
                    password=self.__Cfg.get('database', 'pass'),
                    client_encoding='utf8', unicode_results=True)
            dbc = self.__dbh.cursor()
            dbc.execute("SET NAMES 'UTF8'")
            dbc.close()
        except PgSQL.libpq.DatabaseError, e:
            raise VMMException((str(e), ERR.DATABASE_ERROR))

    def __chkLocalpart(self, localpart):
        """Validates the local part of an e-mail address.
        
        Keyword arguments:
        localpart -- the e-mail address that should be validated (str)
        """
        if len(localpart) > 64:
            raise VMMException(('The local part is too long',
                ERR.LOCALPART_TOO_LONG))
        if re.compile(RE_LOCALPART).search(localpart):
            raise VMMException((
                'The local part »%s« contains invalid characters.' % localpart,
                ERR.LOCALPART_INVALID))
        return localpart

    def __idn2ascii(self, domainname):
        """Converts an idn domainname in punycode.
        
        Keyword arguments:
        domainname -- the domainname to convert (str)
        """
        tmp = []
        for label in domainname.split('.'):
            if len(label) == 0:
                continue
            tmp.append(ToASCII(unicode(label, ENCODING_IN)))
        return '.'.join(tmp)

    def __ace2idna(self, domainname):
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

    def __chkDomainname(self, domainname):
        """Validates the domain name of an e-mail address.
        
        Keyword arguments:
        domainname -- the domain name that should be validated
        """
        if not re.match(RE_ASCII_CHARS, domainname):
            domainname = self.__idn2ascii(domainname)
        if len(domainname) > 255:
            raise VMMException(('The domain name is too long.',
                ERR.DOMAIN_TOO_LONG))
        if not re.match(RE_DOMAIN, domainname):
            raise VMMException(('The domain name is invalid.',
                ERR.DOMAIN_INVALID))
        return domainname

    def __chkEmailAddress(self, address):
        try:
            localpart, domain = address.split('@')
        except ValueError:
            raise VMMException(("Missing '@' sign in e-mail address »%s«." %
                address, ERR.INVALID_ADDRESS))
        except AttributeError:
            raise VMMException(("»%s« looks not like an e-mail address." %
                address, ERR.INVALID_ADDRESS))
        domain = self.__chkDomainname(domain)
        localpart = self.__chkLocalpart(localpart)
        return '%s@%s' % (localpart, domain)

    def __getAccount(self, address, password=None):
        address = self.__chkEmailAddress(address)
        self.__dbConnect()
        if not password is None:
            password = self.__pwhash(password)
        return Account(self.__dbh, self.__Cfg.get('maildir', 'base'), address,
                password)

    def __getAlias(self, address, destination=None):
        address = self.__chkEmailAddress(address)
        if not destination is None:
            if destination.count('@'):
                destination = self.__chkEmailAddress(destination)
            else:
                destination = self.__chkLocalpart(destination)
        self.__dbConnect()
        return Alias(self.__dbh, address, self.__Cfg.get('maildir', 'base'),
                destination)

    def __getDomain(self, domainname, transport=None):
        domainname = self.__chkDomainname(domainname)
        self.__dbConnect()
        return Domain(self.__dbh, domainname,
                self.__Cfg.get('maildir', 'base'), transport)

    def __getDiskUsage(self, directory):
        """Estimate file space usage for the given directory.
        
        Keyword arguments:
        directory -- the directory to summarize recursively disk usage for
        """
        return Popen([self.__Cfg.get('bin', 'du'), "-hs", directory],
                stdout=PIPE).communicate()[0].split('\t')[0]

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
        basedir = self.__Cfg.get('maildir', 'base')
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

    def __maildirdelete(self, domdir, uid, gid):
        if uid > 0 and gid > 0:
            maildir = '%s' % uid
            if maildir.count('..') or domdir.count('..'):
                raise VMMException(('FATAL: ".." in maildir path detected.',
                    ERR.FOUND_DOTS_IN_PATH))
            if os.path.isdir(domdir):
                os.chdir(domdir)
                if os.path.isdir(maildir):
                    mdstat = os.stat(maildir)
                    if (mdstat.st_uid, mdstat.st_gid) != (uid, gid):
                        raise VMMException(
                            ('FATAL: owner/group mismatch in maildir detected',
                                ERR.MAILDIR_PERM_MISMATCH))
                    rmtree(maildir, ignore_errors=True)

    def __domdirdelete(self, domdir, gid):
        if gid > 0:
            basedir = '%s' % self.__Cfg.get('maildir', 'base')
            domdirdirs = domdir.replace(basedir+'/', '').split('/')
            if basedir.count('..') or domdir.count('..'):
                raise VMMException(
                        ('FATAL: ".." in domain directory path detected.',
                            ERR.FOUND_DOTS_IN_PATH))
            if os.path.isdir('%s/%s' % (basedir, domdirdirs[0])):
                os.chdir('%s/%s' % (basedir, domdirdirs[0]))
                if os.lstat(domdirdirs[1]).st_gid != gid:
                    raise VMMException(
                    ('FATAL: group mismatch in domain directory detected',
                        ERR.DOMAINDIR_GROUP_MISMATCH))
                rmtree(domdirdirs[1], ignore_errors=True)

    def __pwhash(self, password, scheme=None, user=None):
        # XXX alle Schemen berücksichtigen XXX
        if scheme is None:
            scheme = self.__Cfg.get('misc', 'passwdscheme')
        return Popen([self.__Cfg.get('bin', 'dovecotpw'), '-s', scheme, '-p',
            password], stdout=PIPE).communicate()[0][len(scheme)+2:-1]

    def hasWarnings(self):
        """Checks if warnings are present, returns bool."""
        return bool(len(self.__warnings))

    def getWarnings(self):
        """Returns a list with all available warnings."""
        return self.__warnings

    def setupIsDone(self):
        """Checks if vmm is configured, returns bool"""
        try:
            return self.__Cfg.getboolean('config', 'done')
        except ValueError, e:
            raise VMMConfigException('Configurtion error: "'+str(e)
                +'"\n(in section "Connfig", option "done")'
                +'\nsee also: vmm.cfg(5)\n')

    def configure(self, section=None):
        """Starts interactive configuration.

        Configures in interactive mode options in the given section.
        If no section is given (default) all options from all sections
        will be prompted.

        Keyword arguments:
        section -- the section to configure (default None):
            'database', 'maildir', 'bin' or 'misc'
        """
        try:
            if not section:
                self.__Cfg.configure(self.__cfgSections)
            elif section not in self.__cfgSections:
                raise VMMException(("Invalid section: »%s«" % section,
                    ERR.INVALID_SECTION))
            else:
                self.__Cfg.configure([section])
        except:
            raise

    def domain_add(self, domainname, transport=None):
        dom = self.__getDomain(domainname, transport)
        dom.save()
        self.__domdirmake(dom.getDir(), dom.getID())

    def domain_transport(self, domainname, transport):
        dom = self.__getDomain(domainname, None)
        dom.updateTransport(transport)

    def domain_delete(self, domainname, force=None):
        if not force is None and force not in ['deluser','delalias','delall']:
            raise VMMDomainException(('Invalid argument: «%s»' % force,
                ERR.INVALID_OPTION))
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
                % self.__ace2idna(dominfo['domainname'])
        if dominfo['aliases'] is None:
            dominfo['aliases'] = 0
        if detailed is None:
            return dominfo
        elif detailed == 'detailed':
            return dominfo, dom.getAccounts(), dom.getAliases()
        else:
            raise VMMDomainException(('Invalid argument: »%s«' % detailed,
                ERR.INVALID_OPTION))

    def user_add(self, emailaddress, password):
        acc = self.__getAccount(emailaddress, password)
        acc.save(self.__Cfg.get('maildir', 'folder'))
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
            self.__maildirdelete(acc.getDir('domain'), uid, gid)

    def alias_info(self, aliasaddress):
        alias = self.__getAlias(aliasaddress)
        return alias.getInfo()

    def alias_delete(self, aliasaddress):
        alias = self.__getAlias(aliasaddress)
        alias.delete()

    def user_info(self, emailaddress, diskusage=False):
        acc = self.__getAccount(emailaddress)
        info = acc.getInfo()
        if self.__Cfg.getboolean('maildir', 'diskusage') or diskusage:
            info['disk usage'] = self.__getDiskUsage('%(home)s/%(mail)s' % info)
        return info

    def user_password(self, emailaddress, password):
        acc = self.__getAccount(emailaddress)
        acc.modify('password', self.__pwhash(password))

    def user_name(self, emailaddress, name):
        acc = self.__getAccount(emailaddress)
        acc.modify('name', name)

    def user_disable(self, emailaddress):
        acc = self.__getAccount(emailaddress)
        acc.disable()

    def user_enable(self, emailaddress):
        acc = self.__getAccount(emailaddress)
        acc.enable()

    def __del__(self):
        if not self.__dbh is None and self.__dbh._isOpen:
            self.__dbh.close()
