=========
 vmm.cfg
=========

---------------------------
Konfigurationsdatei für vmm
---------------------------

:Author:         Pascal Volk <neverseen@users.sourceforge.net>
:Date:           |today|
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
|vmm(1)|_ liest seine Konfigurationsparameter aus der Datei *vmm.cfg*.

Die Konfigurationsdatei ist in mehrere Sektionen unterteilt. Jede Sektion
wird mit dem in eckigen Klammern '**[**' und '**]**' eingefassten Namen der
Sektion eingeleitet, gefolgt von '*Option* = *Wert*' Einträgen.

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

Die meisten Optionen haben einen Vorgabewert. Dieser ist nach dem Namen der
Option in Klammern angegebenen. Um den Vorgabewert einer Option zu
verwenden, wird die entsprechende Zeile entweder mit **#** oder **;**
auskommentiert oder die Zeile wird einfach aus der *vmm.cfg* entfernt.

Eine minimale *vmm.cfg* könnte so aussehen::

  [database]
  user = ich
  pass = xxxxxxxx

  [misc]
  dovecot_version = 1.2.11


SUCHREIHENFOLGE
---------------
Standardmäßig sucht |vmm(1)|_ die *vmm.cfg* in folgenden Verzeichnissen,
in der angegebenen Reihenfolge:

  | */root*
  | */usr/local/etc*
  | */etc*

Die zuerst gefundene Datei wird verwendet.


SEKTIONEN
=========
Im Folgenden werden die Sektionen der *vmm.cfg* und deren Optionen
beschrieben.


ACCOUNT
-------
Die Optionen der Sektion **account** legen Konto-spezifische Einstellungen
fest.

.. _account.delete_directory:

``delete_directory (Vorgabe: false)`` : *Boolean*
  Bestimmt das Verhalten von |vmm(1)|_ beim Löschen eines Kontos
  (|userdelete|_). Wenn der Wert dieser Option *true* ist, wird das
  Home-Verzeichnis des zu löschenden Anwenders rekursiv gelöscht.

.. _account.directory_mode:

``directory_mode (Vorgabe: 448)`` : *Int*
  Zugriffsbits des Home-Verzeichnisses, sowie aller enthaltenen
  Verzeichnisse, in Dezimal-Schreibweise (Basis 10).

  | Beispiel: 'drwx------' -> oktal 0700 -> dezimal 448

.. _account.disk_usage:

``disk_usage (Vorgabe: false)`` : *Boolean*
  Legt fest, ob die Festplattenbelegung des Maildirs eines Benutzers jedes
  Mal mit **du**\(1) ermittelt und mit den Konto-Informationen ausgegeben
  werden soll.

  Bei umfangreichen Maildirs kann das langsam sein. Falls Sie Quotas
  aktiviert haben, wird der **vmm**-Unterbefehl |userinfo|_ ebenfalls die
  aktuelle Quota-Nutzung des Kontos mit ausgegeben. Sie können auch eines
  der optionalen Argumente **du** oder **full** an |userinfo|_ übergeben,
  um sich die aktuelle Festplattenbelegung anzeigen zu lassen.

.. _account.imap:

``imap (Vorgabe: true)`` : *Boolean*
  Bestimmt, ob sich neu angelegte Benutzer per IMAP anmelden können sollen.

.. _account.password_length:

``password_length (Vorgabe: 8)`` : *Int*
  Diese Option legt die Anzahl der Zeichen für automatisch erzeugte
  Passwörter fest. Alle Werte kleiner als 8 werden auf 8 erhöht.

.. _account.pop3:

``pop3 (Vorgabe: true)`` : *Boolean*
  Bestimmt, ob sich neu angelegte Benutzer per POP3 anmelden können sollen.

.. _account.random_password:

``random_password (Vorgabe: false)`` : *Boolean*
  Mit dieser Option wird bestimmt , ob **vmm** ein zufälliges Passwort
  generieren soll, wenn kein Passwort an den Unterbefehl |useradd|_
  übergeben wurde. Ist der Wert dieser Option *false*, wird **vmm** Sie
  auffordern, ein Passwort für den neun Account einzugeben.

  Sie können die Länge für automatisch generierte Passwörter mit der Option
  |account.password_length|_ konfigurieren.

.. _account.sieve:

``sieve (Vorgabe: true)`` : *Boolean*
  Bestimmt, ob sich neu angelegte Benutzer per ManageSieve anmelden können
  sollen.

