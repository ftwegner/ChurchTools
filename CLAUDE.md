# ChurchTools Gottesdienst-Export

## Purpose

`gottesdienst-export.py` fetches church service data from three ChurchTools instances via REST API and produces a formatted Excel workbook plus one PDF per Gemeinde (`VOL-`, `DUV-`, `OAB-Gottesdienste.pdf`). Optionally sends all four files as attachments of one email. No files are written to disk.

## Running the script

```bash
python gottesdienst-export.py [--from YYYY-MM-DD] [--to YYYY-MM-DD]
```

Default date range: today → today + 365 days.

## Dependencies

Installed via `.venv` (virtual environment in the project root):

| Package | Use |
|---|---|
| `requests` | ChurchTools REST API calls |
| `openpyxl` | Excel workbook creation and styling |
| `reportlab` | PDF generation (Gemeindebrief-PDFs) |
| `python-dateutil` | Listed in `requirements.txt`; not directly imported in this script |

Standard library used: `locale`, `os`, `sys`, `calendar`, `datetime`, `zoneinfo`, `io`, `smtplib`, `email`.

Install: `pip install -r requirements.txt` (then also `pip install openpyxl` — it is not in `requirements.txt` but is required).

## Configuration

### `config.py`

| Variable | Description |
|---|---|
| `BASE_URL` | Legacy base URL (Volksdorf); overridden per-instance inside the script |
| `use_email` | `True` → send email after generation |
| `smtp_server` | SMTP host (default: `smtp.web.de`) |
| `smtp_port` | SMTP port (default: `587` / STARTTLS) |
| `smtp_username` | Sender email address |
| `email_recipients` | Comma-separated recipient list |

### Environment variables (secrets — never committed)

| Variable | Description |
|---|---|
| `CHURCHTOOLS_TOKEN_VOL` | Bearer token for `volksdorf.church.tools` |
| `CHURCHTOOLS_TOKEN_DUV` | Bearer token for `cantatekirche.church.tools` |
| `CHURCHTOOLS_TOKEN_OAB` | Bearer token for `oberalster-bergstedt.church.tools` |
| `SMTP_PASSWORD` | Password for the SMTP sender account |

Authentication header: `Authorization: Login <TOKEN>`

### Login-token session change (ChurchTools, announced 2026-08-21)

ChurchTools is changing the default behavior of REST-API login tokens: they will no longer implicitly create a server-side session. Clients that still want a session can request one by sending `with_session=true` as a query parameter on login. The new (session-less) behavior can already be enabled per-instance in ChurchTools system settings to test compatibility ahead of time.

**No code changes needed here.** Every API call in this repo (`gottesdienst-export.py`, `dienstplan_infos.py`, `erweiterte-fuehrungszeugnisse.py`) is a standalone `requests.get`/`post`/`put` call that resends its own `Authorization: Login <TOKEN>` header — none of them use `requests.Session()`, cookies, or call `/api/login`. They never relied on the server-side session ChurchTools was creating as a side effect, so they're already compatible with the upcoming session-less default.

If a token is missing for an instance, that instance is skipped (warning printed, no crash).
If `use_email=True` and `SMTP_PASSWORD` is unset, the script raises `ValueError` immediately.

## ChurchTools instances

Configured in the `parameters` list at the top of the script:

| ID | Name | ChurchTools URL | Calendar IDs |
|---|---|---|---|
| `VOL` | Volksdorf | `volksdorf.church.tools` | `[2]` |
| `DUV` | Duvenstedt | `cantatekirche.church.tools` | `[2]` |
| `OAB` | Oberalster Bergstedt | `oberalster-bergstedt.church.tools` | `[35, 38, 41]` |

Each instance also has `resource_ids` (room booking filter), `musik_service_id`, and `pastores_service_id` for matching services from the Dienstplan.

## ChurchTools API endpoints used

All calls use `GET` with `Authorization: Login <TOKEN>`.
Pagination is handled automatically (iterates through all pages when `meta.pagination.lastPage > 1`).

| Endpoint | Purpose |
|---|---|
| `GET /api/events` | Fetches Dienstplan events; `include=eventServices`, filtered by `calendar_ids[]`, `from`, `to`, `canceled=false` |
| `GET /api/calendars/{id}/appointments` | Fetches calendar entries (subtitle, description, startDate) |
| `GET /api/bookings` | Fetches room bookings filtered by `resource_ids[]`, `from`, `to` |
| `GET /api/calendars/14/appointments` | Kirchenjahr entries (Volksdorf only, calendar ID 14) |

## Data flow

