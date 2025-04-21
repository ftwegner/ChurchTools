# Benutzung
Nachdem du das Skript zur Verwaltung der erweiterten Führungszeugnisse [konfiguriert](configuration.md) hast, kannst Du das Skript auf zwei Arten ausführen:

1. Manuelle Ausführung
2. (optional) Automatisierte Ausführung dieser Funktion

## 1. Manuelle Ausführung

1. Stelle sicher, dass die virtuelle Umgebung  `venv` aktiv ist.
2. Starte Python mit der Datei `erweiterte-fuehrungszeugnisse.py` als Parameter. Passe dabei `<PATH>` an mit dem korrekten Wert:

```
python "<PATH>/ChurchTools Utilities/erweiterte-fuehrungszeugnisse.py"
```


## 2. (optional) Automatisierte Ausführung des Skriptes

Einmal pro Woche (oder wie gewünscht) kann dies Skript über den Windows Task Scheduler oder einen Linux cron Job automatisch laufen. Nutze den Befehl unten. Passe dabei `<PATH>` an mit dem korrekten Wert:

```
"<PATH>\ChurchTools Utilities/.venv/Scripts/python.exe" "<PATH>/ChurchTools Utilities/erweiterte-fuehrungszeugnisse.py"
```
