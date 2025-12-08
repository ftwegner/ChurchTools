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

if use_email and not SMTP_PASSWORD:
    raise ValueError("Das SMTP Passwort ist nicht gesetzt. Bitte die Umgebungsvariable 'SMTP_PASSWORD' definieren.")

if not (isinstance(GROUP_ID, int) and GROUP_ID > 0):
    raise ValueError(f"GROUP_ID in der Datei config.py muss eine positive ganze Zahl sein. Gefunden: {GROUP_ID}")

if not (isinstance(ef_valid_years, int) and ef_valid_years > 0):
    raise ValueError(f"Die Anzahl der Jahre (ef_valid_years) in der Datei config.py muss eine positive ganze Zahl sein. Gefunden: {ef_valid_years}")

if not (isinstance(ef_warn_months, int) and ef_warn_months > 0):
    raise ValueError(f"Die Anzahl der Monate (ef_warn_months) in der Datei config.py muss eine positive ganze Zahl sein. Gefunden: {ef_warn_months}")

def get_services():
    # Finde alle Gottesdienste
    headers = {
        "Authorization": f"Login {TOKEN}"
    }
    response = requests.get(f"{BASE_URL}/events", headers=headers)
    # https://volksdorf.church.tools/api/calendars/2/appointments
    # https://volksdorf.church.tools/api/bookings?resource_ids[]=5&resource_ids[]=3&from=2026-01-01
    # params = {
    #     "resource_ids[]": [5, 7, 12],
    #     "from": "2026-01-01",
    # }
    # r = requests.get(f"{BASE_URL}/bookings", headers=headers, params=params)

    response.raise_for_status()
    events = response.json().get("data", [])
    pagination = response.json().get("meta").get("pagination")
    if pagination:
        pages = pagination.get("lastPage")
        for page in range(2, pages + 1):
            response = requests.get(f"{BASE_URL}/events?page={page}", headers=headers)
            response.raise_for_status()
            events.extend(response.json().get("data", []))
    services = ""
    # Gottesdienste filtern
    for event in events:
        if event.get("calendar").get("title") == "Gottesdienste" and not event.get("isCanceled"):
            event_date = datetime.fromisoformat(event.get("startDate"))
            services = f"{services}{event.get('name')}\nDatum: {event_date.strftime('%d.%m.%Y um %H:%M Uhr')}\n\
Note: {event.get("note")}\n\n"
    return services

def send_email(message):
    # Send the email with the report
    # Create the container (outer) email message.
    msg = MIMEText("""*** Dies ist eine automatisch generierte Nachricht. ***\n\n
Hallo,\n\nHier ist die Liste der Gottesdienste.\n\n
""" + message + """
Viele Grüße,\nFrank""")
    msg['Subject'] = 'Liste der Gottsdienste'
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
    print(get_services())
    # if use_email:
        # Send the email with the report
        # send_email(services)

if __name__ == "__main__":
    main()