```
ChurchTools API
  ├─ /events              → list of Dienstplan events (with eventServices)
  ├─ /calendars/N/appointments → subtitle, description per event
  ├─ /bookings            → room name per event
  └─ /calendars/14/appointments → Kirchenjahr titles (Volksdorf only)
          ↓
  get_services() → rows (list of lists), kirchenjahr_rows
          ↓
  sorted_gemeindebrief_days() → days (grouped per date, texts prepared; shared by Excel + PDF)
          ↓
  create_excel()  → openpyxl Workbook → bytes (BytesIO)
  create_pdf()    → one PDF per Gemeinde (reportlab) → bytes
          ↓
  send_email()    → SMTP, 4 attachments  (only if use_email=True)
```

## Excel output structure

The workbook produced by `create_excel()` has these sheets (in order):

1. **README** — human-readable explanation of the file (auto-generated, with hyperlinks)
2. **Gemeindebrief - Volksdorf** — formatted 3-column layout; Volksdorf rows highlighted light blue
3. **Gemeindebrief - Duvenstedt** — same layout; Duvenstedt rows highlighted
4. **Gemeindebrief - OA-Bergstedt** — same layout; Oberalster Bergstedt rows highlighted
5. **Gottesdienste** — full raw data with all 13 columns (header row bold)

### Gemeindebrief sheet columns

| Col | Width | Content |
|---|---|---|
| A | 7 | Start time (`HH:MM`) |
| B | 25 | Standort (bold) + room in parentheses (Volksdorf only) — uses `CellRichText` |
| C | 55 | `Name \| Pastor*in (Leitung) \| Untertitel` (Musik currently commented out) |

Date headings span all 3 columns; Kirchenjahr titles replace weekday names where available.

### Gottesdienste sheet columns

`Gemeinde`, `Standort`, `Datum (Sortierung)`, `Datum`, `Beginn`, `Ende`, `Name`, `Dienstplan_Notiz`, `Kalender_Untertitel`, `Kalender_Beschreibung`, `Raum`, `Pastor*in`, `Organist*in`

## PDF output (Gemeindebrief-PDFs)

`create_pdf(days, highlight_gemeinde, design)` renders the same content as the corresponding Gemeindebrief sheet (all three Gemeinden, own Gemeinde highlighted). Mapping Kürzel → highlighted Gemeinde → sheet → PDF filename is in `GEMEINDEBRIEFE`.

