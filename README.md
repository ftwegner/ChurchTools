# ChurchTools Utilities

Dieses Projekt enthält Python-Skripte, mit denen die Verwaltung von Vorgängen in der Kirchengemeinde mit ChurchTools vereinfacht werden kann.

## Features
1. **Erweiterte Führungszeugnisse** - Statusbericht und Warnung bei Ablauf.

## Installation

Voraussetzung: Python 3 mit `pip` und `venv`.

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt        # Linux / macOS
venv\Scripts\pip install -r requirements.txt    # Windows
```

## Konfiguration & Zugangsdaten

Das Skript liest alle Secrets aus Umgebungsvariablen — es sind **keine Passwörter im Code oder in `config.py`** hinterlegt. Auch E-Mail-Adressen und SMTP-Server werden als Umgebungsvariablen gesetzt; `config.py` enthält nur allgemeine ChurchTools-Einstellungen.

### Benötigte Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `CHURCHTOOLS_TOKEN` | API-Token für deine ChurchTools-Instanz (`https://<gemeinde>.church.tools`) |
| `USE_EMAIL` | optional: `true` → Ergebnis zusätzlich per E-Mail versenden (Standard: aus) |
| `SMTP_SERVER` | bei E-Mail-Versand: Hostname des SMTP-Servers, z. B. `smtp.example.com` |
| `SMTP_PORT` | optional: Port des SMTP-Servers (Standard: `587`, STARTTLS) |
| `SMTP_USERNAME` | bei E-Mail-Versand: Absenderadresse / Login des SMTP-Kontos |
| `SMTP_PASSWORD` | bei E-Mail-Versand: Passwort des SMTP-Kontos |
| `EMAIL_RECIPIENTS` | bei E-Mail-Versand: Komma-separierte Liste der Empfänger |

### Umgebungsvariablen setzen

Am einfachsten werden die Variablen in einer Secrets-Datei gespeichert, die nur für den eigenen Benutzer lesbar ist und vor dem Skriptstart geladen wird.

**Linux / macOS** — z. B. `~/.churchtools_secrets`:
```bash
export CHURCHTOOLS_TOKEN="dein_churchtools_api_token"
export USE_EMAIL="true"
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USERNAME="absender@example.com"
export SMTP_PASSWORD="dein_smtp_passwort"
export EMAIL_RECIPIENTS="empfaenger1@example.com,empfaenger2@example.com"
```

Datei absichern (nur für den eigenen Benutzer lesbar):
```bash
chmod 600 ~/.churchtools_secrets
```

**Windows (PowerShell)** — für die aktuelle Sitzung:
```powershell
$env:CHURCHTOOLS_TOKEN = "dein_churchtools_api_token"
$env:USE_EMAIL        = "true"
$env:SMTP_SERVER      = "smtp.example.com"
$env:SMTP_PORT        = "587"
$env:SMTP_USERNAME    = "absender@example.com"
$env:SMTP_PASSWORD    = "dein_smtp_passwort"
$env:EMAIL_RECIPIENTS = "empfaenger1@example.com,empfaenger2@example.com"
```
Dauerhaft lassen sich die Variablen über *Systemsteuerung → System → Erweiterte Systemeinstellungen → Umgebungsvariablen* setzen.

### Wo bekomme ich den ChurchTools-Token?

1. In ChurchTools einloggen → oben rechts auf das Benutzerbild klicken → **„Mein Profil"**
2. Im Profil: Reiter **„Sicherheit"** → **„API-Token"** → Token kopieren

### Automatisch ausführen (z. B. per Cron-Job)

Unter Linux / macOS lädt der Cron-Job die Secrets-Datei und startet das Skript täglich. Crontab bearbeiten mit `crontab -e`, Eintrag (täglich um 07:00 Uhr; `/pfad/zum/projekt` durch das Projektverzeichnis ersetzen):
```
0 7 * * * . $HOME/.churchtools_secrets && /pfad/zum/projekt/venv/bin/python3 /pfad/zum/projekt/erweiterte-fuehrungszeugnisse.py >> /pfad/zum/projekt/cron.log 2>&1
```

Unter Windows kann dafür die **Aufgabenplanung** verwendet werden.

### Test (manuell ausführen)

```bash
. ~/.churchtools_secrets && venv/bin/python3 erweiterte-fuehrungszeugnisse.py
```

## Dokumentation
Die vollständige Dokumentation ist [hier verfügbar](https://ftwegner.github.io/ChurchTools/site/index.html).

## Autor
- **Frank Wegner**

## Version
- **1.0**

## Datum
- **21.04.2025**
