=====
 vmm
=====

-----------------------------------------------------------------------------
Kommandozeilenprogramm zur Verwaltung von E-Mail-Domains, -Konten und -Aliase
-----------------------------------------------------------------------------

:Author:         Pascal Volk <neverseen@users.sourceforge.net>
:Date:           |today|
:Version:        vmm-0.6.0
:Manual group:   vmm Manual
:Manual section: 1

.. contents::
  :backlinks: top
  :class: htmlout

SYNOPSIS
========
vmm *Unterbefehl* *Objekt* [ *Argumente* ]


BESCHREIBUNG
============
**vmm** (a virtual mail manager) ist ein Kommandozeilenprogramm für
Administratoren/Postmaster zur Verwaltung von (Alias-) Domains, Konten und
Alias-Adressen. Es wurde entwickelt für Dovecot und Postfix mit einem
PostgreSQL-Backend.


UNTERBEFEHLE
============
Von jedem Unterbefehl gibt es jeweils eine lange und kurze Variante. Die
Kurzform ist in Klammern geschrieben. Bei beiden Formen ist die
Groß-/Kleinschreibung zu berücksichtigen.


ALLGEMEINE UNTERBEFEHLE
-----------------------
.. _configget:

``configget (cg) Option``
 Dieser Unterbefehl wird verwendet, um den aktuellen Wert der übergebenen
 *Option* anzuzeigen. Die *Option* wird in der Form *Sektion*\ **.**\ *Option*
 angegeben. Zum Beispiel: **misc.transport**.

.. _configset:

``configset (cs) Option Wert``
  Verwenden Sie diesen Unterbefehl, um einer einzelnen Konfigurations-*Option*
  einen neuen *Wert* zuzuweisen. Die *Option* wird dabei in der Form
  *Sektion*\ **.**\ *Option* angegeben. *Wert* ist der neue Wert der *Option*.

  Beispiel::

    vmm configget misc.transport
    misc.transport = dovecot:
    vmm configset misc.transport lmtp:unix:private/dovecot-lmtp
    vmm cg misc.transport
    misc.transport = lmtp:unix:private/dovecot-lmtp

.. _configure:

``configure (cf) [ Sektion ]``
  Startet den interaktiven Konfiguration-Modus für alle Sektionen der
  Konfiguration.

  Dabei wird der aktuell konfigurierte Wert einer jeden Option in eckigen
  Klammern ausgegeben. Sollte kein Wert konfiguriert sein, wird der
  Vorgabewert der jeweiligen Option in in eckigen Klammern angezeigt. Um den
  angezeigten Wert unverändert zu übernehmen, ist dieser mit der
  Eingabe-Taste zu bestätigen.

  Wurde das optionale Argument *Sektion* angegeben, werden nur die Optionen
  der angegebenen Sektion angezeigt und können geändert werden. Folgende
  Sektionen sind vorhanden:

  | - **account**
  | - **bin**
  | - **database**
  | - **domain**
  | - **maildir**
  | - **misc**

  Beispiel::

    vmm configure domain
    Verwende Konfigurationsdatei: /usr/local/etc/vmm.cfg

    * Konfigurations Sektion: „domain“
    Neuer Wert für Option directory_mode [504]:
    Neuer Wert für Option delete_directory [False]: 1
    Neuer Wert für Option auto_postmaster [True]:
    Neuer Wert für Option force_deletion [False]: on

.. _getuser:

``getuser (gu) userid``
  Wenn nur eine UserID vorhanden ist, zum Beispiel aus der Prozessliste,
  kann mit dem Unterbefehl **getuser** die E-Mail-Adresse des Users
  ermittelt werden.

  Beispiel::

    vmm getuser 70004
    Account Informationen
    ---------------------
            UID............: 70004
            GID............: 70000
            Address........: c.user@example.com

.. _listdomains:

