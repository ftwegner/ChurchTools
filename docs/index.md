# ChurchTools Utilities

Die ChurchTools Utilities bestehen aus folgender Funktion:

1. [Erweitere Führungszeugnisse](erweiterte-fuehrungszeugnisse/index.md)

Weitere Funktionen können späterhinzukommen.

Source code auf GitHub: [https://github.com/ftwegner/ChurchTools](https://github.com/ftwegner/ChurchTools)

## Installation

Stelle sicher, dass [Python](https://www.python.org/downloads) und [git](https://git-scm.com/downloads) auf deinem Rechner installiert und eingerichtet sind.

Um das [ChurchTools Utilities Git-Repository](https://github.com/ftwegner/ChurchTools) auf deinen Windows-Rechner zu klonen, folge diesen Schritten:

1. **Öffne die PowerShell oder Eingabeaufforderung**:
   Drücke `Win + R`, gib `powershell` oder `cmd` ein und drücke `Enter`.

2. **Navigiere zu dem Ordner, in dem du das Repository speichern möchtest**

3. **Klonen des Repositories**:
   Führe den folgenden Befehl aus:
   ```bash
   git clone https://github.com/ftwegner/ChurchTools.git
   ```

4. **Wechsle in das geklonte Verzeichnis**:
   ```bash
   cd ChurchTools
   ```

5. **Erstelle eine virtuelle Python Umngebung**:
   ```
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
Das Repository ist jetzt auf deinem Rechner verfügbar. Du kannst es in [Visual Studio Code](https://code.visualstudio.com/docs/setup/setup-overview) (verfügbar für Windows/Mac/Linux/Raspberry Pi) oder einem anderen Werkzeug deiner Wahl öffnen, um es im nächsten SChritt zu konfigurieren.

## Konfiguration

Die Konfiguration besteht aus zwei Teilen:

1. Access Token holen
2. Umgebungsvariable `CHURCHTOOLS_TOKEN` setzen
3. API Base URL setzen

### 1. Access Token
Damit die ChurchTools Utilities funktioneren, muss auf dem Rechner, auf dem die Utilities laufen, die Umgebungsvariable `CHURCHTOOLS_TOKEN` mit dem ChurchTools Access Token angelegt sein.

#### ChurchTools Access Token besorgen
In ChurchTools Web bekommst du das Token in `Personen & Gruppen > Personenliste > „Person A“ > Berechtigungen > Login-Token`

### 2. Umgebungsvariable `CHURCHTOOLS_TOKEN` setzen

#### Windows
Um die Umgebungsvariable `CHURCHTOOLS_TOKEN` für den aktuellen Benutzer in Windows zu setzen, führe die folgenden Schritte aus:

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

5. **Überprüfen, ob die Variable gesetzt ist**
Führe in der PowerShell den folgenden Befehl aus, um zu überprüfen, ob die Umgebungsvariable korrekt gesetzt wurde:
```powershell
echo $env:CHURCHTOOLS_TOKEN
```
#### Linux und Raspberry Pi
Um eine Umgebungsvariable permanent für einen Benutzer auf einem Linux System oder einem einem Raspberry Pi zu setzen, kannst du die `.bashrc`-Datei des Benutzers bearbeiten. Hier sind die Schritte:

1. **Öffne die `.bashrc`-Datei und füge die Umgebungsvariable hinzu**
Füge am Ende der Datei die folgende Zeile hinzu und speichere die Datei:
```bash
export CHURCHTOOLS_TOKEN="<token value here>"
```

2. **Aktualisiere die Umgebungsvariablen**
Lade die `.bashrc`-Datei neu, damit die Änderungen wirksam werden:
```bash
source ~/.bashrc
```

3. **Überprüfe die Umgebungsvariable**
Prüfe, ob die Umgebungsvariable korrekt gesetzt wurde:
```bash
echo $CHURCHTOOLS_TOKEN
```

Wenn der Token angezeigt wird, ist die Umgebungsvariable korrekt gesetzt.

### 2. API Base URL
Setze die `BASE URL` in der Datei `config.py` auf den Wert für deine Kirchengemeinde:
```
# Base URL der ChurchTools Instanz API
BASE_URL = "https://volksdorf.church.tools/api"
```

### Nächste Schritte
1. Führe die Konfiguration der einzelen Funktionen durch:
   * [Erweiterte Führungszeugnisse](erweiterte-fuehrungszeugnisse/index.md)
2. Gib mir Feedback.
