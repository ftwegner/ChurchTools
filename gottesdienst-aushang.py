import copy
import os
import sys
import calendar
import textwrap
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from io import BytesIO

import requests
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Prüfe, ob mindestens Python 3.6 installiert ist
if sys.version_info < (3, 6):
    raise Exception("Dieses Skript benötigt Python 3.6 oder höher.")

# -----------------------------------------------------------------------
# Manuell vor jedem Skriptstart anzupassende Parameter
# -----------------------------------------------------------------------
# Datum, ab dem Gottesdienste für den Aushang berücksichtigt werden
# (Gottesdienste vor diesem Datum werden nicht aufgenommen).
AUSHANG_DATE = date.today()

# Gemeinden-Kürzel, deren Gottesdienste im Aushang erscheinen sollen.
# Mögliche Werte: "VOL" (Volksdorf), "DUV" (Duvenstedt), "OAB" (Oberalster Bergstedt)
GEMEINDEN = ["VOL"]

# Konfigurationsparameter für verschiedene ChurchTools Instanzen
parameters = [
    {
        "name" : "Volksdorf",
        "id" : "VOL",
        "calendar_ids" : [2],
        "url_name" : "volksdorf",
        "resource_ids" : [3, 5, 9, 10, 11, 12, 13, 14, 22],
        "musik_service_id" : 2,
        "pastores_service_id" : 3
    },
    {
        "name" : "Duvenstedt",
        "id" : "DUV",
        "calendar_ids" : [2,39],
        "url_name" : "cantatekirche",
        "resource_ids" : [8],
        "musik_service_id" : 2,
        "pastores_service_id" : 3
    },
    {
        "name" : "Oberalster Bergstedt",
        "id" : "OAB",
        "calendar_ids" : [35, 38, 41],
        "url_name" : "oberalster-bergstedt",
        "resource_ids" : [8, 11, 12, 15, 19, 20, 28, 29, 30, 32, 33, 34, 39, 41, 42],
        "musik_service_id" : 10,
        "pastores_service_id" : 1
    }
]

FROM = AUSHANG_DATE.strftime("%Y-%m-%d")
one_year_from_aushang_date = AUSHANG_DATE + timedelta(days=365)
TO = one_year_from_aushang_date.strftime("%Y-%m-%d")

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

def get_services(from_date=None, to_date=None, gemeinden=None):
    _from = from_date if from_date else FROM
    _to   = to_date   if to_date   else TO
    rows = [
        ['Gemeinde', 'Standort', 'Datum (Sortierung)', 'Datum', 'Beginn', 'Ende', 'Name',
         'Dienstplan_Notiz', 'Kalender_Untertitel', 'Kalender_Beschreibung', 'Raum', 'Pastor*in', 'Organist*in'],
    ]
    person_titel_cache = {}  # (base_url, person_id) -> gottesdienstplan_titel
    for param in parameters:
        ID = param.get("id")
        if gemeinden and ID not in gemeinden:
            continue
        NAME = param.get("name")
        BASE_URL = f"https://{param.get("url_name")}.church.tools/api"
        CALENDAR_IDS = param.get("calendar_ids")
        RESOURCE_IDS = param.get("resource_ids")
        MUSIK_SERVICE_ID = param.get("musik_service_id")
        PASTORES_SERVICE_ID = param.get("pastores_service_id")

        # Lese das Zugangstoken aus der Umgebungsvariablen
        TOKEN = os.getenv(f"CHURCHTOOLS_TOKEN_{ID}")

        if not TOKEN:
            print(f"Das Access Token ist nicht gesetzt. Bitte die Umgebungsvariable 'CHURCHTOOLS_TOKEN_{ID}' definieren.", file=sys.stderr)
            continue

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
        print(f"{len(events)} Events für {NAME} gefunden.", file=sys.stderr)
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
        print(f"{len(appointments)} Kalendereinträge für {NAME} gefunden.", file=sys.stderr)

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
        print(f"{len(bookings)} Raumbuchungen für {NAME} gefunden.", file=sys.stderr)

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

    return rows