``listdomains (ld) [ Muster ]``
  Dieser Unterbefehl listet alle verfügbaren Domains auf. Allen Domains wird
  ein Präfix vorangestellt. Entweder ein '[+]', falls es sich um eine
  primäre Domain handelt, oder ein '[-]', falls es sich um eine Alias-Domain
  handelt. Die Ausgabe kann reduziert werden, indem ein optionales *Muster*
  angegeben wird.

  Um eine Wildcard-Suche durchzuführen kann das **%**-Zeichen am Anfang
  und/oder Ende des *Musters* verwendet werden.

  Beispiel::

    vmm listdomains %example%
    Übereinstimmende Domains
    ------------------------
            [+] example.com
            [-]     e.g.example.com
            [-]     example.name
            [+] example.net
            [+] example.org

.. _help:

``help (h)``
  Dieser Unterbefehl gibt alle verfügbaren Kommandos auf der Standardausgabe
  (stdout) aus. Danach beendet sich **vmm**.

.. _version:

``version (v)``
  Gibt Versionsinformationen zu **vmm** aus.

DOMAIN UNTERBEFEHLE
-------------------
.. _domainadd:

``domainadd (da) Domain [ Transport ]``
  Fügt eine neue *Domain* in die Datenbank ein und erstellt das
  Domain-Verzeichnis.

  Ist das optionale Argument *Transport* angegeben, wird der
  Vorgabe-Transport (|misc.transport|_) aus |vmm.cfg(5)|_ für diese *Domain*
  ignoriert und der angegebene *Transport* verwendet. Der angegebene
  *Transport* ist gleichzeitig der Vorgabe-Transport für alle neuen Konten,
  die unter dieser Domain eingerichtet werden.

  Beispiele::

    vmm domainadd support.example.com smtp:mx1.example.com
    vmm domainadd sales.example.com

.. _domaininfo:

``domaininfo (di) Domain [ Details ]``
  Dieser Unterbefehl zeigt Information zur angegeben *Domain* an.

  Um detaillierte Informationen über die *Domain* zu erhalten, kann das
  optionale Argument *Details* angegeben werden. Ein möglicher Wert für
  *Details* kann eines der folgenden fünf Schlüsselwörter sein:

  ``accounts``
    um alle existierenden Konten aufzulisten
  ``aliasdomains``
    um alle zugeordneten Alias-Domains aufzulisten
  ``aliases``
    um alle verfügbaren Alias-Adressen aufzulisten
  ``relocated``
    um alle Adressen der relocated Users aufzulisten
  ``full``
    um alle oben genannten Informationen aufzulisten

  Beispiel::

    vmm domaininfo sales.example.com
    Domain Informationen
    --------------------
            Domainname.....: sales.example.com
            GID............: 70002
            Transport......: dovecot:
            Domaindir......: /home/mail/5/70002
            Aliasdomains...: 0
            Accounts.......: 0
            Aliases........: 0
            Relocated......: 0

.. _domaintransport:

``domaintransport (dt) Domain Transport [ force ]``
  Ein neuer *Transport* für die angegebene *Domain* kann mit diesem
  Unterbefehl festgelegt werden.

  Wurde das optionale Schlüsselwort **force** angegeben, so werden alle
  bisherigen Transport-Einstellungen, der in dieser Domain vorhandenen
  Konten, mit dem neuen *Transport* überschrieben.

  Andernfalls gilt der neue *Transport* nur für Konten, die zukünftig
  erstellt werden.

  Beispiel::

    vmm domaintransport support.example.com dovecot:

.. _domaindelete:

``domaindelete (dd) Domain [ force ]``
  Mit diesem Unterbefehl wird die angegebene *Domain* gelöscht.

  Sollten der *Domain* Konten, Aliase und/oder relocated User  zugeordnet
  sein, wird **vmm** die Ausführung des Befehls mit einer entsprechenden
  Fehlermeldung beenden.

  Sollten Sie sich Ihres Vorhabens sicher sein, so kann optional das
  Schlüsselwort **force** angegeben werden.

  Sollten Sie wirklich immer wissen was Sie tun, so editieren Sie Ihre
  *vmm.cfg* und setzen den Wert der Option |domain.force_deletion|_ auf
  true. Dann werden Sie beim Löschen von Domains nicht mehr wegen vorhanden
  Konten, Aliase und/oder relocated User gewarnt.


ALIAS-DOMAIN UNTERBEFEHLE
-------------------------
.. _aliasdomainadd:

