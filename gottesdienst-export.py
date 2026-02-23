import requests
import locale
import os
import sys
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
from config import BASE_URL, GROUP_ID, needs_ef_col, ef_date_col, use_email, smtp_server, smtp_port, smtp_username, email_recipients
#use_email = False

if use_email:
    # Import smtplib for the actual sending function
    import smtplib

    # Here are the email package modules we'll need
    from email.message import EmailMessage

# Prüfe, ob mindestens Python 3.6 installiert ist
# Diese Version ist notwendig, um die Datetime- und Dateutil-Bibliotheken und f-Strings zu verwenden.
if sys.version_info < (3, 6):
    raise Exception("Dieses Skript benötigt Python 3.6 oder höher.")

# Lese die SMTP Konfiguration aus der Umgebungsvariablen
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

if use_email and not SMTP_PASSWORD:
    raise ValueError("Das SMTP Passwort ist nicht gesetzt. Bitte die Umgebungsvariable 'SMTP_PASSWORD' definieren.")

# Konfigurationsparameter für verschiedene ChurchTools Instanzen
parameters = [
    {
        "name" : "Volksdorf",
        "id" : "VOL",
        "calendar_ids" : [2],
        "calender_title" : "Gottesdienste",
        "url_name" : "volksdorf",
        "resource_ids" : [3, 5, 9, 10, 11, 12, 13, 14, 22],
        "musik_service_id" : 2,
        "pastores_service_id" : 3
    },
    {
        "name" : "Duvenstedt",
        "id" : "DUV",
        "calendar_ids" : [2],
        "calender_title" : "Gottesdienst (durch PastorInnen zu erstellen)",
        "url_name" : "cantatekirche",
        "resource_ids" : [8],
        "musik_service_id" : 2,
        "pastores_service_id" : 3
    },
    {
        "name" : "Oberalster Bergstedt",
        "id" : "OAB",
        "calendar_ids" : [35, 38, 41],
        "calender_title" : "Gottesdienst",
        "url_name" : "oberalster-bergstedt",
        "resource_ids" : [8, 11, 12, 15, 19, 20, 28, 29, 30, 32, 33, 34, 39, 41, 42],
        "musik_service_id" : 10,
        "pastores_service_id" : 1
    }
]
TO = "2026-12-31"

