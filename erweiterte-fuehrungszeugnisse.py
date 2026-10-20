import requests
import locale
import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from config import BASE_URL, GROUP_ID, needs_ef_col, ef_date_col, ef_valid_years, ef_warn_months, use_email, smtp_server, smtp_port, smtp_username, email_recipients
if use_email:
    # Import smtplib for the actual sending function
    import smtplib

    # Here are the email package modules we'll need
    from email.mime.text import MIMEText

# Prüfe, ob mindestens Python 3.6 installiert ist
# Diese Version ist notwendig, um die Datetime- und Dateutil-Bibliotheken und f-Strings zu verwenden.
if sys.version_info < (3, 6):
    raise Exception("Dieses Skript benötigt Python 3.6 oder höher.")

# Lese das Zugangstoken aus der Umgebungsvariablen
TOKEN = os.getenv("CHURCHTOOLS_TOKEN")

# Lese die SMTP Konfiguration aus der Umgebungsvariablen
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

if not TOKEN:
    raise ValueError("Das Access Token ist nicht gesetzt. Bitte die Umgebungsvariable 'CHURCHTOOLS_TOKEN' definieren.")

# Beim E-Mail-Versand müssen alle SMTP-Angaben als Umgebungsvariablen gesetzt sein
_missing = [name for name, value in (("SMTP_SERVER", smtp_server), ("SMTP_USERNAME", smtp_username),
                                     ("EMAIL_RECIPIENTS", email_recipients), ("SMTP_PASSWORD", SMTP_PASSWORD))
            if not value]
if use_email and _missing:
    raise ValueError("USE_EMAIL ist aktiv, aber folgende Umgebungsvariablen fehlen: " + ", ".join(_missing))

if not (isinstance(GROUP_ID, int) and GROUP_ID > 0):
    raise ValueError(f"GROUP_ID in der Datei config.py muss eine positive ganze Zahl sein. Gefunden: {GROUP_ID}")

if not (isinstance(ef_valid_years, int) and ef_valid_years > 0):
    raise ValueError(f"Die Anzahl der Jahre (ef_valid_years) in der Datei config.py muss eine positive ganze Zahl sein. Gefunden: {ef_valid_years}")

if not (isinstance(ef_warn_months, int) and ef_warn_months > 0):
    raise ValueError(f"Die Anzahl der Monate (ef_warn_months) in der Datei config.py muss eine positive ganze Zahl sein. Gefunden: {ef_warn_months}")

