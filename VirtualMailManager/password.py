# -*- coding: UTF-8 -*-
# Copyright (c) 2010, Pascal Volk
# See COPYING for distribution information.

"""
    VirtualMailManager.password

    VirtualMailManager's password module to generate password hashes from
    passwords or random passwords. This module provides following
    functions:

        hashed_password = pwhash(password[, scheme][, user])
        random_password = randompw()
        scheme, encoding = verify_scheme(scheme)
"""

from crypt import crypt
from random import SystemRandom
from subprocess import Popen, PIPE

try:
    import hashlib
except ImportError:
    from VirtualMailManager.pycompat import hashlib

from VirtualMailManager import ENCODING
from VirtualMailManager.EmailAddress import EmailAddress
from VirtualMailManager.common import get_unicode, version_str
from VirtualMailManager.constants.ERROR import VMM_ERROR
from VirtualMailManager.errors import VMMError

COMPAT = hasattr(hashlib, 'compat')
SALTCHARS = './0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
PASSWDCHARS = '._-+#*23456789abcdefghikmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
DEFAULT_B64 = (None, 'B64', 'BASE64')
DEFAULT_HEX = (None, 'HEX')

_ = lambda msg: msg
cfg_dget = lambda option: None
_sys_rand = SystemRandom()
_get_salt = lambda salt_len: ''.join(_sys_rand.sample(SALTCHARS, salt_len))


def _test_crypt_algorithms():
    """Check for Blowfish/SHA-256/SHA-512 support in crypt.crypt()."""
    blowfish_ = sha256_ = sha512_ = False
    _blowfish = '$2a$04$0123456789abcdefABCDE.N.drYX5yIAL1LkTaaZotW3yI0hQhZru'
    _sha256 = '$5$rounds=1000$0123456789abcdef$K/DksR0DT01hGc8g/kt9McEgrbFMKi\
9qrb1jehe7hn4'
    _sha512 = '$6$rounds=1000$0123456789abcdef$ZIAd5WqfyLkpvsVCVUU1GrvqaZTqvh\
JoouxdSqJO71l9Ld3tVrfOatEjarhghvEYADkq//LpDnTeO90tcbtHR1'

    if crypt('08/15!test~4711', '$2a$04$0123456789abcdefABCDEF$') == _blowfish:
        blowfish_ = True
    if crypt('08/15!test~4711', '$5$rounds=1000$0123456789abcdef$') == _sha256:
        sha256_ = True
    if crypt('08/15!test~4711', '$6$rounds=1000$0123456789abcdef$') == _sha512:
        sha512_ = True
    return blowfish_, sha256_, sha512_

CRYPT_BLOWFISH, CRYPT_SHA256, CRYPT_SHA512 = _test_crypt_algorithms()