# -----------------------------------------------------------------------
# Word-Aushang: Feldaufbereitung
# -----------------------------------------------------------------------
_UNTERTITEL_PLACEHOLDERS = ('(kein Untertitel)', '(Kein Kalendereintrag)')
_RAUM_PLACEHOLDER = '(Keine Raumbuchung)'
_STANDORT_PLACEHOLDER = '(kein Standort)'
_PASTOR_PLACEHOLDER = '(keine Pastor*in)'

MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

def _format_date(dt):
    # Kurzform ohne führende Nullen, wie im Aushang-Muster: "6.9.2026"
    return f"{dt.day}.{dt.month}.{dt.year}"

def _format_time(hhmm):
    hour, minute = (int(x) for x in hhmm.split(':'))
    if minute == 0:
        return f"{hour} Uhr"
    return f"{hour}:{minute:02d} Uhr"

def _format_location(row):
    raum = row[10]
    if raum and raum != _RAUM_PLACEHOLDER:
        return raum
    standort = row[1]
    if standort and standort != _STANDORT_PLACEHOLDER:
        return standort
    return ""

def _format_pastores(row):
    pastor_field = row[11]
    if not pastor_field or pastor_field == _PASTOR_PLACEHOLDER:
        return ""
    return pastor_field.replace(" | ", " / ")

def _format_title(row):
    name = row[6] or ""
    untertitel = row[8]
    if untertitel and untertitel not in _UNTERTITEL_PLACEHOLDERS:
        return f"{name} {untertitel}".strip()
    return name

def _build_entry(row):
    return {
        "date": _format_date(row[2]),
        "time": _format_time(row[4]),
        "location": _format_location(row),
        "pastores": _format_pastores(row),
        "title": _format_title(row),
    }

# -----------------------------------------------------------------------
# Seitenfüllung: wie viele Gottesdienste passen auf eine Seite?
#
# Word rendert keine exakte Zeilenumbruchsimulation ohne echte Layout-Engine.
# Die folgenden Werte sind empirisch aus einem per LibreOffice gerenderten
# Aushang.docx (Open Sans 24pt fett) kalibriert: PNG-Export bei 100dpi,
# Tabellenlinien pixelgenau vermessen und in Twips zurückgerechnet. Eine rein
# theoretische Schätzung (Zeilenhöhe = Schriftgröße * 1.15) lag deutlich
# daneben (552 statt tatsächlich ca. 680 Twips je Zeile) und führte zu einer
# zweiten Seite. Zeilen erhalten die Höhenregel "mindestens", sodass Word bei
# einer zu knapp geschätzten Zeile trotzdem noch selbst nachjustieren kann.
# Ein zusätzlicher Sicherheitsabstand (_SAFETY_MARGIN_TWIPS) fängt restliche
# Ungenauigkeiten ab, damit garantiert nur eine Seite entsteht.
_PAGE_HEIGHT_TWIPS = 16838   # A4 Höhe
_MARGIN_TOP_TWIPS = 1417
_MARGIN_BOTTOM_TWIPS = 1134
_USABLE_HEIGHT_TWIPS = _PAGE_HEIGHT_TWIPS - _MARGIN_TOP_TWIPS - _MARGIN_BOTTOM_TWIPS

FONT_NAME = "Open Sans"
FONT_SIZE_PT = 14

_LINE_HEIGHT_TWIPS = 397  # empirisch gemessen (Open Sans 14pt fett, LibreOffice-Rendering)

