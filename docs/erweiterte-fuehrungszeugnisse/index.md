# Erweitere Führungszeugnisse

Für bestimmte MitarbeiterInnen einer Kirchengemeinde wird oft ein erweitertes Führungszeugnis benötigt. 

1. [Konfiguration](configuration.md)
2. [Benutzung](usage.md)

## Beschreibung

Ein erweitertes Führungszeugnis ist eine bestimmte Zahl an Jahren gültig (Default = 3 Jahre). Diese Zahl kann angepasst werden.

Dieses Script erzeugt einen Beitrag in einer Gruppe von Verantwortlichen, die sich um Führungszeugnisse kümmern, und informiert über den Status der erweiterten Führungszeugnisse. Dabei wird gewarnt, wenn ein erweitertes Führungszeugnis in den nächsten Monaten ungültig wird.

Es wird empfohlen, dieses Script regelmäßig, z.B. einmal pro Woche, auszuführen. Die Schritte dazu sind im Abschnitt [Benutzung](usage.md) erklärt.

Der generierte Beitrag enthält eine Liste der MitabreiterInnen, mit den folgenden Kategorien (Ein Beispiel vom April 2025 mit den Default Werten für Gültigkeit und Warnung - 3 Jahre bzw. 3 Monate):

> **Status der erweiterten Führungszeugnisse**
>
> Ein erweitertes Führungszeugnis fehlt für:
> - Vorname1 Nachname1
>
> Das erweiterte Führungszeugnis ist nicht mehr gültig für:
> - Vorname2 Nachname2: Das Führungszeugnis vom 1. Januar 2021 ist am 1. Januar 2024 abgelaufen.
>
> Das erweiterte Führungszeugnis wird innerhalb von 3 Monaten ungültig für:
> - Vorname3 Nachname3: Das Führungszeugnis vom 1. Mai 2022 läuft am 1. Mai 2025 ab.
>
> Das erweiterte Führungszeugnis ist ok für:
> - Vorname4 Nachname4: Das Führungszeugnis vom 12. März 2024 ist bis zum 12. März 2027 gültig.
> - Vorname5 Nachname5: Das Führungszeugnis vom 1. März 2025 ist bis zum 1. März 2028 gültig.

Wenn dieses Script ausgeführt wird, werden zunächst eventuell vorhandene Beiträge in dieser Gruppe mit demselben Titel "Status der erweiterten Führungszeugnisse"
gelöscht. Dann wird der neue Beitrag erzeugt und veröffentlicht. So ist immer genau ein Beitrag mit dem Titel "Status der erweiterten Führungszeugnisse" in dieser Gruppe vorhanden.