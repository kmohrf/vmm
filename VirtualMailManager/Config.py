#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2007-2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""Configurtion class for read, modify and write the
configuration from Virtual Mail Manager.

"""

from constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

import sys
from shutil import copy2
from ConfigParser import ConfigParser
from cStringIO import StringIO

from Exceptions import VMMConfigException
import constants.ERROR as ERR

class VMMConfig(ConfigParser):
    """This class is for configure the Virtual Mail Manager.

    You can specify settings for the database connection
    and maildirectories.

    """

    def __init__(self, filename):
        """Creates a new VMMConfig instance

        Keyword arguments:
        filename -- name of the configuration file
        """
        ConfigParser.__init__(self)
        self.__cfgFileName = filename
        self.__cfgFile = None
        self.__VMMsections = ['database', 'maildir', 'services', 'domdir',
                'bin', 'misc', 'config']
        self.__changes = False
        self.__missing = {}
        self.__dbopts = [
                ['host', 'localhot'],
                ['user', 'vmm'],
                ['pass', 'your secret password'],
                ['name', 'mailsys']
                ]
        self.__mdopts = [
                ['base', '/home/mail'],
                ['folder', 'Maildir'],
                ['mode', 448],
                ['diskusage', 'false'],
                ['delete', 'false']
                ]
        self.__serviceopts = [
                ['smtp', 'true'],
                ['pop3', 'true'],
                ['imap', 'true'],
                ['managesieve', 'true']
                ]
        self.__domdopts = [
                ['mode', 504],
                ['delete', 'false']
                ]
        self.__binopts = [
                ['dovecotpw', '/usr/sbin/dovecotpw'],
                ['du', '/usr/bin/du']
                ]
        self.__miscopts = [
                ['passwdscheme', 'CRAM-MD5'],
                ['gid_mail', 8],
                ['forcedel', 'false'],
                ['transport', 'dovecot:']
                ]

    def load(self):
        """Loads the configuration, r/o"""
        try:
            self.__cfgFile = file(self.__cfgFileName, 'r')
        except:
            raise
        self.readfp(self.__cfgFile)
        self.__cfgFile.close()

    def check(self):
        if not self.__chkSections():
            errmsg = StringIO()
            for k,v in self.__missing.items():
                if v[0] is True:
                    errmsg.write("missing section: %s\n" % k)
                else:
                    errmsg.write("missing options in section %s:\n" % k)
                    for o in v:
                        errmsg.write(" * %s\n" % o)
            raise VMMConfigException((errmsg.getvalue(), ERR.CONF_ERROR))

    def getsections(self):
        """Return a list with all configurable sections."""
        return self.__VMMsections[:-1]

    def configure(self, sections):
        """Interactive method for configuring all options in the given section

        Keyword arguments:
        sections -- list of strings
        """
        if not isinstance(sections, list):
            raise TypeError("Argument 'sections' is not a list.")
        # if [config] done = false (default at 1st run),
        # then set changes true
        try:
            if not self.getboolean('config', 'done'):
                self.__changes = True
        except ValueError:
            self.set('config', 'done', 'False')
            self.__changes = True
        for s in sections:
            if s == 'config':
                pass
            else:
                print '* Config section: %s' % s
            for opt, val in self.items(s):
                newval = raw_input('Enter new value for %s [%s]: ' %(opt, val))
                if newval and newval != val:
                    self.set(s, opt, newval)
                    self.__changes = True
            print
        if self.__changes:
            self.__saveChanges()

    def __saveChanges(self):
        """Writes changes to the configuration file."""
        self.set('config', 'done', 'true')
        copy2(self.__cfgFileName, self.__cfgFileName+'.bak')
        self.__cfgFile = file(self.__cfgFileName, 'w')
        self.write(self.__cfgFile)
        self.__cfgFile.close()

    def __chkSections(self):
        """Checks if all configuration sections are existing."""
        errors = False
        for s in self.__VMMsections:
            if not self.has_section(s):
                self.__missing[s] = [True]
            elif not self.__chkOptions(s):
                errors = True
        return not errors

    def __chkOptions(self, section):
        """Checks if all configuration options in section are existing.

        Keyword arguments:
        section -- the section to be checked
        """
        retval = True
        missing = []
        if section == 'database':
            opts = self.__dbopts
        elif section == 'maildir':
            opts = self.__mdopts
        elif section == 'services':
            opts = self.__serviceopts
        elif section == 'domdir':
            opts = self.__domdopts
        elif section == 'bin':
            opts = self.__binopts
        elif section == 'misc':
            opts = self.__miscopts
        elif section == 'config':
            opts = [['done', 'false']]
        for o, v in opts:
            if not self.has_option(section, o):
                missing.append(o)
                retval = False
        if len(missing):
            self.__missing[section] = missing
        return retval
