# -*- coding: UTF-8 -*-
# Copyright (c) 2011 - 2012, Pascal Volk
# See COPYING for distribution information.
"""
    VirtualMailManager.network
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Network/IP address related class and function
"""

import socket


class NetInfo(object):
    """Simple class for CIDR network addresses an IP addresses."""
    __slots__ = ('_addr', '_prefix', '_bits_max', '_family', '_nw_addr')

    def __init__(self, nw_address):
        """Creates a new `NetInfo` instance.

        Argument:

        `nw_address` : basestring
          string representation of an IPv4/IPv6 address or network address.
          E.g. 192.0.2.13, 192.0.2.0/24, 2001:db8::/32 or ::1
          When the address has no netmask the prefix length will be set to
          32 for IPv4 addresses and 128 for IPv6 addresses.
        """
        self._addr = None
        self._prefix = 0
        self._bits_max = 0
        self._family = 0
        self._nw_addr = nw_address
        self._parse_net_range()

    def __hash__(self):
        return hash((self._addr, self._family, self._prefix))

    def __repr__(self):
        return "NetInfo('%s')" % self._nw_addr

    def _parse_net_range(self):
        """Parse the network range of `self._nw_addr and assign values
        to the class attributes.
        `"""
        sep = '/'
        if self._nw_addr.count(sep):
            ip_address, sep, self._prefix = self._nw_addr.partition(sep)
            self._family, self._addr = get_ip_addr_info(ip_address)
        else:
            self._family, self._addr = get_ip_addr_info(self._nw_addr)
        self._bits_max = (128, 32)[self._family is socket.AF_INET]
        if self._prefix is 0:
            self._prefix = self._bits_max
        else:
            try:
                self._prefix = int(self._prefix)
            except ValueError:
                raise ValueError('Invalid prefix length: %r' % self._prefix)
        if self._prefix > self._bits_max or self._prefix < 0:
            raise ValueError('Invalid prefix length: %r' % self._prefix)

    @property
    def family(self):
        """Address family: `socket.AF_INET` or `socket.AF_INET6`"""
        return self._family

    def address_in_net(self, ip_address):
        """Checks if the `ip_address` belongs to the same subnet."""
        family, address = get_ip_addr_info(ip_address)
        if family != self._family:
            return False
        return address >> self._bits_max - self._prefix == \
               self._addr >> self._bits_max - self._prefix


def get_ip_addr_info(ip_address):
    """Checks if the string `ip_address` is a valid IPv4 or IPv6 address.

    When the `ip_address` could be validated successfully a tuple
    `(address_family, address_as_long)` will be returned. The
    `address_family`will be either `socket.AF_INET` or `socket.AF_INET6`.
    """
    if not isinstance(ip_address, str) or not ip_address:
        raise TypeError('ip_address must be a non empty string.')
    if not ip_address.count(':'):
        family = socket.AF_INET
        try:
            address = socket.inet_aton(ip_address)
        except socket.error:
            raise ValueError('Not a valid IPv4 address: %r' % ip_address)
    elif not socket.has_ipv6:
        raise ValueError('Unsupported IP address (IPv6): %r' % ip_address)
    else:
        family = socket.AF_INET6
        try:
            address = socket.inet_pton(family, ip_address)
        except socket.error:
            raise ValueError('Not a valid IPv6 address: %r' % ip_address)
    return (family, int(address.encode('hex'), 16))
