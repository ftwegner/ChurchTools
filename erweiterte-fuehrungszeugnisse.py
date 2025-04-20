import requests
import locale
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ChurchTools Instanz spezifische Variablen, die angepasst werden müssen
# ----------------------------------------------------------------------
# Base URL der ChurchTools Instanz API
BASE_URL = "https://volksdorf.church.tools/api"

# ID der Gruppe (Merkmal) der Verantwortlichen für die Führungszeugnisse, in der die Posts veröffentlicht werden sollen
GROUP_ID = 153

# Name der Tabellenspalte, die anzeigt, dass ein Mitarbeiter ein erweitertes Führungszeugnis benötigt
# Die ist ein Ja-Nein-Feld
needs_ef_col = "ef_benoetigt"

# Name der Tabellenspalte, die das Datum des Führungszeugnisses enthält 
# Dies ist ein Datumsfeld
ef_date_col = "ef_datum"

# Wieviele Jahre ist ein erweitertes Führungszeugnis gültig
ef_valid_years = 3

# Wieviele Monate vor Ablauf eines erweiterten Führungszeugnisses soll gewarnt werden
ef_warn_months = 1
# -----------------------------------------------------------------------

# Lese das Zugangstoken aus der Umgebungsvariablen
TOKEN = os.getenv("CHURCHTOOLS_TOKEN")

if not TOKEN:
    raise ValueError("Das Access Token ist nicht gesetzt. Bitte die Umgebungsvariable 'CHURCHTOOLS_TOKEN' definieren.")

if not (isinstance(GROUP_ID, int) and GROUP_ID > 0):
    raise ValueError(f"GROUP_ID muss eine positive Zahl sein. Gefunden: {GROUP_ID}")

if not (isinstance(ef_valid_years, int) and ef_valid_years > 0):
    raise ValueError(f"Die Anzahl der Jahre (ef_valid_years) muss eine positive ganze Zahl sein. Gefunden: {ef_valid_years}")

if not (isinstance(ef_warn_months, int) and ef_warn_months > 0):
    raise ValueError(f"Die Anzahl der Monate (ef_warn_months) muss eine positive ganze Zahl sein. Gefunden: {ef_warn_months}")

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

    # Die Überschrift für die verschiedenen Statuswerte:
    ef_fehlt_head = "Ein erweitertes Führungszeugnis fehlt für:\n"
    ef_abgelaufen_head = "Das erweiterte Führungszeugnis ist nicht mehr gültig für:\n"

    if ef_warn_months == 1:
        months_text = "einem Monat"
    else:
        months_text = f"{ef_warn_months} Monaten"

    ef_alt_head = f"Das erweiterte Führungszeugnis wird innerhalb von {months_text} ungültig für:\n"
    ef_ok_head = "Das erweiterte Führungszeugnis ist ok für:\n"

    # Dies sind die Textvariablen für die verschiedenen Listen der Benutzer
    ef_fehlt = ""
    ef_abgelaufen = ""  
    ef_alt = ""
    ef_ok = ""

    # Dies ist der Text, der als Gesamtbericht zurückgegeben wird.
    user_data = ""

    # Setze die Locale auf Deutsch, damit der ausgeschriebene Monatsname in den Datumsangaben auf Deutsch ist
    locale.setlocale(locale.LC_TIME, "de_DE")

    # Das DatumIm Feld ef_datum (Erstellung des erweiterten Führungszeugnisses) ein Datum eingetragen ist

    # Prüfe alle Benutzer
    for user in users:
        # Wird ein erweitertes Führungszeuignis benötigt?
        # Dazu muss der Wert in ef_benoetigt ("Benötigt ein erweitertes Führungszeugnis") auf True stehen
        if user.get(needs_ef_col):
            # Ja, es wird ein Führungszeugnis benötigt

            # Prüpfe, ob ein Führungszeugnis vorhanden ist. 
            # D.h. ob in dem Feld ef_datum (Erstellung des erweiterten Führungszeugnisses) ein Datum eingetragen ist
            ef_datum = str(user.get(ef_date_col))
            if ef_datum == "None":
                # Es ist kein Datum vorthanden, das benötigte Führungszeugnis fehlt
                # Füge den Benutzer zur Liste ef_fehlt hinzu
                ef_fehlt += f"- {user.get('firstName')} {user.get('lastName')}\n"
            else:
                # Es gibt ein Führungszeugnis mit einem Erstellungsdatum
                # Wir prüfen, ob es nich gültig ist oder bald ungültig wird

                ef_date = datetime.strptime(ef_datum, "%Y-%m-%d")
                ef_datum = ef_date.strftime("%#d. %B %Y")
                ef_expiry = ef_date + relativedelta(years=ef_valid_years)
                ef_ablauf = ef_expiry.strftime("%#d. %B %Y")
                ef_warn = ef_expiry - relativedelta(months=ef_warn_months)
                if ef_expiry < datetime.now():
                    ef_abgelaufen += f"- {user.get('firstName')} {user.get('lastName')}: Das Führungszeugnis vom {ef_datum} ist am {ef_ablauf} abgelaufen.\n"
                elif ef_warn < datetime.now():
                    ef_alt += f"- {user.get('firstName')} {user.get('lastName')}: Das Führungszeugnis vom {ef_datum} läuft am {ef_ablauf} ab.\n"
                else:
                    ef_ok += f"- {user.get('firstName')} {user.get('lastName')}: Das Führungszeugnis vom {ef_datum} ist bis zum {ef_ablauf} gültig.\n"

    if len(ef_fehlt) > 0:
        user_data += ef_fehlt_head + ef_fehlt + "\n"
    if len(ef_abgelaufen) > 0:
        user_data += ef_abgelaufen_head + ef_abgelaufen + "\n"
    if len(ef_alt) > 0:
        user_data += ef_alt_head + ef_alt + "\n"
    if len(ef_ok) > 0:
        user_data += ef_ok_head + ef_ok + "\n"
    return user_data

def delete_previous_posts():
    # Get previous post
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
            response = requests.delete( f"{BASE_URL}/posts/{post.get("id")}", headers=headers)
            response.raise_for_status()
            # use "continue" in case we have multiple posts with the same title - to clean up any potential errors
            continue
    
def post_to_group(message):
    # Example:  "expirationDate": "2029-10-19T12:00:00Z",
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

def main():
    # Fetch users and their custom field data
    delete_previous_posts()
    post_to_group(get_users())
    #print(get_users())

if __name__ == "__main__":
    main()