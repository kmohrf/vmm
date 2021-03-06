#!/bin/sh
#
# Installation script for the Virtual Mail Manager
# run: ./install.sh

LANG=C
PATH=/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
PREFIX=/usr/local

PF_CONFDIR=$(postconf -h config_directory)
PF_GID=$(id -g $(postconf -h mail_owner))
LOCALE_DIR=${PREFIX}/share/locale
DOC_DIR=${PREFIX}/share/doc/vmm
if [ ${PREFIX} = "/usr" ]; then
    MANDIR=${PREFIX}/share/man
    SYSCONFDIR=/etc
else
    MANDIR=${PREFIX}/man
    SYSCONFDIR=${PREFIX}/etc
fi
DOCS="ChangeLog Configure.Dovecot_2 COPYING INSTALL NEWS README"

INSTALL_OPTS="-g 0 -o 0 -p"
INSTALL_OPTS_CF="-b -m 0640 -g ${PF_GID} -o 0 -p"

if [ $(id -u) -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

python setup.py -q install --force --prefix ${PREFIX}
python setup.py clean --all >/dev/null

[ -d ${SYSCONFDIR} ] || mkdir -m 0755 -p ${SYSCONFDIR}
install -b -m 0600 ${INSTALL_OPTS} vmm.cfg ${SYSCONFDIR}/
install ${INSTALL_OPTS_CF} postfix/pgsql-*.cf ${PF_CONFDIR}/
install -m 0700 ${INSTALL_OPTS} vmm ${PREFIX}/sbin

[ -d ${LOCALE_DIR} ] || mkdir -m 0755 -p ${LOCALE_DIR}
cd po
for po in $(ls -1 *.po); do
    lang=$(basename ${po} .po)
    ddir=${LOCALE_DIR}/${lang}/LC_MESSAGES
    [ -d ${ddir}  ] || mkdir -m 0755 -p ${ddir}
    msgfmt -o ${LOCALE_DIR}/${lang}/LC_MESSAGES/vmm.mo ${po}
done
cd - >/dev/null

cd man
[ -d ${MANDIR}/man1 ] || mkdir -m 0755 -p ${MANDIR}/man1
install -m 0644 ${INSTALL_OPTS} man1/vmm.1 ${MANDIR}/man1

[ -d ${MANDIR}/man5 ] || mkdir -m 0755 -p ${MANDIR}/man5
install -m 0644 ${INSTALL_OPTS} man5/vmm.cfg.5 ${MANDIR}/man5
cd - >/dev/null

[ -d ${DOC_DIR} ] || mkdir -m 0755 -p ${DOC_DIR}
for DOC in ${DOCS}; do
    install -m 0644 ${INSTALL_OPTS} ${DOC} ${DOC_DIR}
done

[ -d ${DOC_DIR}/examples ] || mkdir -m 0755 -p ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} postfix/pgsql-*.cf ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} vmm.cfg ${DOC_DIR}/examples

echo
echo "Don't forget to edit ${PREFIX}/etc/vmm.cfg - or run: vmm cf"
echo "and ${PF_CONFDIR}/pgsql-*.cf files."
echo