``aliasdomainadd (ada) Aliasdomain Zieldomain``
  Mit diesem Unterbefehl wird der *Zieldomain* die Alias-Domain
  *Aliasdomain* zugewiesen.

  Beispiel::

    vmm aliasdomainadd example.name example.com

.. _aliasdomaininfo:

``aliasdomaininfo (adi) Aliasdomain``
  Dieser Unterbefehl informiert darüber, welcher Domain die Alias-Domain
  *Aliasdomain* zugeordnet ist.

  Beispiel::

    vmm aliasdomaininfo example.name
    Alias-Domain Informationen
    --------------------------
            Die Alias-Domain example.name gehört zu:
                * example.com

.. _aliasdomainswitch:

``aliasdomainswitch (ads) Aliasdomain Zieldomain``
  Wenn das Ziel der vorhandenen *Aliasdomain* auf eine andere *Zieldomain*
  geändert werden soll, ist dieser Unterbefehl zu verwenden.

  Beispiel::

    vmm aliasdomainswitch example.name example.org

.. _aliasdomaindelete:

``aliasdomaindelete (add) Aliasdomain``
  Wenn die Alias-Domain mit dem Namen *Aliasdomain* gelöscht werden soll,
  ist dieser Unterbefehl zu verwenden.

  Beispiel::

    vmm aliasdomaindelete e.g.example.com


KONTO UNTERBEFEHLE
------------------
.. _useradd:

``useradd (ua) Adresse [ Passwort ]``
  Mit diesem Unterbefehl wird ein neues Konto für die angegebene *Adresse*
  angelegt.

  Wurde kein *Passwort* angegeben wird **vmm** dieses im interaktiven Modus
  erfragen. Falls kein *Passwort* angegeben wurde und
  |account.random_password|_ den Wert **true** hat, wird **vmm** ein
  zufälliges Passwort generieren und auf stdout ausgeben, nachdem das Konto
  angelegt wurde.

  Beispiele::

    vmm ua d.user@example.com 'A 5ecR3t P4s5\\/\\/0rd'
    vmm ua e.user@example.com
    Neues Passwort eingeben:
    Neues Passwort wiederholen:

.. _userinfo:

``userinfo (ui) Adresse [ Details ]``
  Dieser Unterbefehl zeigt einige Informationen über das Konto mit der
  angegebenen *Adresse* an.

  Wurde das optionale Argument *Details* angegeben, werden weitere
  Informationen ausgegeben. Mögliche Werte für *Details* sind:

  ``aliases``
    um alle Alias-Adressen, mit dem Ziel *Adresse*, aufzulisten
  ``du``
    um zusätzlich die Festplattenbelegung des Maildirs eines Kontos
    anzuzeigen. Soll die Festplattenbelegung jedes Mal mit der **userinfo**
    ermittelt werden, ist in der *vmm.cfg* der Wert der Option
    |account.disk_usage|_ auf true zu setzen.
  ``full``
    um alle oben genannten Informationen anzuzeigen

.. _username:

``username (un) Adresse 'Bürgerlicher Name'``
  Der Bürgerliche Name des Konto-Inhabers mit der angegebenen *Adresse* kann
  mit diesem Unterbefehl gesetzt/aktualisiert werden.

  Beispiel::

    vmm un d.user@example.com 'John Doe'

.. _userpassword:

``userpassword (up) Adresse [ Passwort ]``
  Das *Passwort* eines Kontos kann mit diesem Unterbefehl aktualisiert
  werden.

  Wurde kein *Passwort* angegeben wird **vmm** dieses im interaktiven Modus
  erfragen.

  Beispiel::

    vmm up d.user@example.com 'A |\\/|0r3 5ecur3 P4s5\\/\\/0rd?'

.. _usertransport:

``usertransport (ut) Adresse Transport``
  Mit diesem Unterbefehl kann ein abweichender *Transport* für das Konto mit
  der angegebenen *Adresse* bestimmt werden.

  Beispiel::

    vmm ut d.user@example.com smtp:pc105.it.example.com

.. _userdisable:

