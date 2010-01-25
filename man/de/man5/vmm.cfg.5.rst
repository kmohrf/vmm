=========
 vmm.cfg
=========

---------------------------
Konfigurationsdatei für vmm
---------------------------

:Author:         Pascal Volk <neverseen@users.sourceforge.net>
:Date:           2010-01-25
:Version:        vmm-0.6.0
:Manual group:   vmm Manual
:Manual section: 5

.. contents::
    :backlinks: top
    :class: htmlout

SYNOPSIS
========
vmm.cfg

BESCHREIBUNG
============
**vmm**\(1) liest seine Konfigurationsparameter aus der Datei *vmm.cfg*.

Die Konfigurationsdatei ist in mehrere Abschnitte unterteilt. Jeder Abschnitt
wird mit dem, in eckigen Klammern '**[**' und '**]**' eingefassten, Namen des
Abschnitts eingeleitet, gefolgt von '*Option* = *Wert*' Einträgen::

    [database]
    host = 127.0.0.1

Leerräume um das Gleichheitszeichen '=' und am Ende eines Wertes werden
ignoriert.

Leerzeilen und Zeilen, die mit einer '#' oder einem ';' anfangen, werden
ignoriert.

Jeder Wert ist von einem der folgenden Datentypen:

* *Boolean* um zu bestimmen, ob etwas eingeschaltet/aktiviert (true) oder
  ausgeschaltet/deaktiviert (false) ist.

  | Mögliche Werte für *true* sind: **1**, **yes**, **true** und **on**.
  | Mögliche Werte für *false* sind: **0**, **no**, **false** und **off**.

* *Int* eine Integer-Zahl, geschrieben ohne eine gebrochene oder dezimale
  Komponente.

  | Beispielsweise **1**, **50** oder **321** sind Integer-Zahlen.

* *String* eine Folge von Buchstaben und Zahlen.

  | Zum Beispiel: '**Wort**', '**Hallo Welt**' oder '**/usr/bin/strings**'


SUCHREIHENFOLGE
---------------
Standardmäßig sucht **vmm**\(1) die *vmm.cfg* in folgenden Verzeichnissen,
in der angegebenen Reihenfolge:

    | */root*
    | */usr/local/etc*
    | */etc*

Die zuerst gefundene Datei wird verwendet.

ABSCHNITTE
==========
Im Folgenden werden die Abschnitte der *vmm.cfg* und deren Optionen
beschrieben.

ACCOUNT
-------
Die Optionen des Abschnitts **account** legen Konto-spezifische
Einstellungen fest.

``delete_directory (Vorgabe: false)`` : *Boolean*
    Bestimmt das Verhalten von **vmm**\(1) beim Löschen eines Kontos.
    Wenn der Wert dieser Option *true* ist, wird das Home-Verzeichnis des
    zu löschenden Anwenders rekursiv gelöscht.

``directory_mode (Vorgabe: 448)`` : *Int*
    Zugriffsbits des Home-Verzeichnisses, sowie aller enthaltenen
    Verzeichnisse, in Dezimal-Schreibweise (Basis 10).

    | Beispiel: 'drwx------' -> oktal 0700 -> dezimal 448

``disk_usage (Vorgabe: false)`` : *Boolean*
    Legt fest, ob die Festplattenbelegung des Maildirs eines Benutzers jedes
    Mal mit **du**\(1) ermittelt und mit den Konto-Informationen ausgegeben
    werden soll.

    Bei umfangreichen Maildirs kann das langsam sein. Falls Sie Quotas
    aktiviert haben, wird der **vmm**-Unterbefehl **userinfo** ebenfalls
    die aktuelle Quota-Nutzung des Kontos mit ausgegeben. Sie können auch
    eines der optionalen Argumente **du** oder **full** an **userinfo**
    übergeben, um sich die aktuelle Festplattenbelegung anzeigen zu lassen.

``imap (Vorgabe: true)`` : *Boolean*
    Bestimmt, ob sich neu angelegte Benutzer per IMAP anmelden können sollen.

``password_length (Vorgabe: 8)`` : *Int*
    Diese Option legt die Anzahl der Zeichen für automatisch erzeugte
    Passwörter fest. Alle Werte kleiner als 8 werden auf 8 erhöht.

