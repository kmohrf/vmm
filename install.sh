#!/bin/sh
# $Id$
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
MAN1DIR=${PREFIX}/share/man/man1
MAN5DIR=${PREFIX}/share/man/man5
DOCS="ChangeLog COPYING INSTALL README"

case "$(uname -s)" in
    'OpenBSD' | 'NetBSD')
        INSTALL_OPTS="-g 0 -o 0 -p"
        INSTALL_OPTS_CF="-b -m 0640 -g ${PF_GID} -o 0 -p"
        ;;
    *)
        INSTALL_OPTS="-g 0 -o 0 -p -v"
        INSTALL_OPTS_CF="-b -m 0640 -g ${PF_GID} -o 0 -p -v"
        ;;
esac

if [ $(id -u) -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

python setup.py install --prefix ${PREFIX}
python setup.py clean --all >/dev/null

install -b -m 0600 ${INSTALL_OPTS} vmm.cfg ${PREFIX}/etc/
install ${INSTALL_OPTS_CF} pgsql-*.cf ${PF_CONFDIR}/
install -m 0700 ${INSTALL_OPTS} vmm ${PREFIX}/sbin

[ -d ${LOCALE_DIR} ] || mkdir -m 0755 -p ${LOCALE_DIR}
cd po
for po in $(ls -1 *.po); do
    lang=$(basename ${po} .po)
    ddir=${LOCALE_DIR}/${lang}/LC_MESSAGES
    [ -d ${ddir}  ] || mkdir -m 0755 -p ${ddir}
    msgfmt -o ${LOCALE_DIR}/${lang}/LC_MESSAGES/vmm.mo ${po}
done
cd -

[ -d ${MAN1DIR} ] || mkdir -m 0755 -p ${MAN1DIR}
install -m 0644 ${INSTALL_OPTS} vmm.1 ${MAN1DIR}

[ -d ${MAN5DIR} ] || mkdir -m 0755 -p ${MAN5DIR}
install -m 0644 ${INSTALL_OPTS} vmm.cfg.5 ${MAN5DIR}

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