- **Design per Gemeinde:** `PDF_DESIGNS["VOL"|"DUV"|"OAB"]`; currently all copies of `_PDF_DESIGN_STANDARD`. Override single keys with `{**_PDF_DESIGN_STANDARD, "key": value}`.
- **Standard design:** 13.5 × 18.5 cm portrait, 0.5 cm margins; Open Sans 9pt / 10pt leading; cell padding 3pt top/bottom; 8pt space above each date heading.
- **Date heading** (`_DateHeading` flowable): date ExtraBold 10pt + Sonntagsname/weekday SemiBold 10pt; on the first day of each month the month name in CAPS, SemiBold 15pt, right-aligned in the month's design color.
- **Ort column:** Standort SemiBold, room in parentheses Regular.
- **Colors (CMYK):** season colors per month (`_FARBE_WINTER/FRUEHLING/SOMMER/HERBST`). Rows of the own Gemeinde get an 11 % tint (`highlight_opacity`) of the color of the **first date on the page** — one color per page. Implemented as two render passes: pass 1 records on which page each day lands (`_GemeindebriefDocTemplate.afterFlowable`; a day split across pages keeps the color of its start page), pass 2 renders with the per-page colors (colors don't affect layout).
- **Page breaks** (`_DayBlock` flowable): a day (heading + table) that doesn't fit on the current page moves completely to the next page, so every page starts with a date. A day longer than a whole page is split; the date heading is repeated on the next page without month name and with "(Fortsetzung)" (Regular). Frame has zero padding so the page margin is exactly `margin_cm`.
- **24.12. page reference:** `sorted_gemeindebrief_days(rows, kirchenjahr_rows, dec24_page=N, from_date, to_date)` drops all services starting on 24.12. and adds, for every 24.12. within the date range, a day with the normal date heading and a `note` ("Die Gottesdienste am 24.12. finden Sie auf Seite N dieses Gemeindebriefes."). Rendered in the PDF as a full-width table row (Regular, lines, no background) and in Excel as a merged row. Used by the web wrapper's `--seite-24-12 N`.
- **Heiligabend extra page** (`_christmas_eve_pages`, config `_HEILIGABEND_SEITE_VOL`, currently VOL only via `PDF_DESIGNS["VOL"]["christmas_eve_page"]`): only when a 24.12. page number is chosen (`dec24_page`). The removed 24.12. services are kept in `day["christmas_eve_services"]`. Appended page(s): title "Heiligabend" in the December color, one column per room (`columns`, matched against the cleaned room name, e.g. "Rockenhof", "St. Gabriel"), each service as time + title (ExtraBold), then subtitle (line breaks kept) and Leitung; red "Region" box at the end of the last column. Columns that don't fit continue on a further page (no font shrinking). Services of the Gemeinde in other rooms / without booking go to an extra page "Nicht zugeordnete Gottesdienste am Heiligabend" (with Standort/Raum line). DUV/OAB: add their own config later.
- **24.12. only own instance** (`christmas_eve_own_only`, currently DUV): on 24.12. the PDF lists only services of its own Gemeinde (`_only_own_on_christmas_eve` in `create_pdf`); a 24.12. without own services (and without page note) is dropped. Other days and other PDFs unchanged.
- **24.12. grouped by location** (`christmas_eve_by_location`, currently OAB; implies own instance only): on 24.12. one full-width table row per Standort (alphabetical) with "Standort:" (SemiBold) and below one line per service "HH:MM Titel | Leitung | Untertitel"; rows get the usual 11 % highlight tint. With a 24.12. page number chosen, only the page note is shown (as for all PDFs).
- **OAB in Cyan** (`PDF_DESIGNS["OAB_CYAN"]`, file `OAB-Cyan-Gottesdienste.pdf`): same as OAB, but month names always 100 % Cyan and all highlight tints 15 % Cyan (no seasonal colors). Listed in `GEMEINDEBRIEFE` with Excel sheet `None` (PDF only) → also the 5th email attachment.
- **Fonts:** TTFs bundled in `fonts/` (Open Sans, SIL OFL, see `fonts/OFL.txt`) so the script works on the server without installed fonts.

## Locale

`locale.setlocale(LC_TIME, "de_DE.utf8")` is called per iteration to produce German weekday/month names. Requires German locale to be installed on the OS.

## Notes

- Pagination for events uses `?page=N` appended as a raw query string while still passing the full `params` dict — this works but results in duplicate query parameters on subsequent pages.
- Timezone: all datetimes are converted to `Europe/Berlin` via `zoneinfo.ZoneInfo`.

---

# gottesdienst-aushang.py — Word-Aushang mit Gottesdienstterminen

## Purpose

`gottesdienst-aushang.py` teilt sich die ChurchTools-Datenbeschaffung (Events, Kalendereinträge, Raumbuchungen, Pastor*innen aus dem Dienstplan) mit `gottesdienst-export.py`, erzeugt daraus aber statt einer Excel-Datei einen einseitigen Word-Aushang `docs/Aushang.docx` auf Basis der Vorlage `docs/Aushang-template.docx`.

## Running the script

```bash
python gottesdienst-aushang.py
```

Keine CLI-Argumente. Vor dem Start werden zwei Variablen oben im Skript manuell gesetzt (gleiches Prinzip wie `APPLY_EDITS` in `dienstplan_infos.py`):

| Variable | Beschreibung |
|---|---|
| `AUSHANG_DATE` | Datum, ab dem Gottesdienste berücksichtigt werden (Default: `date.today()`) |
| `GEMEINDEN` | Liste der Gemeinden-Kürzel (`"VOL"`, `"DUV"`, `"OAB"`), Default `["VOL"]` |

## Vorlage und Musterdatei

- `docs/Aushang-template.docx` — leere Word-Vorlage: Logo/Überschriftenblock + Tabelle mit Kopfzeile und ein paar leeren Datenzeilen.
- `docs/Aushang-sample.docx` — Referenzdatei mit zwei ausgefüllten Beispielzeilen und einer Zeile, die die Feldnamen zeigt (`<Date>`, `<start-time><location>`, `<pastores><title> <subtitle>`), aus der das Spaltenmapping abgeleitet wurde.

### Spaltenmapping (aus den `rows`-Zeilen von `get_services()`)

| Tabellenspalte | Zeile 1 | Zeile 2 |
|---|---|---|
| Datum | `d.m.yyyy` ohne führende Nullen (z. B. `6.9.2026`) | (leer) |
| Zeit/Ort | Beginn als `H Uhr` bzw. `H:MM Uhr` | Raum (`Raum`-Feld); Fallback auf `Standort`, wenn keine Raumbuchung existiert |
| Liturgie / Gottesdienst | Pastor*in (`Pastor*in`-Feld, " / "-getrennt statt " \| ") | `Name` + `Kalender_Untertitel` (Untertitel wird weggelassen, wenn Platzhalter wie `(kein Untertitel)`) |

Die Überschriftenzeile "im {Monat} {Jahr}" wird aus `AUSHANG_DATE` aktualisiert (deutsche Monatsnamen aus einer festen Liste, unabhängig von der System-Locale). "Unsere Gottesdienste" bleibt unverändert.

## Seitenfüllung (wie viele Gottesdienste passen auf die Seite?)

Es gibt keine echte Word-Layout-Engine in Python. Das Skript schätzt stattdessen anhand von Zeichenanzahl je Spaltenbreite und Zeilenhöhe (kalibriert anhand der tatsächlichen Seiten-/Spaltenmaße aus `Aushang-template.docx`, siehe Konstanten `_FIXED_TOP_BLOCK_TWIPS`, `_LINE_HEIGHT_TWIPS`, `_CHARS_PER_LINE_COL2/3`), wie viele Zeilen (inkl. Zeilenumbrüchen bei langen Pastor*in-/Titel-Texten) noch auf eine A4-Seite passen. Tabellenzeilen werden mit Höhenregel "mindestens" gesetzt, damit Word bei einer leicht zu knappen Schätzung trotzdem selbst nachjustieren kann. Nicht mehr passende Gottesdienste (chronologisch nach den ersten N) werden weggelassen; das Skript gibt dazu einen Hinweis auf STDOUT aus.

Die Tabelle in `Aushang-template.docx` wird dynamisch um Zeilen ergänzt oder gekürzt (per Kopie/Löschen der leeren Vorlagenzeilen), je nachdem wie viele Zeilen tatsächlich passen — die Zeilenanzahl der Vorlage selbst ist keine feste Obergrenze.

## Unterschiede zu gottesdienst-export.py

- Keine Kirchenjahr-Abfrage (Kalender 14, nur für die Gemeindebrief-Excel relevant).
- Kein Email-Versand.
- `get_services()` akzeptiert zusätzlich `gemeinden=` zum Filtern auf einzelne ChurchTools-Instanzen.

---

# dienstplan_infos.py — Dienstplan-Auswertung & automatische Korrekturen (Volksdorf)

## Purpose

`dienstplan_infos.py` liest alle Dienstplan-Einträge (Events) der ChurchTools-Instanz **Volksdorf** aus, exportiert sie inkl. Ressourcenbuchungen nach Excel und kann optional festgelegte Korrekturregeln (Titel, "Weitere Infos") automatisch **live in ChurchTools** anwenden.

Anders als `gottesdienst-export.py` (welches nur den Gottesdienste-Kalender `[2]` behandelt) fragt dieses Skript **alle** Kalender und Ressourcen der Instanz ab, um einen vollständigen Überblick über sämtliche Dienstplan-Einträge zu bekommen.

## Running the script

```bash
python dienstplan_infos.py [--from YYYY-MM-DD] [--to YYYY-MM-DD]
```

Default date range: today → today + 365 days.

## APPLY_EDITS-Schalter (Zeile ~17)

```python
APPLY_EDITS = False
```

Diese Variable wird **manuell vor jedem Skriptstart** im Code gesetzt (kein CLI-Flag, bewusst so gewählt, damit ein Lauf mit Schreibzugriff nicht versehentlich per Kommandozeilen-Parameter ausgelöst werden kann):

- `False` (Standard) — nur Simulation. Es werden keinerlei Änderungen an ChurchTools vorgenommen. Ausgabe: `Dienstplan_Infos.xlsx` mit den simulierten Werten zum Vergleich.
- `True` — die simulierten Änderungen (siehe Regeln unten) werden **live per API geschrieben**, zusätzlich zur `Dienstplan_Infos.xlsx` wird ein Änderungsprotokoll `Dienstplan_Aenderungen.xlsx` erzeugt (inkl. README-Sheet mit den Regeln und Erfolg/Fehler je Eintrag).

## Simulations-/Korrekturregeln

Definiert in `TITEL_SIMULATION` und `WEITERE_INFOS_SIMULATION` (oben im Skript) sowie textuell in `README_RULES` (wird 1:1 ins README-Sheet von `Dienstplan_Aenderungen.xlsx` geschrieben):

1. Titel `"Gottesdienst - Rockenhof"` → `"Gottesdienst"`
2. Titel `"Gottesdienst - St. Gabriel"` → `"Gottesdienst"`
3. Ressourcenbuchung enthält `"Kirche Rockenhof"` **und** "Weitere Infos" ist leer → "Weitere Infos" = `"am Rockenhof"`
4. Ressourcenbuchung enthält `"Kirche St. Gabriel"` **und** "Weitere Infos" ist leer → "Weitere Infos" = `"in St. Gabriel"`

Regeln 3/4 überschreiben nie einen bereits vorhandenen "Weitere Infos"-Wert (Dienstplan-Notiz). Um weitere Regeln zu ergänzen, einfach die beiden Dictionaries erweitern — die Anwendung (`apply_changes`) und die README-Generierung greifen automatisch darauf zurück; `README_RULES` ist aktuell freier Text und muss beim Ändern der Dictionaries manuell mitgepflegt werden.

## Wichtige technische Erkenntnis: Titel hängt am Kalendertermin, nicht am Event

Der Dienstplan-Titel (`event.name`, angezeigt als "Titel") ist **read-only auf der Event-Ressource** — `PUT /api/events/{eventId}` akzeptiert nur `note`, `isCanceled`, `adminIds`. Der tatsächliche Titel liegt am zugehörigen Kalendertermin (`appointment.title`, verknüpft über `event.appointmentId`).

Ermittelt über die live-Swagger-Spezifikation der Instanz: `GET https://volksdorf.church.tools/system/runtime/swagger/openapi.json` (verlinkt von der HTML-Seite `/api`, referenziert in `/system/churchcore/openapi.js`). Nützlich, falls künftig weitere Schreib-Endpunkte gebraucht werden.

### Titel ändern (Read-Modify-Write)

```
GET /api/calendars/{calendarId}/appointments/{appointmentId}
→ Feld "title" im "appointment"-Objekt ändern
→ Deprecated Alias-Felder entfernen: @deprecated, caption, note, information, additions
PUT /api/calendars/{calendarId}/appointments/{appointmentId}   Body: das volle (modifizierte) Objekt
```

PUT verlangt praktisch das komplette Termin-Objekt (inkl. `version` für Optimistic Locking) — daher immer erst frisch per GET lesen, nur das benötigte Feld ändern und unverändert zurückschreiben. Andere Felder wie `subtitle` (z. B. "KiGo") bleiben dabei automatisch erhalten. Implementiert in `update_appointment_title()`.

### "Weitere Infos" ändern

```
GET /api/events/{eventId}   (für aktuelles isCanceled/adminIds)
PUT /api/events/{eventId}   Body: {"note": "...", "isCanceled": ..., "adminIds": [...]}
```

Implementiert in `update_event_note()`.

Beide Funktionen werden aus `apply_changes()` aufgerufen, welche pro Dienstplan-Eintrag prüft, ob sich Titel und/oder "Weitere Infos" gegenüber der Simulation unterscheiden, den/die passenden API-Call(s) ausführt und das Ergebnis (inkl. Fehlermeldung bei Exceptions) für das Änderungsprotokoll sammelt.

## Zusätzliche gelesene Endpunkte

| Endpoint | Zweck |
|---|---|
| `GET /api/calendars` | Alle Kalender-IDs der Instanz (ohne Filter — Grundlage für `calendar_ids[]` bei `/events`) |
| `GET /api/resources` | Alle Ressourcen-IDs der Instanz (ohne Filter — Grundlage für `resource_ids[]` bei `/bookings`) |

`/api/bookings` verlangt zwingend `resource_ids[]` (400 Validation Error ohne diesen Parameter), ebenso ist `calendar_ids[]` bei `/api/events` de facto erforderlich, um Daten zu erhalten — deshalb der Umweg über die ungefilterten `/calendars`- und `/resources`-Listen.

## Output-Dateien

| Datei | Wann | Inhalt |
|---|---|---|
| `Dienstplan_Infos.xlsx` | immer | Sheet "Dienstplan": Datum, Uhrzeit, Kalender, Titel, Weitere Infos, Ressourcenbuchungen, Titel (simuliert), Weitere Infos (simuliert) |
| `Dienstplan_Aenderungen.xlsx` | nur wenn `APPLY_EDITS = True` | Sheet "README" (Regeltext, technische Umsetzung, Zeitstempel) + Sheet "Änderungen" (Datum, Uhrzeit, Kalender, Titel vorher/nachher, Weitere Infos vorher/nachher, Status, Fehler) |

## Sonstiges

- Ressourcenbuchungen pro Event werden über `event.appointmentId == booking.base.appointmentId` gematcht und dedupliziert (`dict.fromkeys`) — bei wiederkehrenden Terminen (gleiche `appointmentId` für die ganze Serie) taucht sonst dieselbe Ressource mehrfach auf.
- STDOUT zeigt bewusst nur Zusammenfassungszahlen (Anzahl Kalender/Ressourcen/Events/Buchungen/Änderungen), keine Detailliste — die Detailliste steht ausschließlich in den Excel-Dateien.
