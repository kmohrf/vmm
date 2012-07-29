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
extract the downloaded archive use ``tar xzf vmm-0.6.0.tar.gz``. This will
create the new directory :file:`vmm-0.6.0` in the current working directory.

Verify the downloaded archive
-----------------------------
If you have downloaded the archive from the download site you can
optionally verify the integrity_ of this archive.
In order to verify the integrity of the archive you have to download the
corresponding signature file (:file:`vmm-0.6.0.tar.gz.sig`) too.
The signature can be verified using GPG_ or PGP_.
For example to check the signature of the archive :file:`vmm-0.6.0.tar.gz`
you can execute this command ``gpg --verify vmm-0.6.0.tar.gz.sig``.

The tarball was signed by Pascal Volk (ID: CEC0904E).
You can fetch the public key from a key server using the command
``gpg --recv-keys 0xCEC0904E``.

Get vmm from the Mercurial repository
-------------------------------------
To get a tagged clone of the current vmm release from the Mercurial_
repository use:
``hg clone http://hg.localdomain.org/vmm/ -r vmm-0.6.0 vmm-0.6.0``.
This will put the files into the new created directory :file:`vmm-0.6.0`.

When you omit the ``-r vmm-0.6.0`` option, you will get the latest changes
from the `vmm repository`_. This code may work for you or not.

.. include:: substitutions.rst
.. include:: ext_references.rst
