#!/bin/bash
# $Id$
#
# Installation script for the vmm
# run: ./install.sh

LANG=C
PATH=/usr/sbin:/usr/bin
INSTALL_OPTS="-g 0 -o 0 -p -v"
PREFIX=/usr/local
PF_CONFDIR=$(postconf -h config_directory)
PF_GID=$(id -g postfix)

if [ $(id -u) -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

python setup.py install --prefix ${PREFIX}
python setup.py clean --all >/dev/null

install -b -m 0600 ${INSTALL_OPTS} vmm.cfg ${PREFIX}/etc/
install -b -m 0640 -g ${PF_GID} -o 0 -p -v pgsql-*.cf ${PF_CONFDIR}/
install -m 0700 ${INSTALL_OPTS} vmm ${PREFIX}/sbin/

echo
echo "Don't forget to edit ${PREFIX}/etc/vmm.cfg"
echo "and ${PF_CONFDIR}/pgsql-*.cf files."
echo
