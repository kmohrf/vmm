# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2012, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.pycompat.hashlib

    VirtualMailManager's minimal hashlib emulation for Python 2.4

    hashlib.md5(...), hashlib.sha1(...), hashlib.new('md5', ...) and
    hashlib.new('sha1', ...) will work always.

    When the PyCrypto module <http://www.pycrypto.org/> could be found in
    sys.path hashlib.new('md4', ...) will also work.

    With PyCrypto >= 2.1.0alpha1 hashlib.new('sha256', ...) and
    hashlib.sha256(...) becomes functional.
"""


import md5 as _md5
import sha as _sha1

try:
    import Crypto
except ImportError:
    _md4 = None
    SHA256 = None
else:
    from Crypto.Hash import MD4 as _md4
    if hasattr(Crypto, 'version_info'):  # <- Available since v2.1.0alpha1
        from Crypto.Hash import SHA256   # SHA256 works since v2.1.0alpha1
        sha256 = SHA256.new
    else:
        SHA256 = None
    del Crypto


compat = 0x01
md5 = _md5.new
sha1 = _sha1.new


def new(name, string=''):
    """Return a new hashing object using the named algorithm, optionally
    initialized with the provided string.
    """
    if name in ('md5', 'MD5'):
        return _md5.new(string)
    if name in ('sha1', 'SHA1'):
        return _sha1.new(string)
    if not _md4:
        raise ValueError('unsupported hash type')
    if name in ('md4', 'MD4'):
        return _md4.new(string)
    if name in ('sha256', 'SHA256') and SHA256:
        return SHA256.new(string)
    raise ValueError('unsupported hash type')