def get_users():
    # Finde alle Benutzer, bei denen ein erweitertes Führundgzeugnis benötigt wird
    # und prüfe ob das Führungszeugnis abgelaufen ist

    # Lade alle Benutzer von ChurchTools
    headers = {
        "Authorization": f"Login {TOKEN}"
    }
    response = requests.get(f"{BASE_URL}/persons", headers=headers)
    response.raise_for_status()
    users = response.json().get("data", [])
    pages = response.json().get("meta").get("pagination").get("lastPage")
    for page in range(2, pages + 1):
        response = requests.get(f"{BASE_URL}/persons?page={page}", headers=headers)
        response.raise_for_status()
        users.extend(response.json().get("data", []))
    

    # Benutzer bestimmen, die ein erweitertes Führungszeugnis benötigen

    # Initialisiere die Variablen

    # Überschriften für die Abschnitte
    if ef_warn_months == 1:
        months_text = "einem Monat"
    else:
        months_text = f"{ef_warn_months} Monaten"

    sections = [
        ("Ein erweitertes Führungszeugnis fehlt für:",        "fehlt"),
        ("Das erweiterte Führungszeugnis ist nicht mehr gültig für:", "abgelaufen"),
        (f"Das erweiterte Führungszeugnis wird innerhalb von {months_text} ungültig für:", "bald"),
        ("Das erweiterte Führungszeugnis ist gültig für:",    "ok"),
    ]

    # Listen: Tupel (nachname, vorname, ef_datum_str, gueltig_bis_str)
    # ef_datum_str / gueltig_bis_str sind "–" wenn kein Datum vorhanden
    ef_fehlt     = []
    ef_abgelaufen = []
    ef_alt       = []
    ef_ok        = []

    # Setze die Locale auf Deutsch, damit der ausgeschriebene Monatsname in den Datumsangaben auf Deutsch ist
    locale.setlocale(locale.LC_TIME, "de_DE.utf8")

    # Prüfe alle Benutzer
    for user in users:
        if user.get(needs_ef_col):
            last  = user.get('lastName',  '')
            first = user.get('firstName', '')
            ef_datum_raw = str(user.get(ef_date_col))

            if ef_datum_raw == "None":
                ef_fehlt.append((last, first, "–", "–"))
            else:
                ef_date   = datetime.strptime(ef_datum_raw, "%Y-%m-%d")
                ef_datum  = ef_date.strftime("%-d. %B %Y")
                ef_expiry = ef_date + relativedelta(years=ef_valid_years)
                ef_ablauf = ef_expiry.strftime("%-d. %B %Y")
                ef_warn   = ef_expiry - relativedelta(months=ef_warn_months)

                if ef_expiry < datetime.now():
                    ef_abgelaufen.append((last, first, ef_datum, ef_ablauf))
                elif ef_warn < datetime.now():
                    ef_alt.append((last, first, ef_datum, ef_ablauf))
                else:
                    ef_ok.append((last, first, ef_datum, ef_ablauf))

    def html_table(entries):
        """Gibt eine HTML-Tabelle für eine sortierte Eintrags-Liste zurück."""
        rows = ""
        for last, first, datum, ablauf in sorted(entries):
            rows += (
                f"<tr>"
                f"<td style='padding:4px 8px;border:1px solid #ccc;'>{first} {last}</td>"
                f"<td style='padding:4px 8px;border:1px solid #ccc;'>{datum}</td>"
                f"<td style='padding:4px 8px;border:1px solid #ccc;'>{ablauf}</td>"
                f"</tr>"
            )
        return (
            "<table style='border-collapse:collapse;font-size:14px;'>"
            "<thead><tr>"
            "<th style='padding:4px 8px;border:1px solid #ccc;text-align:left;'>Name</th>"
            "<th style='padding:4px 8px;border:1px solid #ccc;text-align:left;'>Datum des Führungszeugnisses</th>"
            "<th style='padding:4px 8px;border:1px solid #ccc;text-align:left;'>Gültig bis</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )

    category_map = {"fehlt": ef_fehlt, "abgelaufen": ef_abgelaufen, "bald": ef_alt, "ok": ef_ok}

    # Baue den HTML-Bericht auf (für E-Mail)
    html_body = ""
    for heading, key in sections:
        entries = category_map[key]
        if entries:
            html_body += f"<h3>{heading}</h3>{html_table(entries)}"
    if not html_body:
        html_body = "<p>Es sind keine Benutzer gefunden worden, die ein erweitertes Führungszeugnis benötigen.</p>"

    # Baue den Plain-Text-Bericht auf (für ChurchTools Post)
    plain_body = ""
    plain_headings = {
        "fehlt":      "Ein erweitertes Führungszeugnis fehlt für:",
        "abgelaufen": "Das erweiterte Führungszeugnis ist nicht mehr gültig für:",
        "bald":       sections[2][0],
        "ok":         "Das erweiterte Führungszeugnis ist gültig für:",
    }
    for heading, key in sections:
        entries = category_map[key]
        if entries:
            plain_body += plain_headings[key] + "\n"
            for last, first, datum, ablauf in sorted(entries):
                if datum == "–":
                    plain_body += f"- {first} {last}\n"
                else:
                    plain_body += f"- {first} {last}: Führungszeugnis vom {datum}, gültig bis {ablauf}\n"
            plain_body += "\n"
    if not plain_body:
        plain_body = "Es sind keine Benutzer gefunden worden, die ein erweitertes Führungszeugnis benötigen.\n"

    return plain_body, html_body

def delete_previous_posts():
    # Lösche alle vorherigen Posts mit dem Titel "Status der erweiterten Führungszeugnisse"

    # Dazu werden zunächst alle Posts mit dem Titel "Status der erweiterten Führungszeugnisse" in der Gruppe mit GROUP_ID abgerufen
    headers = {
        "Authorization": f"Login {TOKEN}",
        "accept": "application/json"
    }
    response = requests.get(f"{BASE_URL}/posts?group_ids%5B%5D={GROUP_ID}&limit=5&only_my_groups=true", headers=headers)
    response.raise_for_status()
    posts = response.json().get("data", [])
    for post in posts:
        if post.get("title") == "Status der erweiterten Führungszeugnisse":
            # Delete the previous post
            response = requests.delete( f"{BASE_URL}/posts/{post.get('id')}", headers=headers)
            response.raise_for_status()
            # use "continue" in case we have multiple posts with the same title - to clean up any potential errors
            continue
    
def post_to_group(message):
    # Post the message to the group with GROUP_ID
    # Example expiry date:  "expirationDate": "2029-10-19T12:00:00Z",
    text = {
  "content": message,
  "title": "Status der erweiterten Führungszeugnisse",
  "visibility": "group_visible",
  "commentsActive": True,
  "groupId": GROUP_ID
}
    # Define the headers
    headers = {
        "Authorization": f"Login {TOKEN}",
        "Content-Type": "application/json"
    }
    # Make the POST request
    response = requests.post(f"{BASE_URL}/posts", headers=headers, json=text)

    # Raise an exception if the request fails
    response.raise_for_status()

def send_email(message):
    # Send the email with the report
    html = f"""<!DOCTYPE html>
<html lang="de"><body style="font-family:Arial,sans-serif;font-size:14px;color:#333;">
<p><em>*** Dies ist eine automatisch generierte Nachricht. ***</em></p>
<p>Hallo,</p>
<p>hier ist der aktuelle Status der erweiterten Führungszeugnisse:</p>
{message}
<p>Wenn Du diese Nachricht nicht mehr erhalten möchtest, sag mir bitte Bescheid.</p>
<p>Viele Grüße,<br>Frank</p>
</body></html>"""
    msg = MIMEText(html, 'html', 'utf-8')
    msg['Subject'] = 'Status der erweiterten Führungszeugnisse'
    msg['From'] = smtp_username
    msg['To'] = email_recipients

    # Send the email
    try:
        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(smtp_username, SMTP_PASSWORD)  # Log in to the SMTP server
            server.sendmail(msg['From'], msg['To'].split(', '), msg.as_string())  # Send the email
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    delete_previous_posts()
    plain_text, html_text = get_users()
    post_to_group(plain_text)
    if use_email:
        send_email(html_text)

if __name__ == "__main__":
    main()