# Logo + Überschriftenblock ("Unsere Gottesdienste" / "im {Monat} {Jahr}"),
# empirisch gemessen (Tabellenbeginn minus oberer Rand). Bleibt unabhängig
# von der Tabellenschriftgröße gleich, da dieser Block fest bei 24pt bleibt.
_FIXED_TOP_BLOCK_TWIPS = 5293
# Word fügt nach jeder Tabelle zwingend einen Absatz ein (hier: der letzte,
# 22pt-Absatz im Template) - der steht mit auf der Seite und muss mitgezählt
# werden, sonst wird eine Zeile zu viel eingefügt und es entsteht Seite 2.
# Ebenfalls unabhängig von der Tabellenschriftgröße.
_TRAILING_PARAGRAPH_TWIPS = 624
# Puffer gegen restliche Ungenauigkeiten der Schätzung (ca. 1 Zeile)
_SAFETY_MARGIN_TWIPS = _LINE_HEIGHT_TWIPS

# Nutzbare Spaltenbreite abzüglich Zellenrändern, umgerechnet in Zeichen pro
# Zeile bei 14pt fett - gegen das tatsächliche Rendering verifiziert.
_CHARS_PER_LINE_COL1 = 12   # Spalte "Datum"
_CHARS_PER_LINE_COL2 = 17   # Spalte "Zeit/Ort"
_CHARS_PER_LINE_COL3 = 27   # Spalte "Liturgie / Gottesdienst"

_HEADER_TEXTS_AND_WIDTHS = (
    ("Datum", _CHARS_PER_LINE_COL1),
    ("Zeit/Ort", _CHARS_PER_LINE_COL2),
    ("Liturgie / Gottesdienst", _CHARS_PER_LINE_COL3),
)

def _n_lines(text, chars_per_line):
    if not text:
        return 1
    # Wortweiser Umbruch (wie in Word) statt reiner Zeichen-Division: lange
    # Wörter/Bindestrich-Wörter erzwingen oft einen Umbruch, bevor die Zeile
    # rechnerisch voll wäre, siehe z. B. "Prädn. Roedenbeck-Wachsmann".
    return max(1, len(textwrap.wrap(text, width=chars_per_line)))

def _row_height_twips(entry):
    col1_lines = _n_lines(entry["date"], _CHARS_PER_LINE_COL1) + 1  # + Leerzeile
    col2_lines = _n_lines(entry["time"], _CHARS_PER_LINE_COL2) + _n_lines(entry["location"], _CHARS_PER_LINE_COL2)
    col3_lines = _n_lines(entry["pastores"], _CHARS_PER_LINE_COL3) + _n_lines(entry["title"], _CHARS_PER_LINE_COL3)
    return max(col1_lines, col2_lines, col3_lines) * _LINE_HEIGHT_TWIPS

def _header_row_twips():
    lines = max(_n_lines(text, width) for text, width in _HEADER_TEXTS_AND_WIDTHS)
    return lines * _LINE_HEIGHT_TWIPS

def _select_entries_for_one_page(entries):
    usable = (
        _USABLE_HEIGHT_TWIPS
        - _FIXED_TOP_BLOCK_TWIPS
        - _header_row_twips()
        - _TRAILING_PARAGRAPH_TWIPS
        - _SAFETY_MARGIN_TWIPS
    )
    selected = []
    used = 0
    for entry in entries:
        height = _row_height_twips(entry)
        if selected and used + height > usable:
            break
        used += height
        selected.append((entry, height))
    return selected

# -----------------------------------------------------------------------
# Word-Dokument erzeugen
# -----------------------------------------------------------------------
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "Aushang-template.docx")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "Aushang.docx")

def _force_font(run):
    # Das Template hat auf manchen (leeren) Platzhalter-Runs keine oder
    # abweichende rFonts/Größe gesetzt, was zu einem sichtbaren Schriftmix
    # führt. Deshalb Schrift/Größe/Fett für jeden befüllten Run explizit
    # erzwingen, statt uns auf die Template-Formatierung zu verlassen.
    run.font.bold = True
    run.font.size = Pt(FONT_SIZE_PT)
    run.font.name = FONT_NAME
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rFonts.set(qn(attr), FONT_NAME)