.. _account.smtp:

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
In der **bin**-Sektion werden die Pfade zu den von |vmm(1)|_ benötigten
Binaries angegeben.

.. _bin.dovecotpw:

``dovecotpw (Vorgabe: /usr/sbin/dovecotpw)`` : *String*
  Der absolute Pfad zum dovecotpw Binary. Geben Sie den absoluten Pfad zum
  **doveadm**\(1) Binary an, falls Sie Dovecot v2.0 verwenden. Dieses Binary
  wird zur Hash-Erzeugung verwendet, wenn |misc.password_scheme|_ einen der
  nachfolgenden Werte hat: 'CRAM-MD5', 'HMAC-MD5', 'LANMAN', 'OTP' 'RPA'
  oder 'SKEY'. Dieses Binary wird auch benötigt, wenn Ihre
  Python-Installation einen der folgenden Hash-Algorithmen nicht
  unterstützt:

  * md4 (hashlib + OpenSSL oder PyCrypto) verwendet für die
    Passwort-Schemen: 'PLAIN-MD4' und 'NTLM'
  * sha256 (hashlib oder PyCrypto >= 2.1.0alpha1) verwendet für die
    Passwort-Schemen: 'SHA256' und 'SSHA256'
  * sha512 (hashlib) verwendet für die Passwort-Schemen: 'SHA512' und
    'SSHA512'

.. _bin.du:

``du (Vorgabe: /usr/bin/du)`` : *String*
  Der absolute Pfad zu **du**\(1). Dieses Binary wird verwendet, wenn die
  Festplattenbelegung eines Kontos ermittelt wird.

.. _bin.postconf:

``postconf (Vorgabe: /usr/sbin/postconf)`` : *String*
  Der absolute Pfad zu Postfix' |postconf(1)|_. Dieses Binary wird
  verwendet, wenn |vmm(1)|_ diverse Postfix-Einstellungen prüft, zum
  Beispiel das |virtual_alias_expansion_limit|_.

Beispiel::

  [bin]
  dovecotpw = /usr/sbin/dovecotpw
  du = /usr/bin/du
  postconf = /usr/sbin/postconf


DATABASE
--------
Die **database**-Sektion wird verwendet, um die für den Datenbankzugriff
benötigten Optionen festzulegen.

.. _database.host:

``host (Vorgabe: localhost)`` : *String*
  Der Hostname oder die IP-Adresse des Datenbank-Servers.

.. _database.name:

``name (Vorgabe: mailsys)`` : *String*
  Der Name der zu verwendenden Datenbank.

.. _database.pass:

``pass (Vorgabe: Nichts)`` : *String*
  Das Passwort des Datenbank-Benutzers.

.. _database.user:

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
In der **domain**-Sektion werden Domain-spezifische Informationen
konfiguriert.

.. _domain.auto_postmaster:

``auto_postmaster (Vorgabe: true)`` : *Boolean*
  Ist der Wert dieser Option *true*, wird |vmm(1)|_ beim Anlegen einer
  Domain (|domainadd|_) automatisch einen postmaster-Account erstellen.

.. _domain.delete_directory:

``delete_directory (Vorgabe: false)`` : *Boolean*
  Bestimmt, ob beim Löschen einer Domain (|domaindelete|_) das Verzeichnis
  der zu löschenden Domain, inklusive aller Anwender-Verzeichnisse, rekursiv
  gelöscht werden soll.

.. _domain.directory_mode:

``directory_mode (Vorgabe: 504)`` : *Int*
  Zugriffsbits des Domain-Verzeichnisses in Dezimal-Schreibweise (Basis 10).

  | Beispiel: 'drwxrwx---' -> oktal 0770 -> dezimal 504

.. _domain.force_deletion:

``force_deletion (Vorgabe: false)`` : *Boolean*
  Erzwingt das Löschen aller zugeordneten Konten und Aliase beim Löschen
  einer Domain (|domaindelete|_).

Beispiel::

  [domain]
  auto_postmaster = true
  delete_directory = false
  directory_mode = 504
  force_deletion = false


MAILBOX
-------
In der **mailbox**-Sektion werden die für die Erstellung von Mailboxen
erforderlichen Optionen festgelegt. Die INBOX wird in jedem Fall erstellt.

.. _mailbox.folders:

