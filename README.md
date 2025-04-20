# Erweiterte Führungszeugnisse in ChurchTools

Für bestimmte MitarbeiterInnen einer Kirchengemeinde wird oft ein erweitertes Führungszeugnis benötigt. Dieses ist 3 Jahre lang gültig.

Dieses Script erzeugt einen Beitrag in einer Gruppe von Verantwortlichen, die sich um Führungszeugnisse kümmern, und informiert über den Status der erweiterten Führungszeugnisse. Es wird empfohlen, dieses Script einmal pro Woche auszuführen. Idealerweise geschieht dies automatisch über den Windows Task Scheduler oder einen cron Job.

Der generierte Beitrag enthält eine Liste der MitabreiterInnen, mit den folgenden Kategorien (Ein Beispiel vom April 2025):

> **Status der erweiterten Führungszeugnisse**
>
> Ein erweitertes Führungszeugnis fehlt für:
> - Vorname1 Nachname1
>
> Das erweiterte Führungszeugnis ist nicht mehr gültig für:
> - Vorname2 Nachname2: Das Führungszeugnis vom 1. Januar 2021 ist am 1. Januar 2024 abgelaufen.
>
> Das erweiterte Führungszeugnis wird innerhalb von 3 Monaten ungültig für:
> - Vorname3 Nachname3: Das Führungszeugnis vom 1. Mai 2022 läuft am 1. Mai 2025 ab.
>
> Das erweiterte Führungszeugnis ist ok für:
> - Vorname4 Nachname4: Das Führungszeugnis vom 12. März 2024 ist bis zum 12. März 2027 gültig.
> - Vorname5 Nachname5: Das Führungszeugnis vom 1. März 2025 ist bis zum 1. März 2028 gültig.

Wenn dieses Script ausgeführt wird, werden zunächst eventuell vorhandene Beiträge in dieser Gruppe mit demselben Titel "Status der erweiterten Führungszeugnisse"
gelöscht. Dann wird der neue Beitrag erzeugt und veröffentlicht. So ist immer genau ein Beitrag mit dem Titel "Status der erweiterten Führungszeugnisse" in dieser Gruppe vorhanden.

## Voraussetzungen

Damit das Script funktionert wird eine Gruppe benötigt, in der der Status gepostet werden soll. Diese Gruppe muss aus Datenschutzgründen versteckt sein und nur für die Gruppenmitglieder sichtbar sein.

Wir brauchen zwei Felder in den ChurchTools Personen Stammdaten, die Informationen zu den Führungszeugnissen haben.

Auf dem Rechner, auf dem das Skript läuft muss die Umgebungsvariable `CHURCHTOOLS_TOKEN` mit dem ChurchTools Access Token angelegt sein. In ChurchTools Web bekommst du das Token in `Personen & Gruppen > Personenliste > „Person A“ > Berechtigungen > Login-Token`

### Eine Gruppe (Merkmal) für Personen, die Führungszeugnisse verwalten

In ChurchTools wird eine Gruppe (Merkmal) (zum Beispiel mit dem Namen "Führungszeugnis-Verantwortliche") gebraucht. Personen in dieser Gruppe dürfen Daten zu den Führungszeugnissen sehen und bearbeiten. Das können die PastorInnen und bestimmte MitarbeiterInnen sein wie hauptamtliche Jugend-Verantwortliche oder Vorsitzende des Ehrenamtlichenasusschusses.

Die Gruppe erhält die folgenden Berechtigungen in Bereich Personen:
Personen bearbeiten - write access
Personendaten sehen bis Sicherheitslevel Stufe 4 (Sehr hoch) - security level person(4)

Für diese Gruppe wir die Funktion "Beiträge" aktiviert.


### Neue Felder in Stammdaten für Personen
Es werden zwei neue Felder in den Stammdaten der Personen benötigt im Abschnitt "Personenfelder"

#### Erweitertes Führungszeugnis benötigt
Ein Ja-Nein-Feld, das per Default "Nein" ist (kein Haken gesetzt). Nur bei den Personen, die ein erweitertes Führungszeugnis benötigen, wird der Haken hier gesetzt, so dass der Wert "Ja" ist.

Bezeichnung: Erweitertes Führungszeugnis benötigt<br/>
Kürzel: Führungszeugnis benötigt<br/>
Feldkategorie: Information<br/>
Feldtyp: Ja-Nein-Feld<br/>
Tabellenspalte: ef_benoetigt (dieser Wert kann im Code angepasst werden, falls das Feld bereits existiert)<br/>
HTML-Darstellung des Zeilenendes: <br/>
Sicherheitslevel: Stufe 4 (Sehr hoch)<br/>
Sortierung: 10

#### Erstellung des erweiterten Führungszeugnisses
Wenn ein erweitertes Führungszeugnis vorgelegt wurde, wird hier das Datum des Führungszeugnisses eingetragen.

