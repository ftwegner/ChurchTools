# Umgebungsvariablen
## ChurchTools API URL für Volksdorf
CHURCHTOOLS_BASE_URL = "https://volksdorf.church.tools/api"
## ChurchTools Token
CHURCHTOOLS_TOKEN = (dein Token)

### ChurchTools Token holen
In ChurchTools Web: Personen & Gruppen > Personenliste > „Person A“ > Berechtigungen > Login-Token

## Umgebungsvariablen setzen
Um die Umgebungsvariable `CHURCHTOOLS_TOKEN` für den aktuellen Benutzer in Windows zu setzen, kannst du die folgenden Schritte ausführen:

### **Dauerhaft für den Benutzer setzen**
Um die Umgebungsvariable dauerhaft für den Benutzer zu setzen, kannst du sie in der Windows-Umgebungsvariablenkonfiguration hinzufügen:

#### Schritte:
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

### 3. **Überprüfen, ob die Variable gesetzt ist**
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


python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
