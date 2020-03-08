# -*- coding: UTF-8 -*-
# Copyright (c) 2010 - 2014, Pascal Volk
# See COPYING for distribution information.
"""
    vmm.password
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    vmm's password module to generate password hashes from
    passwords or random passwords. This module provides following
    functions:

        hashed_password = pwhash(password[, scheme][, user])
        random_password = randompw()
        scheme, encoding = verify_scheme(scheme)
        schemes, encodings = list_schemes()
        scheme = extract_scheme(hashed_password)
"""

import hashlib
import re

from base64 import b64encode
from binascii import b2a_hex
from crypt import crypt
from random import SystemRandom
from subprocess import Popen, PIPE
from gettext import gettext as _

from vmm import ENCODING
from vmm.emailaddress import EmailAddress
from vmm.common import get_unicode, version_str
from vmm.constants import VMM_ERROR
from vmm.errors import VMMError

SALTCHARS = "./0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
PASSWDCHARS = "._-+#*23456789abcdefghikmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
DEFAULT_B64 = (None, "B64", "BASE64")
DEFAULT_HEX = (None, "HEX")
CRYPT_ID_MD5 = 1
CRYPT_ID_BLF = "2a"
CRYPT_ID_SHA256 = 5
CRYPT_ID_SHA512 = 6
CRYPT_SALT_LEN = 2
CRYPT_BLF_ROUNDS_MIN = 4
CRYPT_BLF_ROUNDS_MAX = 31
CRYPT_BLF_SALT_LEN = 22
CRYPT_MD5_SALT_LEN = 8
CRYPT_SHA2_ROUNDS_DEFAULT = 5000
CRYPT_SHA2_ROUNDS_MIN = 1000
CRYPT_SHA2_ROUNDS_MAX = 999999999
CRYPT_SHA2_SALT_LEN = 16
SALTED_ALGO_SALT_LEN = 4


cfg_dget = lambda option: None
_sys_rand = SystemRandom()
_choice = _sys_rand.choice


def _get_salt(s_len):
    return "".join(_choice(SALTCHARS) for _ in range(s_len))


