:mod:`VirtualMailManager` ---  Initialization code and some functions
=====================================================================

.. module:: VirtualMailManager
  :synopsis: Initialization code and some functions

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2

When the VirtualMailManager module, or one of its sub modules, is imported,
the following actions will be performed:

  - :func:`locale.setlocale` (with :const:`locale.LC_ALL`) is called, to set
    :const:`ENCODING`
  - :func:`gettext.install` is called, to have 18N support.

Constants and data
------------------

.. data:: ENCODING

  The systems current character encoding, e.g. ``'UTF-8'`` or
  ``'ANSI_X3.4-1968'`` (aka ASCII).


Functions
---------

.. function:: ace2idna(domainname)

  Converts the idn domain name *domainname* into punycode.

  :param domainname: the domain-ace representation (``xn--…``)
  :type domainname: str
  :rtype: unicode

.. function:: check_domainname(domainname)

  Returns the validated domain name *domainname*.

  It also converts the name of the domain from IDN to ASCII, if necessary.

  :param domainname: the name of the domain
  :type domainname: :obj:`basestring`
  :rtype: str
  :raise VirtualMailManager.errors.VMMError: if the domain name is
    too long or doesn't look like a valid domain name (label.label.label).

.. function:: check_localpart(localpart)

  Returns the validated local-part *localpart* of an e-mail address.

  :param localpart: The local-part of an e-mail address.
  :type localpart: str
  :rtype: str
  :raise VirtualMailManager.errors.VMMError: if the local-part is too
    long or contains invalid characters.

.. function:: exec_ok(binary)

  Checks if the *binary* exists and if it is executable.

  :param binary: path to the binary
  :type binary: str
  :rtype: str
  :raise VirtualMailManager.errors.VMMError: if *binary* isn't a file
    or is not executable.

.. function:: expand_path(path)

  Expands paths, starting with ``.`` or ``~``, to an absolute path.

  :param path: Path to a file or directory
  :type path: str
  :rtype: str

.. function:: get_unicode(string)

  Converts `string` to `unicode`, if necessary.

  :param string: The string taht should be converted
  :type string: str
  :rtype: unicode

.. function:: idn2ascii(domainname)

  Converts the idn domain name *domainname* into punycode.

  :param domainname: the unicode representation of the domain name
  :type domainname: unicode
  :rtype: str

.. function:: is_dir(path)

  Checks if *path* is a directory.

  :param path: Path to a directory
  :type path: str
  :rtype: str
  :raise VirtualMailManager.errors.VMMError: if *path* is not a directory.


Examples
--------

  >>> from VirtualMailManager import *
  >>> ace2idna('xn--pypal-4ve.tld')
  u'p\u0430ypal.tld'
  >>> idn2ascii(u'öko.de')
  'xn--ko-eka.de'
  >>> check_domainname(u'pаypal.tld')
  'xn--pypal-4ve.tld'
  >>> check_localpart('john.doe')
  'john.doe'
  >>> exec_ok('usr/bin/vim')
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "./VirtualMailManager/__init__.py", line 93, in exec_ok
      NO_SUCH_BINARY)
  VirtualMailManager.errors.VMMError: 'usr/bin/vim' is not a file
  >>> exec_ok('/usr/bin/vim')
  '/usr/bin/vim'
  >>> expand_path('.')
  '/home/user/hg/vmm'
  >>> get_unicode('hello world')
  u'hello world'
  >>> is_dir('~/hg')
  '/home/user/hg'
  >>> 

