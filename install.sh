#!/bin/bash
# $Id$
#
# Installation script for the Virtual Mail Manager
# run: ./install.sh

LANG=C
PATH=/bin:/usr/sbin:/usr/bin
INSTALL_OPTS="-g 0 -o 0 -p -v"
PREFIX=/usr/local
PF_CONFDIR=$(postconf -h config_directory)
DOC_DIR=${PREFIX}/share/doc/vmm
MAN1DIR=${PREFIX}/share/man/man1
MAN5DIR=${PREFIX}/share/man/man5
DOCS="ChangeLog COPYING INSTALL README"

if [ $(id -u) -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

python setup.py install --prefix ${PREFIX}
python setup.py clean --all >/dev/null

install -b -m 0600 ${INSTALL_OPTS} vmm.cfg ${PREFIX}/etc/
install -b -m 0640 ${INSTALL_OPTS} pgsql-*.cf ${PF_CONFDIR}/
install -m 0700 ${INSTALL_OPTS} vmm ${PREFIX}/sbin

[ -d ${MAN1DIR} ] || mkdir -m 0755 -p ${MAN1DIR}
install -m 0644 ${INSTALL_OPTS} vmm.1 ${MAN1DIR}

[ -d ${DOC_DIR} ] || mkdir -m 0755 -p ${DOC_DIR}
for DOC in ${DOCS}; do
    install -m 0644 ${INSTALL_OPTS} ${DOC} ${DOC_DIR}
done

[ -d ${DOC_DIR}/examples ] || mkdir -m 0755 -p ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} pgsql-*.cf ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} vmm.cfg ${DOC_DIR}/examples

echo
echo "Don't forget to edit ${PREFIX}/etc/vmm.cfg - or run: vmm cf"
echo "and ${PF_CONFDIR}/pgsql-*.cf files."
echo
