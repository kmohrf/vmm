# -*- coding: UTF-8 -*-
# Copyright 2008 VEB IT
# See COPYING for distribution information.
# $Id$

"""A small - r/o - wrapper class for Postfix' postconf."""

from VirtualMailManager.constants.VERSION import VERSION

__author__ = 'Pascal Volk <p.volk@veb-it.de>'
__version__ = VERSION
__revision__ = 'rev '+'$Rev$'.split()[1]
__date__ = '$Date$'.split()[1]

import re
from subprocess import Popen, PIPE

import VirtualMailManager.constants.ERROR as ERR
from VirtualMailManager.Exceptions import VMMException

RE_PC_PARAMS = """^\w+$"""
RE_PC_VARIABLES = r"""\$\b\w+\b"""

class Postconf:
    def __init__(self, postconf_bin):
        """Creates a new Postconf instance.
        
        Keyword arguments:
        postconf_bin -- absolute path to Postfix' postconf binary (str)
        """
        self.__bin = postconf_bin
        self.__val = ''
        self.__varFinder = re.compile(RE_PC_VARIABLES)

    def read(self, parameter, expand_vars=True):
        """Returns the parameters value.

        If expand_vars is True (default), all variables in the value will be 
        expanded:
        e.g. mydestination -> mail.example.com, localhost.example.com, localhost
        Otherwise the value may contain one or more variables.
        e.g. mydestination -> $myhostname, localhost.$mydomain, localhost

        Keyword arguments:
        parameter -- the name of a Postfix configuration parameter (str)
        expand_vars -- default True (bool)
        """
        if not re.match(RE_PC_PARAMS, parameter):
            raise VMMException(_(u'The value »%s« looks not like a valid\
 postfix configuration parameter name.') % parameter, ERR.INVALID_AGUMENT)
        self.__val = self.__read(parameter)
        if expand_vars:
            self.__expandVars()
        return self.__val

    def __expandVars(self):
        while True:
            pvars = set(self.__varFinder.findall(self.__val))
            pvars_len = len(pvars)
            if pvars_len < 1:
                break
            if pvars_len > 1:
                self.__expandMultiVars(self.__readMulti(pvars))
                continue
            pvars = pvars.pop()
            self.__val = self.__val.replace(pvars, self.__read(pvars[1:]))

    def __expandMultiVars(self, old_new):
        for old, new in old_new.items():
            self.__val = self.__val.replace('$'+old, new)

    def __read(self, parameter):
        out, err = Popen([self.__bin, '-h', parameter], stdout=PIPE,
                stderr=PIPE).communicate()
        if len(err):
            raise Exception, err.strip()
        return out.strip()

    def __readMulti(self, parameters):
        cmd = [self.__bin]
        for parameter in parameters:
            cmd.append(parameter[1:])
        out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        if len(err):
            raise Exception, err.strip()
        par_val = {}
        for line in out.splitlines():
            par, val = line.split(' = ')
            par_val[par] = val
        return par_val

