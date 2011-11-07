# -*- coding: UTF-8 -*-
# Copyright (c) 2008 - 2011, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.ext.postconf
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Wrapper class for Postfix's postconf.
    Postconf instances can be used to read actual values of configuration
    parameters or edit the value of a configuration parameter.

    postconf.read(parameter) -> value
    postconf.edit(parameter, value)
"""

import re
from subprocess import Popen, PIPE

from VirtualMailManager.errors import VMMError
from VirtualMailManager.constants import VMM_ERROR

_ = lambda msg: msg


class Postconf(object):
    """Wrapper class for Postfix's postconf."""
    __slots__ = ('_bin', '_val')
    _parameter_re = re.compile(r'^\w+$')
    _variables_re = re.compile(r'\$\b\w+\b')

    def __init__(self, postconf_bin):
        """Creates a new Postconf instance.

        Argument:

        `postconf_bin` : str
          absolute path to the Postfix postconf binary.
        """
        self._bin = postconf_bin
        self._val = ''

    def edit(self, parameter, value):
        """Set the `parameter`'s value to `value`.

        Arguments:

        `parameter` : str
          the name of a Postfix configuration parameter
        `value` : str
          the parameter's new value.
        """
        self._check_parameter(parameter)
        stderr = Popen((self._bin, '-e', parameter + '=' + str(value)),
                       stderr=PIPE).communicate()[1]
        if stderr:
            raise VMMError(stderr.strip(), VMM_ERROR)

    def read(self, parameter, expand_vars=True):
        """Returns the parameters value.

        If expand_vars is True (default), all variables in the value will be
        expanded:
        e.g. mydestination: mail.example.com, localhost.example.com, localhost
        Otherwise the value may contain one or more variables.
        e.g. mydestination: $myhostname, localhost.$mydomain, localhost

        Arguments:

        `parameter` : str
          the name of a Postfix configuration parameter.
        `expand_vars` : bool
          indicates if variables should be expanded or not, default True
        """
        self._check_parameter(parameter)
        self._val = self._read(parameter)
        if expand_vars:
            self._expand_vars()
        return self._val

    def _check_parameter(self, parameter):
        """Check that the `parameter` looks like a configuration parameter.
        If not, a VMMError will be raised."""
        if not self.__class__._parameter_re.match(parameter):
            raise VMMError(_(u"The value '%s' does not look like a valid "
                             u"postfix configuration parameter name.") %
                           parameter, VMM_ERROR)

    def _expand_vars(self):
        """Expand the $variables in self._val to their values."""
        while True:
            pvars = set(self.__class__._variables_re.findall(self._val))
            if not pvars:
                break
            if len(pvars) > 1:
                self._expand_multi_vars(self._read_multi(pvars))
                continue
            pvars = pvars.pop()
            self._val = self._val.replace(pvars, self._read(pvars[1:]))

    def _expand_multi_vars(self, old_new):
        """Replace all $vars in self._val with their values."""
        for old, new in old_new.iteritems():
            self._val = self._val.replace('$' + old, new)

    def _read(self, parameter):
        """Ask postconf for the value of a single configuration parameter."""
        stdout, stderr = Popen([self._bin, '-h', parameter], stdout=PIPE,
                               stderr=PIPE).communicate()
        if stderr:
            raise VMMError(stderr.strip(), VMM_ERROR)
        return stdout.strip()

    def _read_multi(self, parameters):
        """Ask postconf for multiple configuration parameters. Returns a dict
        parameter: value items."""
        cmd = [self._bin]
        cmd.extend(parameter[1:] for parameter in parameters)
        stdout, stderr = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        if stderr:
            raise VMMError(stderr.strip(), VMM_ERROR)
        par_val = {}
        for line in stdout.splitlines():
            par, val = line.split(' = ')
            par_val[par] = val
        return par_val

del _
