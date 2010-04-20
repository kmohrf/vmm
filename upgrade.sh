#!/bin/sh
#
# Upgrade script for the Virtual Mail Manager
# run: ./upgrade.sh

LANG=C
PATH=/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
PREFIX=/usr/local

PF_CONFDIR=$(postconf -h config_directory)
PF_GID=$(id -g $(postconf -h mail_owner))
POSTCONF=$(which postconf)
DOVECOT_VERS=$(dovecot --version | awk -F . '{print $1 $2}')
LOCALE_DIR=${PREFIX}/share/locale
DOC_DIR=${PREFIX}/share/doc/vmm
if [ ${PREFIX} = "/usr" ]; then
    MANDIR=${PREFIX}/share/man
else
    MANDIR=${PREFIX}/man
fi
DOCS="ChangeLog COPYING NEWS INSTALL README"

INSTALL_OPTS="-g 0 -o 0 -p"
INSTALL_OPTS_CF="-b -m 0640 -g ${PF_GID} -o 0 -p"

if [ $(id -u) -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

# update config file before installing the new files.
./update_config.py
rv=$?
if [ $rv -eq 2 ]; then
	echo "please run the install.sh script"
	exit 1
elif [ $rv -eq 3 ]; then
    echo "please read the upgrade instructions at http://vmm.localdomain.org/"
    exit 1
elif [ $rv -ne 0 ]; then
    echo "Sorry, something went wrong. Please file a bug:"
    echo "https://sourceforge.net/tracker/?group_id=213727"
    exit 1
fi

python setup.py -q install --force --prefix ${PREFIX}
python setup.py clean --all >/dev/null

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

# install manual pages
cd man
[ -d ${MANDIR}/man1 ] || mkdir -m 0755 -p ${MANDIR}/man1
install -m 0644 ${INSTALL_OPTS} man1/vmm.1 ${MANDIR}/man1

[ -d ${MANDIR}/man5 ] || mkdir -m 0755 -p ${MANDIR}/man5
install -m 0644 ${INSTALL_OPTS} man5/vmm.cfg.5 ${MANDIR}/man5

for l in $(find . -maxdepth 1 -mindepth 1 -type d \! -name man\?)
do
    for s in man1 man5; do
        [ -d ${MANDIR}/${l}/${s} ] || mkdir -m 0755 -p ${MANDIR}/${l}/${s}
    done
    if [ -f ${l}/man1/vmm.1 ]; then
        install -m 0644 ${INSTALL_OPTS} ${l}/man1/vmm.1 ${MANDIR}/${l}/man1
    fi
    if [ -f ${l}/man5/vmm.cfg.5 ]; then
        install -m 0644 ${INSTALL_OPTS} ${l}/man5/vmm.cfg.5 ${MANDIR}/${l}/man5
    fi
done
cd - >/dev/null

[ -d ${DOC_DIR} ] || mkdir -m 0755 -p ${DOC_DIR}
for DOC in ${DOCS}; do
    install -m 0644 ${INSTALL_OPTS} ${DOC} ${DOC_DIR}
done

[ -d ${DOC_DIR}/examples ] || mkdir -m 0755 -p ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} postfix/pgsql-*.cf ${DOC_DIR}/examples
install -m 0644 ${INSTALL_OPTS} vmm.cfg ${DOC_DIR}/examples