Bezeichnung: Erstellung des erweiterten Führungszeugnisses<br/>
Kürzel: Erstellung<br/>
Feldkategorie: Information<br/>
Feldtyp: Datumsfeld<br/>
Tabellenspalte: ef_datum (dieser Wert kann im Code angepasst werden, falls das Feld bereits existiert)<br/> 
Sicherheitslevel: Stufe 4 (Sehr hoch)<br/>
Sortierung: 11

WICHTIG:
Am Anfang der Datei `erweiterte-fuehrungszeugnisse.py` müssen die Variablen angepasst werden:
```
# ChurchTools Instanz spezifische Variablen, die angepasst werden müssen
# ----------------------------------------------------------------------
# Base URL der ChurchTools Instanz API
CHURCHTOOLS_BASE_URL = "https://volksdorf.church.tools/api"

# ID der Gruppe (Merkmal) der Verantwortlichen für die Führungszeugnisse, in der die Posts veröffentlicht werden sollen
GROUP_ID = 153

# Name der Tabellenspalte, die anzeigt, dass ein Mitarbeiter ein erweitertes Führungszeugnis benötigt
# Die ist ein Ja-Nein-Feld
needs_ef_col = "ef_benoetigt"

# Name der Tabellenspalte, die das Datum des Führungszeugnisses enthält 
# Dies ist ein Datumsfeld
ef_date_col = "ef_datum"
# -----------------------------------------------------------------------
```


### Umgebungsvariable

ChurchTools Token
CHURCHTOOLS_TOKEN = (dein Token)

#### Umgebungsvariable setzen
Um die Umgebungsvariable `CHURCHTOOLS_TOKEN` für den aktuellen Benutzer in Windows zu setzen, kannst du die folgenden Schritte ausführen:

Um die Umgebungsvariable dauerhaft für den Benutzer zu setzen, kannst du sie in der Windows-Umgebungsvariablenkonfiguration hinzufügen:

1. **Öffne die Umgebungsvariablen-Einstellungen**:
   - Drücke `Win + R`, gib `sysdm.cpl` ein und drücke `Enter`.
   - Gehe zum Tab **Erweitert** und klicke auf **Umgebungsvariablen**.

2. **Neue Benutzer-Umgebungsvariable hinzufügen**:
   - Klicke unter **Benutzervariablen für frank** auf **Neu**.
   - Setze den Namen der Variablen auf `CHURCHTOOLS_TOKEN`.
   - Setze den Wert der Variablen auf deinen Token.

3. **Speichern und Schließen**:
   - Klicke auf **OK**, um die Änderungen zu speichern.
   - Schließe alle Dialoge.

4. **PowerShell neu starten**:
   Starte die PowerShell neu, damit die Änderungen wirksam werden.

**Überprüfen, ob die Variable gesetzt ist**
Führe in der PowerShell den folgenden Befehl aus, um zu überprüfen, ob die Umgebungsvariable korrekt gesetzt wurde:
```powershell
echo $env:CHURCHTOOLS_TOKEN
```

Wenn der Token angezeigt wird, ist die Umgebungsvariable korrekt gesetzt. Du kannst jetzt dein Python-Skript ausführen. Wenn der Token angezeigt wird, ist die Umgebungsvariable korrekt gesetzt. Du kannst jetzt dein Python-Skript ausführen.

Um eine Umgebungsvariable permanent für einen Benutzer auf einem Raspberry Pi zu setzen, kannst du die `.bashrc`-Datei des Benutzers bearbeiten. Hier sind die Schritte:

### 1. **Öffne die `.bashrc`-Datei**
Bearbeite die `.bashrc`-Datei des Benutzers (z. B. `pi`):
```bash
nano ~/.bashrc
```

### 2. **Füge die Umgebungsvariable hinzu**
Füge am Ende der Datei die folgende Zeile hinzu:
```bash
export CHURCHTOOLS_TOKEN="<token value here>"
```

### 3. **Speichere die Datei**
- Drücke `Ctrl + O`, um die Änderungen zu speichern.
- Drücke `Enter`, um die Datei zu bestätigen.
- Drücke `Ctrl + X`, um den Editor zu schließen.

### 4. **Aktualisiere die Umgebungsvariablen**
Lade die `.bashrc`-Datei neu, damit die Änderungen wirksam werden:
```bash
source ~/.bashrc
```

### 5. **Überprüfe die Umgebungsvariable**
Prüfe, ob die Umgebungsvariable korrekt gesetzt wurde:
```bash
echo $CHURCHTOOLS_TOKEN
```

Wenn der Token angezeigt wird, ist die Umgebungsvariable korrekt gesetzt.

### Virtuelle Python Umngebung erstellen
In Windows:
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Install git auf Windows: https://git-scm.com/downloads/win

Einmal pro Woche (oder wie gewünscht) kann dies Skript über den Windows Task Scheduler oder einen Linux cron Job automatisch laufen. Der Code könnte ungefähr so aussehen:

```
"<BASE_PATH>\ChurchTools Utilities/.venv/Scripts/python.exe" "<BASE_PATH>/ChurchTools Utilities/erweiterte-fuehrungszeugnisse.py"
```
