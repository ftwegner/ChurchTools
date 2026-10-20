# Allgemeine Konfiguration für die ChurchTools Utilities
# -----------------------------------------------------------------------
# Base URL der ChurchTools Instanz API
BASE_URL = "https://volksdorf.church.tools/api"

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

# E-Mail-Versand
# -----------------------------------------------------------------------
# Alle systemabhängigen Angaben (E-Mail-Adressen, SMTP-Server) kommen aus Umgebungsvariablen,
# damit diese Datei ohne persönliche Daten veröffentlicht werden kann.
# USE_EMAIL:        "true" → nach der Erstellung wird eine E-Mail gesendet (Standard: aus)
# SMTP_SERVER:      Hostname des SMTP-Servers, z. B. smtp.example.com
# SMTP_PORT:        Port des SMTP-Servers (Standard: 587 für STARTTLS)
# SMTP_USERNAME:    Absenderadresse / Login des SMTP-Kontos
# SMTP_PASSWORD:    Passwort des SMTP-Kontos (wird direkt in den Skripten gelesen)
# EMAIL_RECIPIENTS: Komma-separierte Liste der Empfänger
import os
use_email = os.getenv("USE_EMAIL", "false").strip().lower() in ("1", "true", "yes", "ja")
smtp_server = os.getenv("SMTP_SERVER", "")
smtp_port = int(os.getenv("SMTP_PORT") or 587)
smtp_username = os.getenv("SMTP_USERNAME", "")
email_recipients = os.getenv("EMAIL_RECIPIENTS", "")