``userdisable (u0) Adresse [ Service ... ]``
  Soll ein Anwender keinen Zugriff auf bestimmte oder alle Service haben, kann
  der Zugriff mit diesem Unterbefehl beschränkt werden.

  Wurde kein *Service* angegeben, werden alle Services (**smtp**, **pop3**,
  **imap**, und **sieve**) für das Konto mit der angegebenen *Adresse*
  deaktiviert.

  Andernfalls wird nur der Zugriff auf den/die angegebenen *Service*/s
  gesperrt.

  Beispiele::

    vmm u0 b.user@example.com imap pop3
    vmm userdisable c.user@example.com

.. _userenable:

``userenable (u1) Adresse [ Service ... ]``
  Um den Zugriff auf bestimmte oder alle gesperrten Service zu gewähren,
  wird dieser Unterbefehl verwendet.

  Wurde kein *Service* angegeben, werden alle Services (**smtp**, **pop3**,
  **imap**, und **sieve**) für das Konto mit der angegebenen  *Adresse*
  aktiviert.

  Andernfalls wird nur der Zugriff auf den/die angegebenen *Service*/s
  aktiviert.

.. _userdelete:

``userdelete (ud) Adresse [ force ]``
  Verwenden Sie diesen Unterbefehl um, das Konto mit der angegebenen
  *Adresse* zu löschen.

  Sollte es einen oder mehrere Aliase geben, deren Zieladresse mit der
  *Adresse* des zu löschenden Kontos identisch ist, wird **vmm** die
  Ausführung des Befehls mit einer entsprechenden Fehlermeldung beenden. Um
  dieses zu umgehen, kann das optionale Schlüsselwort **force**
  angegebenen werden.


ALIAS UNTERBEFEHLE
------------------
.. _aliasadd:

``aliasadd (aa) Alias Ziel``
  Mit diesem Unterbefehl werden neue Aliase erstellt.

  Beispiele::

    vmm aliasadd john.doe@example.com d.user@example.com
    vmm aa support@example.com d.user@example.com
    vmm aa support@example.com e.user@example.com

.. _aliasinfo:

``aliasinfo (ai) Alias``
  Informationen zu einem Alias können mit diesem Unterbefehl ausgegeben
  werden.

  Beispiel::

    vmm aliasinfo support@example.com
    Alias Informationen
    -------------------
            E-Mails für support@example.com werden weitergeleitet an:
                 * d.user@example.com
                 * e.user@example.com

.. _aliasdelete:

``aliasdelete (ad) Alias [ Ziel ]``
  Verwenden Sie diesen Unterbefehl um den angegebenen *Alias* zu löschen.

  Wurde die optionale Zieladresse *Ziel* angegeben, so wird nur diese
  Zieladresse vom angegebenen *Alias* entfernt.

  Beispiel::

    vmm ad support@example.com d.user@example.com


RELOCATED UNTERBEFEHLE
----------------------
.. _relocatedadd:

``relocatedadd (ra) alte_adresse neue_adresse``
  Um einen neuen relocated User anzulegen kann dieser Unterbefehl verwendet
  werden.

  Dabei ist *alte_adresse* die ehemalige Adresse des Benutzers, zum Beispiel
  b.user@example.com, und *neue_adresse* die neue Adresse, unter der
  Benutzer erreichbar ist.

  Beispiel::

    vmm relocatedadd b.user@example.com b-user@company.tld

.. _relocatedinfo:

``relocatedinfo (ri) alte_adresse``
  Dieser Unterbefehl zeigt die neue Adresse des relocated Users mit
  *alte_adresse*.

  Beispiel::

    vmm relocatedinfo b.user@example.com
    Relocated Informationen
    -----------------------
    Der Benutzer „b.user@example.com“ ist erreichbar unter „b-user@company.tld“

.. _relocateddelete:

``relocateddelete (rd) alte_adresse``
  Mit diesem Unterbefehl kann der relocated User mit *alte_adresse*
  gelöscht werden.

  Beispiel::

    vmm relocateddelete b.user@example.com


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
|vmm.cfg(5)|_


COPYING
=======
vmm und die dazugehörigen Manualseiten wurden von Pascal Volk geschrieben
und sind unter den Bedingungen der BSD Lizenz lizenziert.

.. include:: ../../substitute_links.rst
.. include:: ../../substitute_links_1.rst