def _dovecotpw(password, scheme, encoding):
    """Communicates with dovecotpw (Dovecot 2.0: `doveadm pw`) and returns
    the hashed password: {scheme[.encoding]}hash
    """
    if encoding:
        scheme = '.'.join((scheme, encoding))
    cmd_args = [cfg_dget('bin.dovecotpw'), '-s', scheme, '-p',
                get_unicode(password)]
    if cfg_dget('misc.dovecot_version') >= 0x20000a01:
        cmd_args.insert(1, 'pw')
    process = Popen(cmd_args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if process.returncode:
        raise VMMError(stderr.strip(), VMM_ERROR)
    hashed = stdout.strip()
    if not hashed.startswith('{%s}' % scheme):
        raise VMMError('Unexpected result from %s: %s' %
                       (cfg_dget('bin.dovecotpw'), hashed), VMM_ERROR)
    return hashed


def _md4_new():
    """Returns an new MD4-hash object if supported by the hashlib or
    provided by PyCrypto - other `None`.
    """
    try:
        return hashlib.new('md4')
    except ValueError, err:
        if str(err) == 'unsupported hash type':
            if not COMPAT:
                try:
                    from Crypto.Hash import MD4
                    return MD4.new()
                except ImportError:
                    return None
        else:
            raise


def _sha256_new(data=''):
    """Returns a new sha256 object from the hashlib.

    Returns `None` if the PyCrypto in pycompat.hashlib is too old."""
    if not COMPAT:
        return hashlib.sha256(data)
    try:
        return hashlib.new('sha256', data)
    except ValueError, err:
        if str(err) == 'unsupported hash type':
            return None
        else:
            raise


def _format_digest(digest, scheme, encoding):
    """Formats the arguments to a string: {scheme[.encoding]}digest."""
    if not encoding:
        return '{%s}%s' % (scheme, digest)
    return '{%s.%s}%s' % (scheme, encoding, digest)


def _clear_hash(password, scheme, encoding):
    """Generates a (encoded) CLEARTEXT/PLAIN 'hash'."""
    if encoding:
        if encoding == 'HEX':
            password = password.encode('hex')
        else:
            password = password.encode('base64').replace('\n', '')
        return _format_digest(password, scheme, encoding)
    return get_unicode('{%s}%s' % (scheme, password))


def _get_crypt_blowfish_salt():
    """Generates a salt for Blowfish crypt."""
    rounds = cfg_dget('misc.crypt_blowfish_rounds')
    if rounds < 4:
        rounds = 4
    elif rounds > 31:
        rounds = 31
    return '$2a$%02d$%s' % (rounds, _get_salt(22))


def _get_crypt_shaxxx_salt(crypt_id):
    """Generates a salt for crypt using the SHA-256 or SHA-512 encryption
    method.
    *crypt_id* must be either `5` (SHA-256) or `6` (SHA1-512).
    """
    assert crypt_id in (5, 6), 'invalid crypt id: %r' % crypt_id
    if crypt_id is 6:
        rounds = cfg_dget('misc.crypt_sha512_rounds')
    else:
        rounds = cfg_dget('misc.crypt_sha256_rounds')
    if rounds < 1000:
        rounds = 1000
    elif rounds > 999999999:
        rounds = 999999999
    return '$%d$rounds=%d$%s' % (crypt_id, rounds, _get_salt(16))


def _crypt_hash(password, scheme, encoding):
    """Generates (encoded) CRYPT/MD5/MD5-CRYPT hashes."""
    if scheme == 'CRYPT':
        if CRYPT_BLOWFISH and cfg_dget('misc.crypt_blowfish_rounds'):
            salt = _get_crypt_blowfish_salt()
        elif CRYPT_SHA512 and cfg_dget('misc.crypt_sha512_rounds'):
            salt = _get_crypt_shaxxx_salt(6)
        elif CRYPT_SHA256 and cfg_dget('misc.crypt_sha256_rounds'):
            salt = _get_crypt_shaxxx_salt(5)
        else:
            salt = _get_salt(2)
    else:
        salt = '$1$%s' % _get_salt(8)
    encrypted = crypt(password, salt)
    if encoding:
        if encoding == 'HEX':
            encrypted = encrypted.encode('hex')
        else:
            encrypted = encrypted.encode('base64').replace('\n', '')
    return _format_digest(encrypted, scheme, encoding)


def _md4_hash(password, scheme, encoding):
    """Generates encoded PLAIN-MD4 hashes."""
    md4 = _md4_new()
    if md4:
        md4.update(password)
        if encoding in DEFAULT_HEX:
            digest = md4.hexdigest()
        else:
            digest = md4.digest().encode('base64').rstrip()
        return _format_digest(digest, scheme, encoding)
    return _dovecotpw(password, scheme, encoding)


def _md5_hash(password, scheme, encoding, user=None):
    """Generates DIGEST-MD5 aka PLAIN-MD5 and LDAP-MD5 hashes."""
    md5 = hashlib.md5()
    if scheme == 'DIGEST-MD5':
        #  Prior to Dovecot v1.1.12/v1.2.beta2 there was a problem with a
        #  empty auth_realms setting in dovecot.conf and user@domain.tld
        #  usernames. So we have to generate different hashes for different
        #  versions. See also:
        #       http://dovecot.org/list/dovecot-news/2009-March/000103.html
        #       http://hg.dovecot.org/dovecot-1.1/rev/2b0043ba89ae
        if cfg_dget('misc.dovecot_version') >= 0x1010cf00:
            md5.update('%s:%s:' % (user.localpart, user.domainname))
        else:
            md5.update('%s::' % user)
    md5.update(password)
    if (scheme in ('PLAIN-MD5', 'DIGEST-MD5') and encoding in DEFAULT_HEX) or \
       (scheme == 'LDAP-MD5' and encoding == 'HEX'):
        digest = md5.hexdigest()
    else:
        digest = md5.digest().encode('base64').rstrip()
    return _format_digest(digest, scheme, encoding)


def _ntlm_hash(password, scheme, encoding):
    """Generates NTLM hashes."""
    md4 = _md4_new()
    if md4:
        password = ''.join('%s\x00' % c for c in password)
        md4.update(password)
        if encoding in DEFAULT_HEX:
            digest = md4.hexdigest()
        else:
            digest = md4.digest().encode('base64').rstrip()
        return _format_digest(digest, scheme, encoding)
    return _dovecotpw(password, scheme, encoding)


def _sha1_hash(password, scheme, encoding):
    """Generates SHA1 aka SHA hashes."""
    sha1 = hashlib.sha1(password)
    if encoding in DEFAULT_B64:
        digest = sha1.digest().encode('base64').rstrip()
    else:
        digest = sha1.hexdigest()
    return _format_digest(digest, scheme, encoding)


def _sha256_hash(password, scheme, encoding):
    """Generates SHA256 hashes."""
    sha256 = _sha256_new(password)
    if sha256:
        if encoding in DEFAULT_B64:
            digest = sha256.digest().encode('base64').rstrip()
        else:
            digest = sha256.hexdigest()
        return _format_digest(digest, scheme, encoding)
    return _dovecotpw(password, scheme, encoding)


def _sha512_hash(password, scheme, encoding):
    """Generates SHA512 hashes."""
    if not COMPAT:
        sha512 = hashlib.sha512(password)
        if encoding in DEFAULT_B64:
            digest = sha512.digest().encode('base64').replace('\n', '')
        else:
            digest = sha512.hexdigest()
        return _format_digest(digest, scheme, encoding)
    return _dovecotpw(password, scheme, encoding)


def _smd5_hash(password, scheme, encoding):
    """Generates SMD5 (salted PLAIN-MD5) hashes."""
    md5 = hashlib.md5(password)
    salt = _get_salt(4)
    md5.update(salt)
    if encoding in DEFAULT_B64:
        digest = (md5.digest() + salt).encode('base64').rstrip()
    else:
        digest = md5.hexdigest() + salt.encode('hex')
    return _format_digest(digest, scheme, encoding)


def _ssha1_hash(password, scheme, encoding):
    """Generates SSHA (salted SHA/SHA1) hashes."""
    sha1 = hashlib.sha1(password)
    salt = _get_salt(4)
    sha1.update(salt)
    if encoding in DEFAULT_B64:
        digest = (sha1.digest() + salt).encode('base64').rstrip()
    else:
        digest = sha1.hexdigest() + salt.encode('hex')
    return _format_digest(digest, scheme, encoding)


def _ssha256_hash(password, scheme, encoding):
    """Generates SSHA256 (salted SHA256) hashes."""
    sha256 = _sha256_new(password)
    if sha256:
        salt = _get_salt(4)
        sha256.update(salt)
        if encoding in DEFAULT_B64:
            digest = (sha256.digest() + salt).encode('base64').rstrip()
        else:
            digest = sha256.hexdigest() + salt.encode('hex')
        return _format_digest(digest, scheme, encoding)
    return _dovecotpw(password, scheme, encoding)


def _ssha512_hash(password, scheme, encoding):
    """Generates SSHA512 (salted SHA512) hashes."""
    if not COMPAT:
        salt = _get_salt(4)
        sha512 = hashlib.sha512(password + salt)
        if encoding in DEFAULT_B64:
            digest = (sha512.digest() + salt).encode('base64').replace('\n',
                                                                       '')
        else:
            digest = sha512.hexdigest() + salt.encode('hex')
        return _format_digest(digest, scheme, encoding)
    return _dovecotpw(password, scheme, encoding)

_scheme_info = {
    'CLEARTEXT': (_clear_hash, 0x10000f00),
    'CRAM-MD5': (_dovecotpw, 0x10000f00),
    'CRYPT': (_crypt_hash, 0x10000f00),
    'DIGEST-MD5': (_md5_hash, 0x10000f00),
    'HMAC-MD5': (_dovecotpw, 0x10000f00),
    'LANMAN': (_dovecotpw, 0x10000f00),
    'LDAP-MD5': (_md5_hash, 0x10000f00),
    'MD5': (_crypt_hash, 0x10000f00),
    'MD5-CRYPT': (_crypt_hash, 0x10000f00),
    'NTLM': (_ntlm_hash, 0x10000f00),
    'OTP': (_dovecotpw, 0x10100a01),
    'PLAIN': (_clear_hash, 0x10000f00),
    'PLAIN-MD4': (_md4_hash, 0x10000f00),
    'PLAIN-MD5': (_md5_hash, 0x10000f00),
    'RPA': (_dovecotpw, 0x10000f00),
    'SHA': (_sha1_hash, 0x10000f00),
    'SHA1': (_sha1_hash, 0x10000f00),
    'SHA256': (_sha256_hash, 0x10100a01),
    'SHA512': (_sha512_hash, 0x20000b03),
    'SKEY': (_dovecotpw, 0x10100a01),
    'SMD5': (_smd5_hash, 0x10000f00),
    'SSHA': (_ssha1_hash, 0x10000f00),
    'SSHA256': (_ssha256_hash, 0x10200a04),
    'SSHA512': (_ssha512_hash, 0x20000b03),
}


def verify_scheme(scheme):
    """Checks if the password scheme *scheme* is known and supported by the
    configured `misc.dovecot_version`.

    The *scheme* maybe a password scheme's name (e.g.: 'PLAIN') or a scheme
    name with a encoding suffix (e.g. 'PLAIN.BASE64').  If the scheme is
    known and supported by the used Dovecot version,
    a tuple ``(scheme, encoding)`` will be returned.
    The `encoding` in the tuple may be `None`.

    Raises a `VMMError` if the password scheme:
      * is unknown
      * depends on a newer Dovecot version
      * has a unknown encoding suffix
    """
    assert isinstance(scheme, basestring), 'Not a str/unicode: %r' % scheme
    scheme_encoding = scheme.upper().split('.')
    scheme = scheme_encoding[0]
    if not scheme in _scheme_info:
        raise VMMError(_(u"Unsupported password scheme: '%s'") % scheme,
                       VMM_ERROR)
    if cfg_dget('misc.dovecot_version') < _scheme_info[scheme][1]:
        raise VMMError(_(u"The password scheme '%(scheme)s' requires Dovecot "
                         u">= v%(version)s") % {'scheme': scheme,
                       'version': version_str(_scheme_info[scheme][1])},
                       VMM_ERROR)
    if len(scheme_encoding) > 1:
        if cfg_dget('misc.dovecot_version') < 0x10100a01:
            raise VMMError(_(u'Encoding suffixes for password schemes require '
                             u'Dovecot >= v1.1.alpha1'), VMM_ERROR)
        if scheme_encoding[1] not in ('B64', 'BASE64', 'HEX'):
            raise VMMError(_(u"Unsupported password encoding: '%s'") %
                           scheme_encoding[1], VMM_ERROR)
        encoding = scheme_encoding[1]
    else:
        encoding = None
    return scheme, encoding


def pwhash(password, scheme=None, user=None):
    """Generates a password hash from the plain text *password* string.

    If no *scheme* is given the password scheme from the configuration will
    be used for the hash generation.  When 'DIGEST-MD5' is used as scheme,
    also an EmailAddress instance must be given as *user* argument.
    """
    if not isinstance(password, basestring):
        raise TypeError('Password is not a string: %r' % password)
    if isinstance(password, unicode):
        password = password.encode(ENCODING)
    password = password.strip()
    if not password:
        raise ValueError("Couldn't accept empty password.")
    if scheme is None:
        scheme = cfg_dget('misc.password_scheme')
    scheme, encoding = verify_scheme(scheme)
    if scheme == 'DIGEST-MD5':
        assert isinstance(user, EmailAddress)
        return _md5_hash(password, scheme, encoding, user)
    return _scheme_info[scheme][0](password, scheme, encoding)


def randompw():
    """Generates a plain text random password.

    The length of the password can be configured in the ``vmm.cfg``
    (account.password_length).
    """
    pw_len = cfg_dget('account.password_length')
    if pw_len < 8:
        pw_len = 8
    return ''.join(_sys_rand.sample(PASSWDCHARS, pw_len))

del _, cfg_dget, _test_crypt_algorithms