``pop3 (Vorgabe: true)`` : *Boolean*
    Bestimmt, ob sich neu angelegte Benutzer per POP3 anmelden können sollen.

``random_password (Vorgabe: false)`` : *Boolean*
    Mit dieser Option wird bestimmt , ob **vmm**\(1) ein zufälliges Passwort
    generieren soll, wenn kein Passwort an den **useradd** Unterbefehl
    übergeben wurde. Ist der Wert dieser Option *false*, wird **vmm** Sie
    auffordern, ein Passwort für den neun Account einzugeben.

    Sie können die Länge für automatisch generierte Passwörter mit der
    Option **password_length** konfigurieren.

``sieve (Vorgabe: true)`` : *Boolean*
    Bestimmt, ob sich neu angelegte Benutzer per ManageSieve anmelden
    können sollen.

``smtp (Vorgabe: true)`` : *Boolean*
    Bestimmt, ob sich neu angelegte Benutzer per SMTP (SMTP AUTH) anmelden
    können sollen.

Beispiel::

    [account]
    delete_directory = false
    directory_mode = 448
    disk_usage = false
    random_password = true
    password_length = 10
    smtp = true
    pop3 = true
    imap = true
    sieve = true

BIN
---
Im **bin**-Abschnitt werden Pfade zu Binaries angegeben, die von
**vmm**\(1) benötigt werden.

``dovecotpw (Vorgabe: /usr/sbin/dovecotpw)`` : *String*
    Der absolute Pfad zum dovecotpw Binary. Dieses Binary wird zur
    Hash-Erzeugung verwendet, wenn **misc.password_scheme** einen der
    nachfolgenden Werte hat: 'SMD5', 'SSHA', 'CRAM-MD5', 'HMAC-MD5',
    'LANMAN', 'NTLM' oder 'RPA'.

``du (Vorgabe: /usr/bin/du)`` : *String*
    Der absolute Pfad zu **du**\(1). Dieses Binary wird verwendet, wenn
    die Festplattenbelegung eines Kontos ermittelt wird.

``postconf (Vorgabe: /usr/sbin/postconf)`` : *String*
    Der absolute Pfad zu Postfix' **postconf**\(1). Dieses Binary wird
    verwendet, wenn **vmm**\(1) diverse Postfix-Einstellungen prüft, zum
    Beispiel das `virtual_alias_expansion_limit`.

Beispiel::

    [bin]
    dovecotpw = /usr/sbin/dovecotpw
    du = /usr/bin/du
    postconf = /usr/sbin/postconf

CONFIG
------
Beim **config**-Abschnitt handelt es sich um einen internen
Steuerungs-Abschnitt.

``done (Vorgabe: false)`` : *Boolean*
    Diese Option hat den Wert *false*, wenn **vmm**\(1) zum ersten Mal
    installiert wurde. Wenn Sie die Datei *vmm.cfg* von Hand editieren,
    weisen Sie dieser Option abschließend den Wert *true* zu. Wird die
    Konfiguration über das Kommando **vmm configure** angepasst, wird der
    Wert dieser Option automatisch auf *true* gesetzt.

    Ist der Wert dieser Option  *false*, so startet **vmm**\(1) beim
    nächsten Aufruf im interaktiven Konfigurations-Modus.

Beispiel::

    [config]
    done = true

DATABASE
--------
Der **database**-Abschnitt wird verwendet, um die für den Datenbankzugriff
benötigten Optionen festzulegen.

``host (Vorgabe: localhost)`` : *String*
    Der Hostname oder die IP-Adresse des Datenbank-Servers.

``name (Vorgabe: mailsys)`` : *String*
    Der Name der zu verwendenden Datenbank.

``pass (Vorgabe: Nichts)`` : *String*
    Das Passwort des Datenbank-Benutzers.

``user (Vorgabe: Nichts)`` : *String*
    Der Name des Datenbank-Benutzers.

Beispiel::

    [database]
    host = localhost
    user = vmm
    pass = PY_SRJ}L/0p-oOk
    name = mailsys

DOMAIN
------
Im **domain**-Abschnitt werden Domain-spezifische Informationen konfiguriert.

