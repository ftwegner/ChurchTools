# ChurchTools Gottesdienst-Export

## Purpose

`gottesdienst-export.py` fetches church service data from three ChurchTools instances via REST API and produces a formatted Excel workbook. Optionally sends the workbook as an email attachment.

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
  create_excel()  → openpyxl Workbook → bytes (BytesIO)
          ↓
  send_email()    → SMTP attachment  (only if use_email=True)
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
| C | 55 | `Name - Untertitel - P: Pastor - Musik: Organist` |

Date headings span all 3 columns; Kirchenjahr titles replace weekday names where available.

### Gottesdienste sheet columns

`Gemeinde`, `Standort`, `Datum (Sortierung)`, `Datum`, `Beginn`, `Ende`, `Name`, `Dienstplan_Notiz`, `Kalender_Untertitel`, `Kalender_Beschreibung`, `Raum`, `Pastor*in`, `Organist*in`

## Locale

`locale.setlocale(LC_TIME, "de_DE.utf8")` is called per iteration to produce German weekday/month names. Requires German locale to be installed on the OS.

## Notes

- Pagination for events uses `?page=N` appended as a raw query string while still passing the full `params` dict — this works but results in duplicate query parameters on subsequent pages.
- Timezone: all datetimes are converted to `Europe/Berlin` via `zoneinfo.ZoneInfo`.

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
