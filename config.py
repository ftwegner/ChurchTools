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

# SMTP Server Konfiguration für den Web.de Emaildienst
# Du kannst den Server und Port bei Bedarf für andere Dienste anpassen
use_email = True  # Wenn True wird eine Email gesendet
smtp_server = 'smtp.web.de'
smtp_port = 587  # Nutze 587 für TLS
smtp_username = 'frank.wegner@web.de' # Das assword ist in der Umgebungsvariablen SMTP_PASSWORD
email_recipients = 'frank.wegner@web.de' # Komma-separierte Liste der Empfänger