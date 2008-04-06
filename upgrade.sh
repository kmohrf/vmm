#!/bin/bash
# $Id$
#
# Upgrade script for the Virtual Mail Manager
# run: ./install.sh

LANG=C
PATH=/bin:/usr/sbin:/usr/bin
INSTALL_OPTS="-g 0 -o 0 -p -v"
PREFIX=/usr/local
PF_CONFDIR=$(postconf -h config_directory)
CFS="smtpd_sender_login_maps transport virtual_mailbox_domains"
DOC_DIR=${PREFIX}/share/doc/vmm
DOCS="ChangeLog COPYING INSTALL README"

if [ $(id -u) -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

python setup.py install --prefix ${PREFIX}
python setup.py clean --all >/dev/null

for CF in ${CFS} ; do
    install -b -m 0640 ${INSTALL_OPTS} pgsql-${CF}.cf ${PF_CONFDIR}/
done
install -m 0700 ${INSTALL_OPTS} vmm ${PREFIX}/sbin

[ -d ${DOC_DIR} ] || mkdir -m 0755 -p ${DOC_DIR}
for DOC in ${DOCS}; do
    install -m 0644 ${INSTALL_OPTS} ${DOC} ${DOC_DIR}
done

[ -d ${DOC_DIR}/examples ] || mkdir -m 0755 -p ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} pgsql-*.cf ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} vmm.cfg ${DOC_DIR}/examples

./update_tables_0.3.x-0.4.py
./update_config_0.3.x-0.4.py

echo
echo "Don't forget to check ${PREFIX}/etc/vmm.cfg"
echo "and modify: ${PF_CONFDIR}/pgsql-*.cf files."
for CF in ${CFS}; do
    echo " * ${PF_CONFDIR}/pgsql-${CF}.cf"
done
echo