def _set_two_lines(cell, line1, line2):
    paragraphs = cell.paragraphs
    if len(paragraphs) < 2:
        new_p = copy.deepcopy(paragraphs[0]._p)
        paragraphs[0]._p.addnext(new_p)
        paragraphs = cell.paragraphs
    for paragraph, text in zip(paragraphs[:2], (line1, line2)):
        if paragraph.runs:
            run = paragraph.runs[0]
            run.text = text
            for extra_run in paragraph.runs[1:]:
                extra_run._r.getparent().remove(extra_run._r)
        else:
            run = paragraph.add_run(text)
        _force_font(run)

def _update_month_heading(doc, aushang_date):
    heading = f"im {MONTHS_DE[aushang_date.month - 1]} {aushang_date.year}"
    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith("im "):
            if paragraph.runs:
                paragraph.runs[0].text = heading
                for extra_run in paragraph.runs[1:]:
                    extra_run.text = ""
            else:
                paragraph.add_run(heading)
            return
    print("Warnung: Überschrift für Monat/Jahr im Template nicht gefunden.", file=sys.stderr)

def create_aushang_docx(entries, aushang_date, template_path=TEMPLATE_PATH):
    doc = Document(template_path)
    table = doc.tables[0]

    _update_month_heading(doc, aushang_date)

    for cell in table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                _force_font(run)

    selected = _select_entries_for_one_page(entries)
    if len(entries) > len(selected):
        print(f"Hinweis: {len(entries) - len(selected)} weitere Gottesdienste passen nicht mehr auf die Seite und wurden nicht aufgenommen.", file=sys.stderr)

    n_needed = len(selected)
    n_existing = len(table.rows) - 1  # ohne Kopfzeile
    if n_needed > n_existing:
        template_row = table.rows[1]._tr
        for _ in range(n_needed - n_existing):
            table._tbl.append(copy.deepcopy(template_row))
    elif n_needed < n_existing:
        for _ in range(n_existing - n_needed):
            table._tbl.remove(table.rows[-1]._tr)

    for i, (entry, height_twips) in enumerate(selected):
        row = table.rows[i + 1]
        row.height = Pt(height_twips / 20.0)
        _set_two_lines(row.cells[0], entry["date"], "")
        _set_two_lines(row.cells[1], entry["time"], entry["location"])
        _set_two_lines(row.cells[2], entry["pastores"], entry["title"])

    output = BytesIO()
    doc.save(output)
    return output.getvalue()

def list_entries(aushang_date, gemeinden):
    """Alle Gottesdienste ab aushang_date für die gewählten Gemeinden, chronologisch
    sortiert und als Aushang-Zeilen aufbereitet (ohne Seitenbegrenzung)."""
    to_date = (aushang_date + timedelta(days=365)).strftime("%Y-%m-%d")
    rows = get_services(from_date=aushang_date.strftime("%Y-%m-%d"), to_date=to_date, gemeinden=gemeinden)
    services = [r for r in rows[1:] if r[2].date() >= aushang_date]
    services.sort(key=lambda r: r[2])
    print(f"{len(services)} Gottesdienste ab {aushang_date.strftime('%d.%m.%Y')} für {', '.join(gemeinden)} gefunden.", file=sys.stderr)
    return [_build_entry(r) for r in services]

def build_aushang_bytes(aushang_date, gemeinden, template_path=TEMPLATE_PATH):
    entries = list_entries(aushang_date, gemeinden)
    return create_aushang_docx(entries, aushang_date, template_path=template_path)

def main():
    docx_bytes = build_aushang_bytes(AUSHANG_DATE, GEMEINDEN)
    with open(OUTPUT_PATH, 'wb') as f:
        f.write(docx_bytes)
    print(f"Aushang gespeichert: {OUTPUT_PATH}", file=sys.stderr)

if __name__ == "__main__":
    main()
