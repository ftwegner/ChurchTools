import requests
import locale
import os
import sys
import calendar
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.cell.rich_text import CellRichText, TextBlock, InlineFont
from xml.sax.saxutils import escape
from reportlab.lib.colors import CMYKColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Table, TableStyle, Paragraph, Flowable
from config import use_email, smtp_server, smtp_port, smtp_username, email_recipients
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
        "calendar_ids" : [2,39],
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
FROM = date.today().strftime("%Y-%m-%d")
one_year_from_today = date.today() + timedelta(days=365)
TO = one_year_from_today.strftime("%Y-%m-%d")

def get_services(from_date=None, to_date=None):
    _from = from_date if from_date else FROM
    _to   = to_date   if to_date   else TO
    rows = [
        ['Gemeinde', 'Standort', 'Datum (Sortierung)', 'Datum', 'Beginn', 'Ende', 'Name',
         'Dienstplan_Notiz', 'Kalender_Untertitel', 'Kalender_Beschreibung', 'Raum', 'Pastor*in', 'Organist*in'],
    ]
    person_titel_cache = {}  # (base_url, person_id) -> gottesdienstplan_titel
    for param in parameters:
        ID = param.get("id")
        NAME = param.get("name")
        BASE_URL = f"https://{param.get("url_name")}.church.tools/api"
        CALENDAR_IDS = param.get("calendar_ids")
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
            "from": _from,
            # Das "to" Feld ist nötig, weil sonst nur Events des aktuellen Monats geladen werden
            "to": _to,
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
            "from": _from,
            # Das "to" Feld ist nötig, weil sonst nur Termine des aktuellen Monats geladen werden
            "to": _to,
        }
        appointments = []
        for cal_id in CALENDAR_IDS:
            appointments_response = requests.get(f"{BASE_URL}/calendars/{cal_id}/appointments", headers=headers, params=params)
            appointments_response.raise_for_status()
            appointments.extend(appointments_response.json().get("data", []))
            pagination = appointments_response.json().get("meta").get("pagination")
            if pagination:
                pages = pagination.get("lastPage")
                for page in range(2, pages + 1):
                    appointments_response = requests.get(f"{BASE_URL}/calendars/{cal_id}/appointments?page={page}", headers=headers, params=params)
                    appointments_response.raise_for_status()
                    appointments.extend(appointments_response.json().get("data", []))
        print(f"{len(appointments)} Kalendereinträge für {NAME} gefunden.")

        # Lade alle Raumbuchungen für die Gottesdienste
        params = {
            # Gottesdienst Räume
            "resource_ids[]": RESOURCE_IDS,
            "from": _from,
            # Das "to" Feld ist nötig, weil sonst nur Buchungen des aktuellen Monats geladen werden
            "to": _to,
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
            if int(event.get("calendar", {}).get("domainIdentifier", 0)) in CALENDAR_IDS:
                if event.get("calendar").get("domainAttributes").get("campusName"):
                    location = event.get("calendar").get("domainAttributes").get("campusName")
                else:
                    location = "(kein Standort)"
                eventServices = event.get("eventServices", [])
                event_start_date = datetime.fromisoformat(event.get("startDate")).astimezone(_BERLIN)
                event_end_date = datetime.fromisoformat(event.get("endDate")).astimezone(_BERLIN)
                pastores = []
                musik = []
                for service in eventServices:
                    if service.get("name"):
                        if service.get("serviceId") == MUSIK_SERVICE_ID:
                            musik.append(service.get("name"))
                        if service.get("serviceId") == PASTORES_SERVICE_ID:
                            person_id = service.get("personId")
                            titel = ""
                            name = service.get("name") or ""
                            if person_id:
                                cache_key = (BASE_URL, person_id)
                                if cache_key not in person_titel_cache:
                                    try:
                                        r = requests.get(f"{BASE_URL}/persons/{person_id}", headers=headers)
                                        r.raise_for_status()
                                        data = r.json().get("data", {})
                                        person_titel_cache[cache_key] = (
                                            data.get("gottesdienstplan_titel", "") or "",
                                            data.get("lastName", "") or "",
                                        )
                                    except Exception:
                                        person_titel_cache[cache_key] = ("", "")
                                titel, last_name = person_titel_cache[cache_key]
                                if last_name:
                                    name = last_name
                            pastores.append(f"{titel} {name}".strip() if titel else name)
                appointment_id = event.get("appointmentId")
                appointment = next((a for a in appointments if a.get("base").get("id") == appointment_id), None)
                if appointment:
                    ab = appointment.get('base')
                    subtitle = ab.get('subtitle') or '(kein Untertitel)'
                    description = ab.get('description') or '(keine Beschreibung)'
                else:
                    subtitle = '(Kein Kalendereintrag)'
                    description = ''
                booking = next((b for b in bookings if b.get("base").get("appointmentId") == appointment_id), None)
                if booking:
                    b_text = booking.get('base').get('resource').get('name')
                else:
                    b_text = "(Keine Raumbuchung)"
                note = event.get('note')
                if not note:
                    note = '(keine Dienstplan-Notiz)'
                if not pastores:
                    pastores.append('(keine Pastor*in)')
                if not musik:
                    musik.append('(kein Organist*in)')
                rows.append([
                    NAME,
                    location,
                    event_start_date.replace(tzinfo=None),
                    f"{calendar.day_name[event_start_date.weekday()]}, den {event_start_date.strftime('%d.%m.%Y')}",
                    event_start_date.strftime('%H:%M'),
                    event_end_date.strftime('%H:%M'),
                    _clean_name(event.get('name')),
                    note,
                    subtitle,
                    description,
                    b_text,
                    " | ".join(pastores),
                    " | ".join(musik),
                ])

    # Kirchenjahr – calendar ID 14, Volksdorf only
    kirchenjahr_rows = []
    vol_param = next((p for p in parameters if p.get("id") == "VOL"), None)
    TOKEN_VOL = os.getenv("CHURCHTOOLS_TOKEN_VOL")
    if vol_param and TOKEN_VOL:
        BASE_URL_VOL = f"https://{vol_param.get('url_name')}.church.tools/api"
        headers = {"Authorization": f"Login {TOKEN_VOL}"}
        params = {"from": _from, "to": _to}
        kj_response = requests.get(f"{BASE_URL_VOL}/calendars/14/appointments", headers=headers, params=params)
        kj_response.raise_for_status()
        kj_appointments = kj_response.json().get("data", [])
        pagination = kj_response.json().get("meta", {}).get("pagination")
        if pagination:
            pages = pagination.get("lastPage")
            for page in range(2, pages + 1):
                kj_response = requests.get(f"{BASE_URL_VOL}/calendars/14/appointments?page={page}", headers=headers, params=params)
                kj_response.raise_for_status()
                kj_appointments.extend(kj_response.json().get("data", []))
        print(f"{len(kj_appointments)} Kirchenjahr-Einträge gefunden.")
        for appt in sorted(kj_appointments, key=lambda a: a.get("base", {}).get("startDate", "")):
            base = appt.get("base", {})
            start_date = base.get("startDate")
            caption = base.get("caption", "")
            if start_date:
                kirchenjahr_rows.append([datetime.fromisoformat(start_date).astimezone(_BERLIN).replace(tzinfo=None), caption])

    return rows, kirchenjahr_rows

_BERLIN = ZoneInfo("Europe/Berlin")

_NAME_TAGS = (" (LM)", " (WO)", " (B)", " LM", " WO", " B", "-SG", "-R")

def _clean_name(name):
    """Entfernt Kürzel aus _NAME_TAGS, aber nur am Ende des Titels (auch mehrere hintereinander)."""
    if not name:
        return name
    stripped = True
    while stripped:
        stripped = False
        for tag in _NAME_TAGS:
            if name.endswith(tag):
                name = name[:-len(tag)]
                stripped = True
    return name

ARIAL = Font(name="Arial")
ARIAL_BOLD = Font(name="Arial", bold=True)
ARIAL_BOLD_LARGE = Font(name="Arial", bold=True, size=12)
LIGHT_BLUE_FILL = PatternFill(start_color="DAEAF6", end_color="DAEAF6", fill_type="solid")
_THIN = Side(style='thin')
SERVICE_ROW_BORDER = Border(top=_THIN, bottom=_THIN)
_CHARS_PER_LINE_C = 60   # approx characters per line in col C at 11 cm, Arial 11pt
_LINE_HEIGHT_PT   = 14   # Excel line height for Arial 11pt
_ROW_PADDING_PT   = 12   # 6pt top + 6pt bottom

def _gemeindebrief_days(sorted_data, kirchenjahr_by_date):
    """Gruppiert die Gottesdienste nach Tag und bereitet die Gemeindebrief-Texte auf.
    Gemeinsame Grundlage für die Excel-Sheets und die PDFs."""
    # Columns in data rows:
    #  0=Gemeinde, 1=Standort, 2=Datum(sort), 3=Datum(text), 4=Beginn,
    #  5=Ende, 6=Name, 7=Notiz, 8=Untertitel, 9=Beschreibung,
    #  10=Raum, 11=Pastor*in, 12=Organist*in
    days = []
    for service in sorted_data:
        dt = service[2]  # datetime object
        date_key = dt.date()
        if not days or days[-1]["date"] != date_key:
            kj_title = kirchenjahr_by_date.get(date_key)
            days.append({
                "date": date_key,
                "bracket_text": kj_title if kj_title else calendar.day_name[dt.weekday()],
                "services": [],
            })
        name       = service[6] or ''
        untertitel = service[8] or ''
        pastor     = service[11] or ''
        organist   = service[12] or ''
        # Reihenfolge: Titel | Leitung (Pastor*in) | Untertitel
        desc_parts = [name]
        if pastor != '(keine Pastor*in)':
            desc_parts.append(pastor)
        if untertitel not in ('(kein Untertitel)', '(Kein Kalendereintrag)'):
            desc_parts.append(untertitel)
        # if organist != '(kein Organist*in)':
        #    desc_parts.append(f"Musik: {organist}")
        # Raum (ohne "Kirche ") wird nur für Volksdorf hinter dem Standort angezeigt
        raum = service[10]
        raum_clean = None
        if service[0] == "Volksdorf" and raum != "(Keine Raumbuchung)":
            raum_clean = raum.replace("Kirche ", "").strip() or None
        days[-1]["services"].append({
            "gemeinde": service[0],
            "beginn": service[4],
            "standort": service[1],
            "raum": raum_clean,
            "description": ' | '.join(desc_parts),
        })
    return days

def _build_gemeindebrief_sheet(wb, sheet_title, days, highlight_gemeinde):
    ws = wb.create_sheet(title=sheet_title)
    ws.sheet_view.showGridLines = False
    row_idx = 1
    for day in days:
        date_heading = f"{day['date'].strftime('%d.%m.%Y')} ({day['bracket_text']})"
        cell = ws.cell(row=row_idx, column=1, value=date_heading)
        cell.font = ARIAL_BOLD_LARGE
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=3)
        ws.row_dimensions[row_idx].height = 30  # double the default (~15pt)
        row_idx += 1
        ws.row_dimensions[row_idx].height = 6   # 6pt spacer below date heading
        row_idx += 1
        if day.get("note"):
            ws.cell(row=row_idx, column=1, value=day["note"]).font = ARIAL
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=3)
            row_idx += 1
        for s in day["services"]:
            description = s["description"]
            fill = LIGHT_BLUE_FILL if s["gemeinde"] == highlight_gemeinde else None
            # Build column B: standort bold; for Volksdorf append cleaned room in normal weight
            runs = [TextBlock(InlineFont(b=True, rFont="Arial"), s["standort"])]
            if s["raum"]:
                runs.append(TextBlock(InlineFont(b=False, rFont="Arial"), f" ({s['raum']})"))
            col_b = CellRichText(runs)
            for col, value in enumerate([s["beginn"], col_b, description], start=1):
                c = ws.cell(row=row_idx, column=col, value=value)
                if col != 2:
                    c.font = ARIAL  # col 2 font is embedded in CellRichText runs
                c.alignment = Alignment(vertical='center', wrap_text=(col >= 2))
                c.border = SERVICE_ROW_BORDER
                if fill:
                    c.fill = fill
            n_lines = max(1, -(-len(description) // _CHARS_PER_LINE_C))
            ws.row_dimensions[row_idx].height = n_lines * _LINE_HEIGHT_PT + _ROW_PADDING_PT
            row_idx += 1
    # Column A: fixed width just for "00:00"
    ws.column_dimensions['A'].width = 7
    # Column B: 5 cm (≈ 25 Excel character units)
    ws.column_dimensions['B'].width = 25
    # Column C: 11 cm (≈ 55 Excel character units)
    ws.column_dimensions['C'].width = 55

def _build_readme_sheet(wb):
    ws = wb.create_sheet(title="README")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 3   # left margin
    ws.column_dimensions['B'].width = 90  # main content

    _H1   = Font(name="Arial", bold=True, size=14)
    _H2   = Font(name="Arial", bold=True, size=11)
    _BODY = Font(name="Arial", size=11)
    _LINK = Font(name="Arial", size=11, color="1A6BBF", underline="single")
    _WRAP = Alignment(wrap_text=True, vertical='top')

    row = [1]

    def text(value, font=None, h=18, link=None):
        c = ws.cell(row=row[0], column=2, value=value)
        c.font = font or _BODY
        c.alignment = _WRAP
        if link:
            c.hyperlink = link
        ws.row_dimensions[row[0]].height = h
        row[0] += 1

    def blank():
        ws.row_dimensions[row[0]].height = 8
        row[0] += 1

    text("Informationen zur Excel-Datei", font=_H1, h=24)
    blank()
    text("Diese Excel-Datei kann zur Erstellung der Gemeindebriefe genutzt werden. "
         "Sie hat folgende Arbeitsblätter:", h=36)
    text("\u2192  Gemeindebrief - Volksdorf",    font=_H2)
    text("\u2192  Gemeindebrief - Duvenstedt",   font=_H2)
    text("\u2192  Gemeindebrief - OA-Bergstedt", font=_H2)
    text("\u2192  Gottesdienste",                font=_H2)
    text("In den Gemeindebrief-Arbeitsblättern sind die Gottesdienste der jeweiligen Gemeinde "
         "hellblau hinterlegt. Alle Arbeitsblätter enthalten alle Gottesdienste.", h=36)
    blank()
    text("Die folgenden Informationen aus ChurchTools werden verwendet:", font=_H2, h=18)
    text("1.  Alle Einträge der jeweiligen \u201eGottesdienst\u201c-Kalender der ChurchTools-Instanzen "
         "werden angezeigt.")
    text("2.  Datum und Uhrzeit sind vom Gottesdienst-Kalendereintrag.")
    text("3.  Die zweite Spalte zeigt den Standort aus ChurchTools; nur bei der Gemeinde Volksdorf "
         "wird zus\u00e4tzlich der gebuchte Raum in Klammern hinter dem Standort angezeigt.", h=36)
    text("4.  Der Text in der dritten Spalte setzt sich wie folgt zusammen:")
    text("    a)  Der Titel des Kalendereintrags")
    text("    b)  Der Untertitel des Kalendereintrags")
    text("    c)  Die Pastoren/Leitung aus dem Dienstplan")
    blank()
    text("\u00c4nderungen oder Anpassungen werden in ChurchTools vorgenommen. Von", h=28)
    text("https://example.com/gottesdienste", font=_LINK, link="https://example.com/gottesdienste")
    text("kann der aktualisierte Plan jederzeit heruntergeladen werden.")
    return ws


# Gemeindebrief-Ausgaben je Gemeinde: (Kürzel, hervorgehobene Gemeinde, Excel-Sheet, PDF-Dateiname)
GEMEINDEBRIEFE = [
    ("VOL", "Volksdorf",            "Gemeindebrief - Volksdorf",    "VOL-Gottesdienste.pdf"),
    ("DUV", "Duvenstedt",           "Gemeindebrief - Duvenstedt",   "DUV-Gottesdienste.pdf"),
    ("OAB", "Oberalster Bergstedt", "Gemeindebrief - OA-Bergstedt", "OAB-Gottesdienste.pdf"),
]

def _is_christmas_eve(d):
    return (d.month, d.day) == (12, 24)

def sorted_gemeindebrief_days(rows, kirchenjahr_rows, dec24_page=None, from_date=None, to_date=None):
    """dec24_page: Wenn gesetzt, werden die Gottesdienste am 24.12. (nach Beginn) weggelassen.
    Stattdessen erscheint für jeden 24.12. im Zeitraum from_date..to_date die Datumszeile mit
    einem Hinweis auf die Seite des Gemeindebriefs, auf der die Gottesdienste stehen."""
    if dec24_page:
        rows = rows[:1] + [r for r in rows[1:] if not _is_christmas_eve(r[2])]
    sorted_data = sorted(rows[1:], key=lambda r: r[2])  # sort by datetime (skip 1 header row)
    kirchenjahr_by_date = {dt.date(): caption for dt, caption in kirchenjahr_rows}
    days = _gemeindebrief_days(sorted_data, kirchenjahr_by_date)
    if dec24_page:
        _from = date.fromisoformat(from_date or FROM)
        _to   = date.fromisoformat(to_date or TO)
        for year in range(_from.year, _to.year + 1):
            dec24 = date(year, 12, 24)
            if _from <= dec24 <= _to:
                days.append({
                    "date": dec24,
                    "bracket_text": kirchenjahr_by_date.get(dec24) or calendar.day_name[dec24.weekday()],
                    "services": [],
                    "note": f"Die Gottesdienste am 24.12. finden Sie auf Seite {dec24_page} dieses Gemeindebriefes.",
                })
        days.sort(key=lambda d: d["date"])
    return days

def create_excel(rows, days):
    wb = openpyxl.Workbook()

    # Sheet 1: Gottesdienste (full data)
    ws1 = wb.active
    ws1.title = "Gottesdienste"
    for i, row in enumerate(rows):
        ws1.append(row)
        if i == 0:
            for cell in ws1[1]:
                cell.font = ARIAL_BOLD
        else:
            for cell in ws1[i + 1]:
                cell.font = ARIAL

    # Sheets 2–4: Gemeindebrief per Gemeinde
    for _, gemeinde, sheet_title, _ in GEMEINDEBRIEFE:
        _build_gemeindebrief_sheet(wb, sheet_title, days, gemeinde)

    # Move Gottesdienste sheet to the far right
    wb.move_sheet("Gottesdienste", offset=len(wb.sheetnames) - 1)

    # README sheet: first position, active on open
    readme_ws = _build_readme_sheet(wb)
    wb.move_sheet("README", offset=-(len(wb.sheetnames) - 1))
    wb.active = readme_ws

    output = BytesIO()
    wb.save(output)
    return output.getvalue()

# ---------------------------------------------------------------------------
# PDF-Gemeindebrief: ein PDF je Gemeinde, Inhalt wie das Gemeindebrief-Sheet.
# Das Design ist je Gemeinde in PDF_DESIGNS konfigurierbar.
# ---------------------------------------------------------------------------
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

_MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"]

# Designfarben je Jahreszeit (C, M, Y, K in %)
_FARBE_WINTER    = (0, 100, 60, 30)    # Dezember/Januar/Februar
_FARBE_FRUEHLING = (75, 100, 25, 30)   # März/April/Mai
_FARBE_SOMMER    = (100, 80, 30, 0)    # Juni/Juli/August
_FARBE_HERBST    = (100, 0, 60, 20)    # September/Oktober/November

_PDF_DESIGN_STANDARD = {
    "page_width_cm":  13.5,
    "page_height_cm": 18.5,
    "margin_cm":      0.5,
    # reportlab-Fontname -> TTF-Datei im Ordner fonts/
    "fonts": {
        "OpenSans":           "OpenSans-Regular.ttf",
        "OpenSans-SemiBold":  "OpenSans-SemiBold.ttf",
        "OpenSans-ExtraBold": "OpenSans-ExtraBold.ttf",
    },
    "font_regular":    "OpenSans",
    "font_semibold":   "OpenSans-SemiBold",
    "font_extrabold":  "OpenSans-ExtraBold",
    "font_size":       9,
    "leading":         10,
    "date_font_size":  10,
    "month_font_size": 15,
    "cell_padding_v_pt":    3,   # Abstand Text <-> Zeilenrand oben und unten
    "cell_padding_h_pt":    2,
    "space_before_date_pt": 8,   # Abstand Datum <-> Tabelle darüber
    "space_after_date_pt":  2,
    "col_widths_cm":   (1.1, 3.6, 7.8),   # Beginn, Ort, Beschreibung (Summe = Seitenbreite - 2 * Rand)
    "text_color_cmyk": (0, 0, 0, 100),
    "line_color_cmyk": (0, 0, 0, 100),
    "line_width_pt":   0.5,
    "month_colors_cmyk": {
        12: _FARBE_WINTER,    1: _FARBE_WINTER,    2: _FARBE_WINTER,
        3:  _FARBE_FRUEHLING, 4: _FARBE_FRUEHLING, 5: _FARBE_FRUEHLING,
        6:  _FARBE_SOMMER,    7: _FARBE_SOMMER,    8: _FARBE_SOMMER,
        9:  _FARBE_HERBST,   10: _FARBE_HERBST,   11: _FARBE_HERBST,
    },
    # Deckung der Monatsfarbe als Hintergrund der Zeilen der eigenen Gemeinde
    "highlight_opacity": 0.11,
}

# Design je Gemeinde; Abweichungen z. B. mit {**_PDF_DESIGN_STANDARD, "font_size": 8}
PDF_DESIGNS = {
    "VOL": dict(_PDF_DESIGN_STANDARD),
    "DUV": dict(_PDF_DESIGN_STANDARD),
    "OAB": dict(_PDF_DESIGN_STANDARD),
}

def _cmyk(values, opacity=1.0):
    c, m, y, k = (v / 100 * opacity for v in values)
    return CMYKColor(c, m, y, k)

def _register_pdf_fonts(design):
    registered = pdfmetrics.getRegisteredFontNames()
    for font_name, filename in design["fonts"].items():
        if font_name not in registered:
            pdfmetrics.registerFont(TTFont(font_name, os.path.join(_FONT_DIR, filename)))

class _DateHeading(Flowable):
    """Datumszeile: Datum (ExtraBold) + Sonntagsname/Wochentag (SemiBold) links,
    optional der Monatsname rechtsbündig auf derselben Grundlinie.
    continued=True: wiederholte Datumszeile auf der Folgeseite mit "(Fortsetzung)" (Regular)."""
    def __init__(self, day_idx, date_text, bracket_text, month_text, month_color, design, continued=False):
        super().__init__()
        self.day_idx = day_idx
        self.date_text = date_text
        self.bracket_text = bracket_text
        self.month_text = month_text
        self.month_color = month_color
        self.design = design
        self.continued = continued
        self.spaceBefore = design["space_before_date_pt"]
        sizes = [(design["font_extrabold"], design["date_font_size"])]
        if month_text:
            sizes.append((design["font_semibold"], design["month_font_size"]))
        self._ascent = max(pdfmetrics.getAscentDescent(f, s)[0] for f, s in sizes)
        self._descent = min(pdfmetrics.getAscentDescent(f, s)[1] for f, s in sizes)

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = self._ascent - self._descent + self.design["space_after_date_pt"]
        return self.width, self.height

    def draw(self):
        d = self.design
        c = self.canv
        x = d["cell_padding_h_pt"]
        baseline = d["space_after_date_pt"] - self._descent
        c.setFillColor(_cmyk(d["text_color_cmyk"]))
        c.setFont(d["font_extrabold"], d["date_font_size"])
        c.drawString(x, baseline, self.date_text)
        x += pdfmetrics.stringWidth(self.date_text, d["font_extrabold"], d["date_font_size"])
        c.setFont(d["font_semibold"], d["date_font_size"])
        bracket = f" ({self.bracket_text})"
        c.drawString(x, baseline, bracket)
        if self.continued:
            x += pdfmetrics.stringWidth(bracket, d["font_semibold"], d["date_font_size"])
            c.setFont(d["font_regular"], d["date_font_size"])
            c.drawString(x, baseline, " (Fortsetzung)")
        if self.month_text:
            c.setFillColor(self.month_color)
            c.setFont(d["font_semibold"], d["month_font_size"])
            c.drawRightString(self.width - d["cell_padding_h_pt"], baseline, self.month_text)

    def continuation(self):
        """Datumszeile für die Folgeseite: ohne Monatsnamen, mit "(Fortsetzung)"."""
        return _DateHeading(self.day_idx, self.date_text, self.bracket_text, None, None,
                            self.design, continued=True)

class _DayBlock(Flowable):
    """Tagesblock aus Datumszeile und Tabelle. Passt er nicht mehr auf die Seite, kommt er
    komplett auf die nächste Seite -> jede Seite beginnt mit einem Datum. Ist er länger als
    eine ganze Seite, wird die Tabelle geteilt und die Datumszeile auf der Folgeseite
    mit "(Fortsetzung)" wiederholt."""
    def __init__(self, heading, table, frame_height):
        super().__init__()
        self.heading = heading
        self.table = table
        self.frame_height = frame_height
        self.day_idx = heading.day_idx
        self.spaceBefore = heading.spaceBefore

    def wrap(self, avail_width, avail_height):
        _, self._heading_height = self.heading.wrap(avail_width, avail_height)
        _, self._table_height = self.table.wrap(avail_width, avail_height)
        self.width = avail_width
        self.height = self._heading_height + self._table_height
        return self.width, self.height

    def draw(self):
        self.heading.drawOn(self.canv, 0, self._table_height)
        self.table.drawOn(self.canv, 0, 0)

    def split(self, avail_width, avail_height):
        _, height = self.wrap(avail_width, self.frame_height)
        if height <= self.frame_height and avail_height < self.frame_height - 0.5:
            return []  # passt auf eine leere Seite -> komplett auf die nächste Seite
        heading_height = self.heading.wrap(avail_width, avail_height)[1]
        parts = self.table.split(avail_width, avail_height - heading_height)
        if len(parts) < 2:
            return []  # nicht einmal eine Zeile passt noch -> nächste Seite
        return [self.heading, parts[0],
                _DayBlock(self.heading.continuation(), parts[1], self.frame_height)]

class _GemeindebriefDocTemplate(BaseDocTemplate):
    """Merkt sich in Zeichenreihenfolge, welcher Tag auf welcher Seite steht."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rahmen ohne Innenabstand, damit der Seitenrand exakt margin_cm beträgt
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(frames=[frame])])
        self.day_records = []  # (Seite, Tagesindex)

    def afterFlowable(self, flowable):
        if isinstance(flowable, (_DayBlock, _DateHeading)):
            self.day_records.append((self.page, flowable.day_idx))

def _pdf_story(days, highlight_gemeinde, design, color_month_by_day, frame_height):
    text_color = _cmyk(design["text_color_cmyk"])
    line_color = _cmyk(design["line_color_cmyk"])
    pad_v, pad_h = design["cell_padding_v_pt"], design["cell_padding_h_pt"]
    cell_style = ParagraphStyle(
        "cell", fontName=design["font_regular"], fontSize=design["font_size"],
        leading=design["leading"], textColor=text_color)
    col_widths = [w * cm for w in design["col_widths_cm"]]
    story = []
    prev_month = None
    for idx, day in enumerate(days):
        month = (day["date"].year, day["date"].month)
        month_text = _MONATE[day["date"].month - 1].upper() if month != prev_month else None
        prev_month = month
        heading = _DateHeading(
            idx, day["date"].strftime("%d.%m.%Y"), day["bracket_text"], month_text,
            _cmyk(design["month_colors_cmyk"][day["date"].month]), design)
        highlight_color = _cmyk(design["month_colors_cmyk"][color_month_by_day[idx]],
                                design["highlight_opacity"])
        data = []
        style = [
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), pad_v),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad_v),
            ("LEFTPADDING",   (0, 0), (-1, -1), pad_h),
            ("RIGHTPADDING",  (0, 0), (-1, -1), pad_h),
            ("LINEABOVE",     (0, 0), (-1, 0),  design["line_width_pt"], line_color),
            ("LINEBELOW",     (0, 0), (-1, -1), design["line_width_pt"], line_color),
        ]
        if day.get("note"):
            # Hinweiszeile über die ganze Breite, ohne Hintergrund
            data.append([Paragraph(escape(day["note"]), cell_style), "", ""])
            style.append(("SPAN", (0, 0), (-1, 0)))
        for row, s in enumerate(day["services"]):
            ort = f'<font name="{design["font_semibold"]}">{escape(s["standort"])}</font>'
            if s["raum"]:
                ort += f' ({escape(s["raum"])})'
            data.append([
                Paragraph(escape(s["beginn"]), cell_style),
                Paragraph(ort, cell_style),
                Paragraph(escape(s["description"]), cell_style),
            ])
            if s["gemeinde"] == highlight_gemeinde:
                style.append(("BACKGROUND", (0, row), (-1, row), highlight_color))
        story.append(_DayBlock(heading, Table(data, colWidths=col_widths, style=TableStyle(style)),
                               frame_height))
    if not story:
        story.append(Paragraph("Keine Gottesdienste im gewählten Zeitraum.", cell_style))
    return story

def _render_pdf(days, highlight_gemeinde, design, color_month_by_day, title):
    output = BytesIO()
    margin = design["margin_cm"] * cm
    doc = _GemeindebriefDocTemplate(
        output, pagesize=(design["page_width_cm"] * cm, design["page_height_cm"] * cm),
        leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin,
        title=title, author="ChurchTools Gottesdienst-Export")
    doc.build(_pdf_story(days, highlight_gemeinde, design, color_month_by_day, doc.height))
    return output.getvalue(), doc.day_records

def create_pdf(days, highlight_gemeinde, design):
    _register_pdf_fonts(design)
    title = f"Gottesdienste - {highlight_gemeinde}"
    # Lauf 1 ermittelt die Seitenumbrüche (die Farben ändern das Layout nicht).
    _, day_records = _render_pdf(days, highlight_gemeinde, design,
                                 [d["date"].month for d in days], title)
    # Lauf 2: eine Farbe pro Seite, bestimmt durch den Monat des ersten Datums auf der Seite.
    # Ein Tag, der über eine Seite hinausgeht, behält die Farbe seiner Startseite.
    first_month_on_page = {}
    start_page_of_day = {}
    for page, idx in day_records:
        first_month_on_page.setdefault(page, days[idx]["date"].month)
        start_page_of_day.setdefault(idx, page)
    color_month_by_day = [first_month_on_page[start_page_of_day[idx]] for idx in range(len(days))]
    pdf_bytes, _ = _render_pdf(days, highlight_gemeinde, design, color_month_by_day, title)
    return pdf_bytes

def send_email(rows, kirchenjahr_rows):
    # Send the email with the report
    # Create the container (outer) email message.
    # msg = MIMEMultipart()
    msg = EmailMessage()
    msg['Subject'] = 'Liste der Gottsdienste'
    msg['From'] = smtp_username
    msg['To'] = email_recipients
    msg.set_content("""*** Dies ist eine automatisch generierte Nachricht. ***\n\n
Hallo,\n\nIm Anhang ist die Liste der Gottesdienste.\n\nViele Grüße,\nFrank""")
    days = sorted_gemeindebrief_days(rows, kirchenjahr_rows)
    excel_bytes = create_excel(rows, days)
    msg.add_attachment(excel_bytes, maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='Gottesdienste.xlsx')
    for gemeinde_id, gemeinde, _, pdf_filename in GEMEINDEBRIEFE:
        pdf_bytes = create_pdf(days, gemeinde, PDF_DESIGNS[gemeinde_id])
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=pdf_filename)
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="from_date", default=None, help="Start date YYYY-MM-DD")
    parser.add_argument("--to",   dest="to_date",   default=None, help="End date YYYY-MM-DD")
    args = parser.parse_args()
    rows, kirchenjahr_rows = get_services(from_date=args.from_date, to_date=args.to_date)
    print(f"{len(rows) - 1} Gottesdienste gefunden.")
    if use_email:
        send_email(rows, kirchenjahr_rows)

if __name__ == "__main__":
    main()