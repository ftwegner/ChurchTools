# Konfiguration der Funktion Erweiterte Führungszeugnisse

Stelle sicher, dass die ChurchTools Utilities korrekt [installiert](../index.md#installation) und [konfiguriert](../index.md#konfiguration) sind. Dann erst führe die Schritte hier aus.

Die Konfiguration der Funktion Erweiterte Führungszeugnisse besteht aus drei Teilen

1. Konfiguration in ChurchTools Stammdaten
2. Einrichten einer ChurchTools Gruppe für die VerwalterInnen der Führungszeugnisse
3. Anpassen der Variablen im Code

## 1. Konfiguration der ChurchTools Stammdaten

Es werden zwei neue Felder in den `Stammdaten` der Personen benötigt im Abschnitt `Personenfelder`, die Informationen zu den Führungszeugnissen haben.

1. **Erweitertes Führungszeugnis benötigt**
Ein Ja-Nein-Feld, das per Default "Nein" ist (kein Haken gesetzt). Nur bei den Personen, die ein erweitertes Führungszeugnis benötigen, wird der Haken hier gesetzt, so dass der Wert "Ja" ist.
    * Bezeichnung: `Erweitertes Führungszeugnis benötigt`
    * Kürzel: `Führungszeugnis benötigt`
    * Feldkategorie: `Information`
    * Feldtyp: `Ja-Nein-Feld`
    * Tabellenspalte: `ef_benoetigt` (dieser Wert kann in `config.py` angepasst werden, falls das Feld bereits existiert)
    * HTML-Darstellung des Zeilenendes: `<br/>`
    * Sicherheitslevel: `Stufe 4 (Sehr hoch)`
    * Sortierung: `10`

2. **Erstellung des erweiterten Führungszeugnisses**
Wenn ein erweitertes Führungszeugnis vorgelegt wurde, wird hier das Datum des Führungszeugnisses eingetragen.
    * Bezeichnung: `Erstellung des erweiterten Führungszeugnisses`
    * Kürzel: `Erstellung`
    * Feldkategorie: `Information`
    * Feldtyp: `Datumsfeld`
    * Tabellenspalte: `ef_datum` (dieser Wert kann in `config.py` angepasst werden, falls das Feld bereits existiert)
    * HTML-Darstellung des Zeilenendes: `<br/>`
    * Sicherheitslevel: `Stufe 4 (Sehr hoch)`
    * Sortierung: `11`

## 2. Gruppe für VerwalterInnen der Führungszeugnisse

Damit das Script funktionert wird eine Gruppe benötigt, in der der Status gepostet werden soll. Diese Gruppe muss aus Datenschutzgründen versteckt sein und nur für die Gruppenmitglieder sichtbar sein.

In ChurchTools wird eine Gruppe vom Typ `Merkmal` (zum Beispiel mit dem Namen `Führungszeugnis-Verantwortliche`) gebraucht. Personen in dieser Gruppe dürfen Daten zu den Führungszeugnissen sehen und bearbeiten. Das können die PastorInnen und bestimmte MitarbeiterInnen sein wie hauptamtliche Jugend-Verantwortliche oder Vorsitzende des Ehrenamtlichenasusschusses.

Die Gruppe erhält die folgenden Berechtigungen in Bereich `Personen`:
* `Personen bearbeiten` - write access
* `Personendaten sehen bis Sicherheitslevel Stufe 4 (Sehr hoch)` - security level person(4)

Für diese Gruppe wir die Funktion `Beiträge` aktiviert.

## 3. Anpassung der Variablen im Code

In der Datei `config.py` müssen die Variablen angepasst werden:
```
# Für die Funktion der erweiterten Führuzngszeugnisse
# -----------------------------------------------------------------------
# ID der Gruppe (Merkmal) der Verantwortlichen für die Führungszeugnisse
GROUP_ID = 153

# Name der Tabellenspalte, die anzeigt, dass ein Mitarbeiter ein Führungszeugnis benötigt
needs_ef_col = "ef_benoetigt"

# Name der Tabellenspalte, die das Datum des Führungszeugnisses enthält
ef_date_col = "ef_datum"

# Wieviele Jahre ist ein Führungszeugnis gültig
ef_valid_years = 3

# Wieviele Monate vor Ablauf eines Führungszeugnisses soll gewarnt werden
ef_warn_months = 3

# SMTP Server Konfiguration für den Web.de Emaildienst
# Du kannst den Server und Port bei Bedarf für andere Dienste anpassen
use_email = True  # Wenn True wird eine Email gesendet
smtp_server = 'smtp.web.de'
smtp_port = 587  # Nutze 587 für TLS
smtp_username = 'frank.wegner@web.de' # Das assword ist in der Umgebungsvariablen SMTP_PASSWORD
email_recipients = 'frank.wegner@web.de' # Komma-separierte Liste der Empfänger
# -----------------------------------------------------------------------
```