``folders (Vorgabe: Drafts:Sent:Templates:Trash)`` : *String*
  Eine durch Doppelpunkten getrennte Liste mit Mailboxnamen die
  erstellt werden sollen. Sollen keine zusätzlichen Mailboxen angelegt werden,
  ist dieser Optionen ein einzelner Doppelpunkt ('**:**') als Wert zuzuweisen.

  Sollen Verzeichnisse mit Unterverzeichnissen angelegt werden, ist ein
  einzelner Punkt ('**.**') als Separator zu verwenden.

  Sollen Mailboxen mit internationalisierten Namen erstellt werden (zum
  Beispiel: 'Wysłane' oder 'Gelöschte Objekte'), ist der Name UTF-8 kodiert
  anzugeben. |vmm(1)|_ wird die internationalisierten Mailboxnamen in eine
  modifizierten Variante des UTF-7-Zeichensatzes (siehe auch: :RFC:`3501`,
  Sektion 5.1.3) konvertieren.

.. _mailbox.format:

``format (Vorgabe: maildir)`` : *String*
  Das zu verwendende Format der Mailbox der Benutzer. Abhängig von der
  verwendeten Dovecot-Version, stehen bis zu drei Formate zur Verfügung:

    ``maildir``
      seit Dovecot v1.0.0
    ``mdbox``
      seit Dovecot v2.0.beta1
    ``sdbox``
      seit Dovecot v2.0.rc3

.. _mailbox.root:

``root (Vorgabe: Maildir)`` : *String*
  Name des Mailbox-Wurzelverzeichnisses im Home-Verzeichnis des jeweiligen
  Benutzers. Übliche Namen, je nach verwendetem |mailbox.format|_, sind:
  **Maildir**, **mdbox** oder **sdbox**.

Beispiel::

  [mailbox]
  folders = Drafts:Sent:Templates:Trash:Lists.Dovecot:Lists.Postfix
  format = maildir
  root = Maildir


MISC
----
In der **misc**-Sektion werden verschiedene Einstellungen festgelegt.

.. _misc.base_directory:

``base_directory (Vorgabe: /srv/mail)`` : *String*
  Alle Domain-Verzeichnisse werden innerhalb dieses Basis-Verzeichnisses
  angelegt.

.. _misc.crypt_blowfish_rounds:

``crypt_blowfish_rounds (Vorgabe: 5)`` : *Int*
  Anzahl der Verschlüsselungsdurchgänge für das *password_scheme*
  **BLF-CRYPT**.

  Der Wert muss im Bereich von **4** - **31** liegen.

.. _misc.crypt_sha256_rounds:

``crypt_sha256_rounds (Vorgabe: 5000)`` : *Int*
  Anzahl der Verschlüsselungdurchgänge für das *password_scheme*
  **SHA256-CRYPT**.

  Der Wert muss im Bereich von **1000** - **999999999** liegen.

.. _misc.crypt_sha512_rounds:

``crypt_sha512_rounds (Vorgabe: 5000)`` : *Int*
  Anzahl der Verschlüsselungsdurchgänge für das *password_scheme*
  **SHA256-CRYPT**.

  Der Wert muss im Bereich von **1000** - **999999999** liegen.

.. _misc.password_scheme:

``password_scheme (Vorgabe: CRAM-MD5)`` : *String*
  Das zu verwendende Passwort-Schema. Um eine Liste aller verfügbaren
  Passwort-Schemata zu erhalten, für Sie das Kommando **dovecotpw -l**
  (Dovecot v1.x) oder **doveadm pw -l** (Dovecot v2.0) aus.

.. _misc.transport:

``transport (Vorgabe: dovecot:)`` : *String*
  Der Standard-Transport aller Domains und Konten. Siehe auch:
  |transport(5)|_

.. _misc.dovecot_version:

``dovecot_version (Vorgabe: Nichts)`` : *String*
  Die eingesetzten Dovecot-Version. (siehe: **dovecot --version**).

  Wenn das Kommando **dovecot --version** zum Beispiel
  *2.0.beta4 (8818db00d347)* ausgibt, ist dieser Option der Wert
  **2.0.beta4** zuzuweisen.

Beispiel::

  [misc]
  base_directory = /srv/mail
  crypt_sha512_rounds = 10000
  password_scheme = SHA512-CRYPT
  transport = dovecot:
  dovecot_version = 2.0.beta4


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
|vmm(1)|_


COPYING
=======
vmm und die dazugehörigen Manualseiten wurden von Pascal Volk geschrieben
und sind unter den Bedingungen der BSD Lizenz lizenziert.

.. include:: ../../substitute_links.rst
.. include:: ../../substitute_links_5.rst
