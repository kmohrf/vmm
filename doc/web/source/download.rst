===============
Downloading vmm
===============

Current version
---------------
|curr_vers_rel_date|
|rel_hist|

Download a gzip compressed archive
----------------------------------
vmm could be downloaded from the `download page`_ at `SourceForge`_. To
extract the downloaded archive use ``tar xzf vmm-0.6.1.tar.gz``. This will
create the new directory :file:`vmm-0.6.1` in the current working directory.

Verify the downloaded archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you have downloaded the archive from the download site you can
optionally verify the integrity_ of this archive.
In order to verify the integrity of the archive you have to download the
corresponding signature file (:file:`vmm-0.6.1.tar.gz.sig`) too.
The signature can be verified using GPG_ or PGP_.
For example to check the signature of the archive :file:`vmm-0.6.1.tar.gz`
you can execute this command ``gpg --verify vmm-0.6.1.tar.gz.sig``.

The tarball was signed by Pascal Volk (ID: CEC0904E).
You can fetch the public key from a key server using the command
``gpg --recv-keys 0xCEC0904E``.

Get vmm from the Mercurial repository
-------------------------------------
To get a tagged clone of the current vmm release from the Mercurial_
repository use:
``hg clone http://hg.localdomain.org/vmm/ -r vmm-0.6.1 vmm-0.6.1``.
This will put the files into the new created directory :file:`vmm-0.6.1`.

When you omit the ``-r vmm-0.6.1`` option, you will get the latest changes
from the `vmm repository`_. This code may work for you or not.

Get vmm from the Git repository
-------------------------------
The Debian project is hosting the `Git repository of vmm
<http://anonscm.debian.org/gitweb/?p=collab-maint/vmm.git>`_.
The *upstream* branch is a mirror of the Mercurial *default* branch.
The *master* branch is for Debian packaging.
In order to clone the *upstream* branch use:
``git clone --branch upstream git://anonscm.debian.org/collab-maint/vmm.git``

Packages
--------
Debian
^^^^^^
Since Debian Wheezy vmm is also `available <http://packages.debian.org/vmm>`_
in the Debian package repository.
The vmm package is `maintained <http://packages.qa.debian.org/v/vmm.html>`_
by Martin F. Krafft.
Take a look at the file :file:`/usr/share/doc/vmm/README.Debian` for Debian
specific modifications.

.. include:: substitutions.rst
.. include:: ext_references.rst
