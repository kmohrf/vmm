# -*- coding: UTF-8 -*-
# Copyright (c) 2007 - 2010, Pascal Volk
# See COPYING for distribution information.

"""Configuration class for read, modify and write the
configuration from Virtual Mail Manager.

"""

from shutil import copy2
from ConfigParser import ConfigParser, MissingSectionHeaderError, ParsingError
from cStringIO import StringIO

from __main__ import ENCODING, ERR, w_std
from Exceptions import VMMConfigException

class Config(ConfigParser):
    """This class is for reading and modifying vmm's configuration file."""

    def __init__(self, filename):
        """Creates a new Config instance

        Arguments:
        filename -- path to the configuration file
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
                ['name', 'Maildir'],
                ['folders', 'Drafts:Sent:Templates:Trash'],
                ['mode', 448],
                ['diskusage', 'false'],
                ['delete', 'false']
                ]
        self.__serviceopts = [
                ['smtp', 'true'],
                ['pop3', 'true'],
                ['imap', 'true'],
                ['sieve', 'true']
                ]
        self.__domdopts = [
                ['base', '/srv/mail'],
                ['mode', 504],
                ['delete', 'false']
                ]
        self.__binopts = [
                ['dovecotpw', '/usr/sbin/dovecotpw'],
                ['du', '/usr/bin/du'],
                ['postconf', '/usr/sbin/postconf']
                ]
        self.__miscopts = [
                ['passwdscheme', 'PLAIN'],
                ['gid_mail', 8],
                ['forcedel', 'false'],
                ['transport', 'dovecot:'],
                ['dovecotvers', '11']
                ]

    def load(self):
        """Loads the configuration, read only.

        Raises a VMMConfigException if the configuration syntax is invalid.
        """
        try:
            self.__cfgFile = file(self.__cfgFileName, 'r')
            self.readfp(self.__cfgFile)
        except (MissingSectionHeaderError, ParsingError), e:
            self.__cfgFile.close()
            raise VMMConfigException(str(e), ERR.CONF_ERROR)
        self.__cfgFile.close()

    def check(self):
        """Performs a configuration check.

        Raises a VMMConfigException if the check fails.
        """
        if not self.__chkSections():
            errmsg = StringIO()
            errmsg.write(_("Using configuration file: %s\n") %\
                    self.__cfgFileName)
            for k,v in self.__missing.items():
                if v[0] is True:
                    errmsg.write(_(u"missing section: %s\n") % k)
                else:
                    errmsg.write(_(u"missing options in section %s:\n") % k)
                    for o in v:
                        errmsg.write(" * %s\n" % o)
            raise VMMConfigException(errmsg.getvalue(), ERR.CONF_ERROR)

    def getsections(self):
        """Return a list with all configurable sections."""
        return self.__VMMsections[:-1]

    def get(self, section, option, raw=False, vars=None):
        return unicode(ConfigParser.get(self, section, option, raw, vars),
                ENCODING, 'replace')

    def configure(self, sections):
        """Interactive method for configuring all options in the given sections

        Arguments:
        sections -- list of strings with section names
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
        w_std(_(u'Using configuration file: %s\n') % self.__cfgFileName)
        for s in sections:
            if s != 'config':
                w_std(_(u'* Config section: “%s”') % s )
            for opt, val in self.items(s):
                newval = raw_input(
                _('Enter new value for option %(opt)s [%(val)s]: ').encode(
                    ENCODING, 'replace') % {'opt': opt, 'val': val})
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

        Arguments:
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
