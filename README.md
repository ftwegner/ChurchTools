# ChurchTools Utilities

Dieses Projekt enthält Python-Skripte, mit denen die Verwaltung von Vorgängen in der Kirchengemeinde mit ChurchTools vereinfacht werden kann.

## Features
1. **Erweiterte Führungszeugnisse** - Statusbericht und Warnung bei Ablauf.

## Konfiguration & Zugangsdaten

Das Skript liest alle Secrets aus Umgebungsvariablen — es sind **keine Passwörter im Code oder in `config.py`** hinterlegt.

### Benötigte Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `CHURCHTOOLS_TOKEN` | API-Token für `volksdorf.church.tools` |
| `SMTP_PASSWORD` | Passwort für das SMTP-Konto (`absender@example.com`) |

### Einrichtung auf dem Server (example.com)

Die Variablen werden in einer Secrets-Datei gespeichert, die vom Cron-Job geladen wird:

```bash
# Secrets-Datei anlegen / bearbeiten
plink -i "C:\path\to\private-key.ppk" user@example.com "nano ~/.churchtools_secrets"
```

Inhalt der Datei `~/.churchtools_secrets`:
```bash
export CHURCHTOOLS_TOKEN="dein_volksdorf_api_token"
export SMTP_PASSWORD="dein_smtp_passwort"
```

Datei absichern (nur für frank lesbar):
```bash
plink -i "C:\path\to\private-key.ppk" user@example.com "chmod 600 ~/.churchtools_secrets"
```

### Wo bekomme ich den ChurchTools-Token?

1. In ChurchTools einloggen → oben rechts auf das Benutzerbild klicken → **„Mein Profil"**
2. Im Profil: Reiter **„Sicherheit"** → **„API-Token"** → Token kopieren

### Cron-Job

Der Cron-Job sourcet die Secrets-Datei und startet das Skript täglich:

```bash
# Crontab bearbeiten
plink -i "C:\path\to\private-key.ppk" user@example.com "crontab -e"
```

Eintrag (täglich um 07:00 Uhr):
```
0 7 * * * . ~/.churchtools_secrets && /home/user/Python/erweiterte-fuehrungszeugnisse/venv/bin/python3 /home/user/Python/erweiterte-fuehrungszeugnisse/erweiterte-fuehrungszeugnisse.py >> /home/user/Python/erweiterte-fuehrungszeugnisse/cron.log 2>&1
```

### Test (manuell ausführen)

```bash
plink -i "C:\path\to\private-key.ppk" user@example.com ". ~/.churchtools_secrets && /home/user/Python/erweiterte-fuehrungszeugnisse/venv/bin/python3 /home/user/Python/erweiterte-fuehrungszeugnisse/erweiterte-fuehrungszeugnisse.py"
```

## Dokumentation
Die vollständige Dokumentation ist [hier verfügbar](https://ftwegner.github.io/ChurchTools/site/index.html).

## Autor
- **Frank Wegner**

## Version
- **1.0**

## Datum
- **21.04.2025**