def get_services():
    services = "'Gemeinde','Standort','Datum (Sortierung)','Datum','Beginn','Ende','Name',\
'Dienstplan_Notiz','Kalender_Untertitel','Kalender_Beschreibung','Raum','Pastor*in','Organist*in'\n\
'ChurchTools Instanz','event.calendar.domainAttributes.campusName','event.startDate',\
'event.startDate','event.startDate','event.endDate','event.name','event.note',\
'appointment.base.subtitle','appointment.base.description','booking.base.resource.name',\
'event.eventServices.name','event.eventServices.name'\n"
    for param in parameters:
        ID = param.get("id")
        NAME = param.get("name")
        BASE_URL = f"https://{param.get("url_name")}.church.tools/api"
        CALENDAR_IDS = param.get("calendar_ids")
        CALENDAR_TITLE = param.get("calender_title")
        RESOURCE_IDS = param.get("resource_ids")
        MUSIK_SERVICE_ID = param.get("musik_service_id")
        PASTORES_SERVICE_ID = param.get("pastores_service_id")

        # Lese das Zugangstoken aus der Umgebungsvariablen
        TOKEN = os.getenv(f"CHURCHTOOLS_TOKEN_{ID}")

        if not TOKEN:
            print(f"Das Access Token ist nicht gesetzt. Bitte die Umgebungsvariable 'CHURCHTOOLS_TOKEN_{ID}' definieren.")
            continue

        # Setze die Locale auf Deutsch, damit der ausgeschriebene Monatsname in den Datumsangaben auf Deutsch ist
        locale.setlocale(locale.LC_TIME, "de_DE.utf8")

        # Lade alle Gottesdienste im Events Modul (Dienstplan)
        # -> events
        headers = {
            "Authorization": f"Login {TOKEN}"
        }
        params = {
            # Kalender ID 2 ist der Gottesdienste Kalender, wir nehmen nur Events aus diesem Kalender
            "calendar_ids[]": CALENDAR_IDS,
            "from": "2026-01-01",
            # Das "to" Feld ist nötig, weil sonst nur Events des aktuellen Monats geladen werden
            "to": TO,
            # Lade auch Details zu Diensten wie Musik und Pastor*in
            "include": "eventServices",
            # Keine abgesagten Events
            "canceled": "false",
        }

        events_response = requests.get(f"{BASE_URL}/events", headers=headers, params=params)    
        events_response.raise_for_status()
        events = events_response.json().get("data", [])
        pagination = events_response.json().get("meta").get("pagination")
        if pagination:
            pages = pagination.get("lastPage")
            for page in range(2, pages + 1):
                events_response = requests.get(f"{BASE_URL}/events?page={page}", headers=headers, params=params)
                events_response.raise_for_status()
                events.extend(events_response.json().get("data", []))
        print(f"{len(events)} Events für {NAME} gefunden.")
        # Lade alle Einträge aus dem Gottesdienste Kalender
        # -> appointments
        params = {
            "from": "2026-01-01",
            # Das "to" Feld ist nötig, weil sonst nur Termine des aktuellen Monats geladen werden
            "to": TO,
        }
        # Gottesdienste Kalender hat die ID 2 für Volksdorf
        appointments_response = requests.get(f"{BASE_URL}/calendars/{CALENDAR_IDS[0]}/appointments", headers=headers, params=params)    
        appointments_response.raise_for_status()
        appointments = appointments_response.json().get("data", [])
        pagination = appointments_response.json().get("meta").get("pagination")
        if pagination:
            pages = pagination.get("lastPage")
            for page in range(2, pages + 1):
                appointments_response = requests.get(f"{BASE_URL}/calendars/{CALENDAR_IDS[0]}/appointments?page={page}", headers=headers, params=params)
                appointments_response.raise_for_status()
                appointments.extend(appointments_response.json().get("data", []))
        print(f"{len(appointments)} Kalendereinträge für {NAME} gefunden.")

        # Lade alle Raumbuchungen für die Gottesdienste
        params = {
            # Gottesdienst Räume
            "resource_ids[]": RESOURCE_IDS,
            "from": "2026-01-01",
            # Das "to" Feld ist nötig, weil sonst nur Buchungen des aktuellen Monats geladen werden
            "to": TO,
        }
        bookings_response = requests.get(f"{BASE_URL}/bookings", headers=headers, params=params)

        bookings_response.raise_for_status()
        bookings = bookings_response.json().get("data", [])
        pagination = bookings_response.json().get("meta").get("pagination")
        if pagination:
            pages = pagination.get("lastPage")
            for page in range(2, pages + 1):
                bookings_response = requests.get(f"{BASE_URL}/bookings?page={page}", headers=headers, params=params)
                bookings_response.raise_for_status()
                bookings.extend(bookings_response.json().get("data", []))
        print(f"{len(bookings)} Raumbuchungen für {NAME} gefunden.")

        # Erstelle die CSV Datei mit den Gottesdiensten
        # CSV Spalten:
        # Gemeinde               - 'Volksdorf' (statisch)
        # Datum                  - 'Montag, den 01.01.2024' (aus event.startDate)
        # Beginn                 - '10:00' (aus event.startDate)
        # Ende                   - '12:00' (aus event.endDate)
        # Name                   - Gottesdienst (aus event.name)
        # Dienstplan_Notiz       - Notiz zum Dienstplan (aus event.note)
        # Kalender_Untertitel    - Untertitel des Kalendereintrags (aus appointment.base.subtitle)
        # Kalender_Beschreibung  - Beschreibung des Kalendereintrags (aus appointment.base.description)
        # Raum                   - Raum/Kirche (aus booking.base.resource.name)
        # Pastor*in              - Pastor*in (aus event.eventServices mit serviceId 3)                                               
        # Organist*in            - Organist*in (aus event.eventServices mit serviceId 2)
        # Gottesdienste
        for event in events:
            if event.get("calendar").get("title") == CALENDAR_TITLE:
                if event.get("calendar").get("domainAttributes").get("campusName"):
                    location = event.get("calendar").get("domainAttributes").get("campusName")
                else:
                    location = "(kein Standort)"
                eventServices = event.get("eventServices", [])
                event_start_date = datetime.fromisoformat(event.get("startDate"))
                event_end_date = datetime.fromisoformat(event.get("endDate"))
                pastores = []
                musik = []
                for service in eventServices:
                    if service.get("name"):
                        if service.get("serviceId") == MUSIK_SERVICE_ID:
                            musik.append(service.get("name"))
                        if service.get("serviceId") == PASTORES_SERVICE_ID:
                            pastores.append(service.get("name"))
                appointment_id = event.get("appointmentId")
                appointment = next((a for a in appointments if a.get("base").get("id") == appointment_id), None)
                if appointment:
                    ab = appointment.get('base')
                    subtitle = ab.get('subtitle')
                    if not subtitle:
                        subtitle = '(kein Untertitel)'
                    description = ab.get('description')
                    if not description:
                        description = '(keine Beschreibung)'
                    a_text = f"'{subtitle.replace("'", "")}','{description.replace("'", "")}',"
                else:
                    a_text = "'(Kein Kalendereintrag)','',"    
                booking = next((b for b in bookings if b.get("base").get("appointmentId") == appointment_id), None)
                if booking:
                    bb = booking.get('base')
                    b_text = f"{bb.get('resource').get('name')}"
                else:
                    b_text = "(Keine Raumbuchung)"
                note = event.get('note')
                if not note:
                    note = '(keine Dienstplan-Notiz)'
                if not pastores:
                    pastores.append('(keine Pastor*in)')
                if not musik:
                    musik.append('(kein Organist*in)')
                services += f"'{NAME.replace("'", "")}',\
'{location.replace("'", "")}',\
'{event_start_date}',\
'{calendar.day_name[event_start_date.weekday()]}, den {event_start_date.strftime('%d.%m.%Y')}',\
'{event_start_date.strftime('%H:%M')}',\
'{event_end_date.strftime('%H:%M')}','{event.get('name').replace("'", "")}',\
'{note.replace("'", "")}',\
{a_text}'{b_text.replace("'", "")}','{" | ".join(pastores)}','{" | ".join(musik)}'\n"

    return services

def send_email(services):
    # Send the email with the report
    # Create the container (outer) email message.
    # msg = MIMEMultipart()
    msg = EmailMessage()
    msg['Subject'] = 'Liste der Gottsdienste'
    msg['From'] = smtp_username
    msg['To'] = email_recipients
    msg.set_content("""*** Dies ist eine automatisch generierte Nachricht. ***\n\n
Hallo,\n\nIm Anhang ist die Liste der Gottesdienste.\n\nViele Grüße,\nFrank""")
    services_bytes = services.encode('utf-8')
    msg.add_attachment(services_bytes, maintype='text', subtype='csv', filename='Gottesdienste.csv')
    # Send the email
    try:
        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(smtp_username, SMTP_PASSWORD)  # Log in to the SMTP server
            server.send_message(msg)  # Send the email
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    services = get_services()
    print(services)
    if use_email:
        # Send the email with the report
        send_email(services)

if __name__ == "__main__":
    main()