def _doveadmpw(password, scheme, encoding):
    """Communicates with Dovecot's doveadm and returns
    the hashed password: {scheme[.encoding]}hash
    """
    if encoding:
        scheme = ".".join((scheme, encoding))
    cmd_args = [
        cfg_dget("bin.doveadm"),
        "pw",
        "-s",
        scheme,
        "-p",
        get_unicode(password),
    ]
    process = Popen(cmd_args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if process.returncode:
        raise VMMError(stderr.strip().decode(ENCODING), VMM_ERROR)
    hashed = stdout.strip().decode(ENCODING)
    if not hashed.startswith("{%s}" % scheme):
        raise VMMError(
            "Unexpected result from %s: %s" % (cfg_dget("bin.doveadm"), hashed),
            VMM_ERROR,
        )
    return hashed


def _md4_new():
    """Returns an new MD4-hash object if supported by the hashlib -
    otherwise `None`.
    """
    try:
        return hashlib.new("md4")
    except ValueError as err:
        if err.args[0].startswith("unsupported hash type"):
            return None
        else:
            raise


def _format_digest(digest, scheme, encoding):
    """Formats the arguments to a string: {scheme[.encoding]}digest."""
    if not encoding:
        return "{%s}%s" % (scheme, digest)
    return "{%s.%s}%s" % (scheme, encoding, digest)


def _clear_hash(password, scheme, encoding):
    """Generates a (encoded) CLEARTEXT/PLAIN 'hash'."""
    password = password.decode(ENCODING)
    if encoding:
        if encoding == "HEX":
            password = b2a_hex(password.encode()).decode()
        else:
            password = b64encode(password.encode()).decode()
        return _format_digest(password, scheme, encoding)
    return "{%s}%s" % (scheme, password)


def _get_crypt_blowfish_salt():
    """Generates a salt for Blowfish crypt."""
    rounds = cfg_dget("misc.crypt_blowfish_rounds")
    if rounds < CRYPT_BLF_ROUNDS_MIN:
        rounds = CRYPT_BLF_ROUNDS_MIN
    elif rounds > CRYPT_BLF_ROUNDS_MAX:
        rounds = CRYPT_BLF_ROUNDS_MAX
    return "$%s$%02d$%s" % (CRYPT_ID_BLF, rounds, _get_salt(CRYPT_BLF_SALT_LEN))


def _get_crypt_sha2_salt(crypt_id):
    """Generates a salt for crypt using the SHA-256 or SHA-512 encryption
    method.
    *crypt_id* must be either `5` (SHA-256) or `6` (SHA-512).
    """
    assert crypt_id in (CRYPT_ID_SHA256, CRYPT_ID_SHA512), (
        "invalid crypt " "id: %r" % crypt_id
    )
    if crypt_id is CRYPT_ID_SHA512:
        rounds = cfg_dget("misc.crypt_sha512_rounds")
    else:
        rounds = cfg_dget("misc.crypt_sha256_rounds")
    if rounds < CRYPT_SHA2_ROUNDS_MIN:
        rounds = CRYPT_SHA2_ROUNDS_MIN
    elif rounds > CRYPT_SHA2_ROUNDS_MAX:
        rounds = CRYPT_SHA2_ROUNDS_MAX
    if rounds == CRYPT_SHA2_ROUNDS_DEFAULT:
        return "$%d$%s" % (crypt_id, _get_salt(CRYPT_SHA2_SALT_LEN))
    return "$%d$rounds=%d$%s" % (crypt_id, rounds, _get_salt(CRYPT_SHA2_SALT_LEN))


def _crypt_hash(password, scheme, encoding):
    """Generates (encoded) CRYPT/MD5/{BLF,MD5,SHA{256,512}}-CRYPT hashes."""
    if scheme == "CRYPT":
        salt = _get_salt(CRYPT_SALT_LEN)
    elif scheme == "BLF-CRYPT":
        salt = _get_crypt_blowfish_salt()
    elif scheme in ("MD5-CRYPT", "MD5"):
        salt = "$%d$%s" % (CRYPT_ID_MD5, _get_salt(CRYPT_MD5_SALT_LEN))
    elif scheme == "SHA256-CRYPT":
        salt = _get_crypt_sha2_salt(CRYPT_ID_SHA256)
    else:
        salt = _get_crypt_sha2_salt(CRYPT_ID_SHA512)
    encrypted = crypt(password.decode(ENCODING), salt)
    if encoding:
        if encoding == "HEX":
            encrypted = b2a_hex(encrypted.encode()).decode()
        else:
            encrypted = b64encode(encrypted.encode()).decode()
    return _format_digest(encrypted, scheme, encoding)


def _md4_hash(password, scheme, encoding):
    """Generates encoded PLAIN-MD4 hashes."""
    md4 = _md4_new()
    if md4:
        md4.update(password)
        if encoding in DEFAULT_HEX:
            digest = md4.hexdigest()
        else:
            digest = b64encode(md4.digest()).decode()
        return _format_digest(digest, scheme, encoding)
    return _doveadmpw(password, scheme, encoding)


def _md5_hash(password, scheme, encoding, user=None):
    """Generates DIGEST-MD5 aka PLAIN-MD5 and LDAP-MD5 hashes."""
    md5 = hashlib.md5()
    if scheme == "DIGEST-MD5":
        md5.update(user.localpart.encode() + b":" + user.domainname.encode() + b":")
    md5.update(password)
    if (scheme in ("PLAIN-MD5", "DIGEST-MD5") and encoding in DEFAULT_HEX) or (
        scheme == "LDAP-MD5" and encoding == "HEX"
    ):
        digest = md5.hexdigest()
    else:
        digest = b64encode(md5.digest()).decode()
    return _format_digest(digest, scheme, encoding)


def _ntlm_hash(password, scheme, encoding):
    """Generates NTLM hashes."""
    md4 = _md4_new()
    if md4:
        password = b"".join(bytes(x) for x in zip(password, bytes(len(password))))
        md4.update(password)
        if encoding in DEFAULT_HEX:
            digest = md4.hexdigest()
        else:
            digest = b64encode(md4.digest()).decode()
        return _format_digest(digest, scheme, encoding)
    return _doveadmpw(password, scheme, encoding)


def _create_hashlib_hash(algorithm, with_salt=False):
    def hash_password(password, scheme, encoding):
        # we default to an empty byte-string to keep the internal logic
        # clean as it behaves like we would not have used a salt
        salt = _get_salt(SALTED_ALGO_SALT_LEN).encode() if with_salt else b""
        _hash = algorithm(password + salt)
        if encoding in DEFAULT_B64:
            digest = b64encode(_hash.digest() + salt).decode()
        else:
            digest = _hash.hexdigest() + b2a_hex(salt).decode()
        return _format_digest(digest, scheme, encoding)
    return hash_password


_sha1_hash = _create_hashlib_hash(hashlib.sha1)
_sha256_hash = _create_hashlib_hash(hashlib.sha256)
_sha512_hash = _create_hashlib_hash(hashlib.sha512)
_smd5_hash = _create_hashlib_hash(hashlib.md5, with_salt=True)
_ssha1_hash = _create_hashlib_hash(hashlib.sha1, with_salt=True)
_ssha256_hash = _create_hashlib_hash(hashlib.sha256, with_salt=True)
_ssha512_hash = _create_hashlib_hash(hashlib.sha512, with_salt=True)


_scheme_info = {
    "CLEAR": (_clear_hash, 0x2010DF00),
    "CLEARTEXT": (_clear_hash, 0x10000F00),
    "CRAM-MD5": (_doveadmpw, 0x10000F00),
    "CRYPT": (_crypt_hash, 0x10000F00),
    "DIGEST-MD5": (_md5_hash, 0x10000F00),
    "HMAC-MD5": (_doveadmpw, 0x10000F00),
    "LANMAN": (_doveadmpw, 0x10000F00),
    "LDAP-MD5": (_md5_hash, 0x10000F00),
    "MD5": (_crypt_hash, 0x10000F00),
    "MD5-CRYPT": (_crypt_hash, 0x10000F00),
    "NTLM": (_ntlm_hash, 0x10000F00),
    "OTP": (_doveadmpw, 0x10100A01),
    "PLAIN": (_clear_hash, 0x10000F00),
    "PLAIN-MD4": (_md4_hash, 0x10000F00),
    "PLAIN-MD5": (_md5_hash, 0x10000F00),
    "RPA": (_doveadmpw, 0x10000F00),
    "SCRAM-SHA-1": (_doveadmpw, 0x20200A01),
    "SHA": (_sha1_hash, 0x10000F00),
    "SHA1": (_sha1_hash, 0x10000F00),
    "SHA256": (_sha256_hash, 0x10100A01),
    "SHA512": (_sha512_hash, 0x20000B03),
    "SKEY": (_doveadmpw, 0x10100A01),
    "SMD5": (_smd5_hash, 0x10000F00),
    "SSHA": (_ssha1_hash, 0x10000F00),
    "SSHA256": (_ssha256_hash, 0x10200A04),
    "SSHA512": (_ssha512_hash, 0x20000B03),
}


def extract_scheme(password_hash):
    """Returns the extracted password scheme from *password_hash*.

    If the scheme couldn't be extracted, **None** will be returned.
    """
    scheme = re.match(r"^\{([^\}]{3,37})\}", password_hash)
    if scheme:
        return scheme.groups()[0]
    return scheme


def list_schemes():
    """Returns the tuple (schemes, encodings).

    `schemes` is an iterator for all supported password schemes (depends on
    the used Dovecot version and features of the libc).
    `encodings` is a tuple with all usable encoding suffixes.
    """
    dcv = cfg_dget("misc.dovecot_version")
    schemes = (k for (k, v) in _scheme_info.items() if v[1] <= dcv)
    encodings = (".B64", ".BASE64", ".HEX")
    return schemes, encodings


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
    assert isinstance(scheme, str), "Not a str: {!r}".format(scheme)
    scheme_encoding = scheme.upper().split(".")
    scheme = scheme_encoding[0]
    if scheme not in _scheme_info:
        raise VMMError(_("Unsupported password scheme: '%s'") % scheme, VMM_ERROR)
    if cfg_dget("misc.dovecot_version") < _scheme_info[scheme][1]:
        raise VMMError(
            _("The password scheme '%(scheme)s' requires Dovecot " ">= v%(version)s.")
            % {"scheme": scheme, "version": version_str(_scheme_info[scheme][1])},
            VMM_ERROR,
        )
    if len(scheme_encoding) > 1:
        if scheme_encoding[1] not in ("B64", "BASE64", "HEX"):
            raise VMMError(
                _("Unsupported password encoding: '%s'") % scheme_encoding[1], VMM_ERROR
            )
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
    if not isinstance(password, str):
        raise TypeError("Password is not a string: %r" % password)
    password = password.encode(ENCODING).strip()
    if not password:
        raise ValueError("Could not accept empty password.")
    if scheme is None:
        scheme = cfg_dget("misc.password_scheme")
    scheme, encoding = verify_scheme(scheme)
    if scheme == "DIGEST-MD5":
        assert isinstance(user, EmailAddress)
        return _md5_hash(password, scheme, encoding, user)
    return _scheme_info[scheme][0](password, scheme, encoding)


def randompw():
    """Generates a plain text random password.

    The length of the password can be configured in the ``vmm.cfg``
    (account.password_length).
    """
    pw_len = cfg_dget("account.password_length")
    if pw_len < 8:
        pw_len = 8
    return "".join(_sys_rand.sample(PASSWDCHARS, pw_len))


# Check for Blowfish/SHA-256/SHA-512 support in crypt.crypt()
if "$2a$04$0123456789abcdefABCDE.N.drYX5yIAL1LkTaaZotW3yI0hQhZru" == crypt(
    "08/15!test~4711", "$2a$04$0123456789abcdefABCDEF$"
):
    _scheme_info["BLF-CRYPT"] = (_crypt_hash, 0x20000B06)
if (
    "$5$rounds=1000$0123456789abcdef$K/DksR0DT01hGc8g/kt9McEgrbFMKi9qrb1jehe7hn4"
    == crypt("08/15!test~4711", "$5$rounds=1000$0123456789abcdef$")
):
    _scheme_info["SHA256-CRYPT"] = (_crypt_hash, 0x20000B06)
if (
    "$6$rounds=1000$0123456789abcdef$ZIAd5WqfyLkpvsVCVUU1GrvqaZTqvhJoouxdSqJO71l9Ld3"
    "tVrfOatEjarhghvEYADkq//LpDnTeO90tcbtHR1"
    == crypt("08/15!test~4711", "$6$rounds=1000$0123456789abcdef$")
):
    _scheme_info["SHA512-CRYPT"] = (_crypt_hash, 0x20000B06)

del cfg_dget
