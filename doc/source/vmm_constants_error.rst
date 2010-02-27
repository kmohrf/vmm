:mod:`VirtualMailManager.constants.ERROR` --- Error codes
=========================================================

.. module:: VirtualMailManager.constants.ERROR
  :synopsis: VirtualMailManager's error codes

.. moduleauthor:: Pascal Volk <neverseen@users.sourceforge.net>

.. toctree::
   :maxdepth: 2

Error codes, used by all :mod:`VirtualMailManager.errors`.

.. data:: ACCOUNT_AND_ALIAS_PRESENT

  Can't delete the  Domain - there are accounts and aliases assigned

.. data:: ACCOUNT_EXISTS

  The Account exists already

.. data:: ACCOUNT_PRESENT

  Can't delete the Domain - there are accounts

.. data:: ALIASDOMAIN_EXISTS

  Can't save/switch the destination of the AliasDomain - old and new destination
  are the same.

.. data:: ALIASDOMAIN_ISDOMAIN

  Can't create AliasDomain - there is already a Domain with the given name

  .. todo:: Move the related check to the Handler class

.. data:: ALIASDOMAIN_NO_DOMDEST

  Can't save/switch the destination of an AliasDomain if the destination was
  omitted 

.. data:: ALIAS_ADDR_DEST_IDENTICAL

  The alias address and its destination are the same

  obsolete?

.. data:: ALIAS_EXCEEDS_EXPANSION_LIMIT

  The Alias has reached or exceeds its expansion limit

.. data:: ALIAS_EXISTS

  Alias with the given destination exists already

  obsolete?

.. data:: ALIAS_MISSING_DEST

  obsolete?

.. data:: ALIAS_PRESENT

  Can't delete Domain or Account - there are aliases assigned

.. data:: CONF_ERROR

  Syntax error in the configuration file or missing settings w/o a default value

.. data:: CONF_NOFILE

  The configuration file couldn't be found

.. data:: CONF_NOPERM

  The user's permissions are insufficient

.. data:: CONF_WRONGPERM

  Configuration file has the wrong access mode

.. data:: DATABASE_ERROR

  A database error occurred

.. data:: DOMAINDIR_GROUP_MISMATCH

  Domain directory is owned by the wrong group

.. data:: DOMAIN_ALIAS_EXISTS

  Can't create Domain - there is already an AliasDomain with the same name

  .. todo:: Move the related check to the Handler class

.. data:: DOMAIN_EXISTS

  The Domain is already available in the database

.. data:: DOMAIN_INVALID

  The domain name is invalid

.. data:: DOMAIN_NO_NAME

  Missing the domain name

.. data:: DOMAIN_TOO_LONG

  The length of domain is > 255

.. data:: FOUND_DOTS_IN_PATH

  Can't delete directory with ``.`` or ``..`` in path

  .. todo:: check if we can solve this issue with expand_path()

.. data:: INVALID_ADDRESS

  The specified value doesn't look like a e-mail address

.. data:: INVALID_AGUMENT

  The given argument is invalid

.. data:: INVALID_OPTION

  The given option is invalid

.. data:: INVALID_SECTION

  The section is not a known configuration section

.. data:: LOCALPART_INVALID

  The local-part of an e-mail address was omitted or is invalid

.. data:: LOCALPART_TOO_LONG

  The local-part (w/o a extension) is too long (> 64)

.. data:: MAILDIR_PERM_MISMATCH

  The Maildir is owned by the wrong user/group

.. data:: MAILLOCATION_INIT

  Can't create a new MailLocation instance

.. data:: NOT_EXECUTABLE

  The binary is not executable

.. data:: NO_SUCH_ACCOUNT

  No Account with the given e-mail address

.. data:: NO_SUCH_ALIAS

  No Alias with the given e-mail address

.. data:: NO_SUCH_ALIASDOMAIN

  The given domain is not an AliasDomain

.. data:: NO_SUCH_BINARY

  Can't find the file at the specified location

.. data:: NO_SUCH_DIRECTORY

  There is no directory with the given path

.. data:: NO_SUCH_DOMAIN

  No Domain with the given name

.. data:: NO_SUCH_RELOCATED

  There is no Relocated user with the given e-mail address

.. data:: RELOCATED_ADDR_DEST_IDENTICAL

  The e-mail address of the Relocated user an its destination are the same

.. data:: RELOCATED_EXISTS

  Can't create Account or Alias, there is already a Relocated user with the
  given e-mail address

.. data:: RELOCATED_MISSING_DEST

  obsolete?

.. data:: TRANSPORT_INIT

  Can't initialize a new Transport instance

.. data:: UNKNOWN_MAILLOCATION_ID

  There is no MailLocation entry with the given ID

.. data:: UNKNOWN_SERVICE

  The specified service is unknown

.. data:: UNKNOWN_TRANSPORT_ID

  There is no Transport entry with the given ID

.. data:: VMM_ERROR

  Internal error

.. data:: VMM_TOO_MANY_FAILURES

  Too many errors in interactive mode