``auto_postmaster (Vorgabe: true)`` : *Boolean*
    Ist der Wert dieser Option *true*, wird **vmm**\(1) beim Anlegen einer
    Domain automatisch einen postmaster-Account erstellen.

``delete_directory (Vorgabe: false)`` : *Boolean*
    Bestimmt, ob beim Löschen einer Domain das Verzeichnis einer Domain,
    inklusive aller Anwender-Verzeichnisse, rekursiv gelöscht werden soll.

``directory_mode (Vorgabe: 504)`` : *Int*
    Zugriffsbits des Domain-Verzeichnisses in Dezimal-Schreibweise (Basis
    10).

    | Beispiel: 'drwxrwx---' -> oktal 0770 -> dezimal 504

``force_deletion (Vorgabe: false)`` : *Boolean*
    Erzwingt das Löschen aller zugeordneten Konten und Aliase beim Löschen
    einer Domain.

Beispiel::

    [domain]
    auto_postmaster = true
    delete_directory = false
    directory_mode = 504
    force_deletion = false

MAILDIR
-------
Im **maildir**-Abschnitt werden die für die Maildirs erforderlichen Optionen
festgelegt.

``folders (Vorgabe: Drafts:Sent:Templates:Trash)`` : *String*
    Eine durch Doppelpunkten getrennte Liste mit Verzeichnisnamen, die
    innerhalb des Maildirs erstellt werden sollen. Sollen innerhalb des
    Maildirs keine Verzeichnisse angelegt werden, ist dieser Optionen ein
    einzelner Doppelpunkt ('**:**') als Wert zuzuweisen.

    Sollen Verzeichnisse mit Unterverzeichnissen angelegt werden, ist ein
    einzelner Punkt ('**.**') als Separator zu verwenden.

``name (Vorgabe: Maildir)`` : *String*
    Der Standard-Name des Maildir-Verzeichnisses im Verzeichnis des
    jeweiligen Anwenders.

Beispiel::

    [maildir]
    folders = Drafts:Sent:Templates:Trash:Lists.Dovecot:Lists.Postfix
    name = Maildir

MISC
----
Im **misc**-Abschnitt werden verschiedene Einstellungen festgelegt.

``base_directory (Vorgabe: /srv/mail)`` : *String*
    Alle Domain-Verzeichnisse werden innerhalb dieses Basis-Verzeichnisses
    angelegt.

``password_scheme (Vorgabe: CRAM-MD5)`` : *String*
    Das zu verwendende Passwort-Schema (siehe auch: **dovecotpw -l**).

``gid_mail (Vorgabe: 8)`` : *Int*
    Die numerische Gruppen-ID der Gruppe mail, bzw. der Gruppe aus
    `mail_privileged_group` der Datei *dovecot.conf*.

``transport (Vorgabe: dovecot:)`` : *String*
    Der Standard-Transport aller Domains und Konten. Siehe auch:
    **transport**\(5)

``dovecot_version (Vorgabe: 12)`` : *Int*
    Die verketteten Major- und Minor-Teile der eingesetzten Dovecot-Version
    (siehe: **dovecot --version**).

    Wenn das Kommando **dovecot --version** zum Beispiel *1.1.18* ausgibt,
    ist dieser Option der Wert **11** zuzuweisen.

Beispiel::

    [misc]
    base_directory = /srv/mail
    password_scheme = CRAM-MD5
    gid_mail = 8
    transport = dovecot:
    dovecot_version = 11

DATEIEN
=======
*/root/vmm.cfg*
    | Wird verwendet, falls vorhanden.
*/usr/local/etc/vmm.cfg*
    | Wird verwendet, sollte obige Datei nicht gefunden werden.
*/etc/vmm.cfg*
    | Wird verwendet, falls obengenannte Dateien nicht existieren.

SIEHE AUCH
==========
vmm(1), Programm für die Kommandozeile, um E-Mail-Domains, -Konten und -Aliase
zu verwalten.

COPYING
=======
vmm und die dazugehörigen Manualseiten wurden von Pascal Volk geschrieben
und sind unter den Bedingungen der BSD Lizenz lizenziert.

