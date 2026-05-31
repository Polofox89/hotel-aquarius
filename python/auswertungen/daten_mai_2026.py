"""Stundendaten Mai 2026 – abgelesen aus den Mitarbeiter-Stundenzetteln.

Aufruf:
    python3 daten_mai_2026.py

Die Tageswerte stammen aus den fotografierten Stundenzetteln. Pro Tag sind
Beginn (von), Ende (bis) und die eingetragene Pause hinterlegt; die
Netto-Arbeitszeit wird in ``stundenzettel_auswertung`` berechnet.
"""

from __future__ import annotations

from stundenzettel_auswertung import (
    MitarbeiterMonat,
    Tageseintrag,
    schreibe_auswertung,
)

# --- Saida – Mai 2026 -----------------------------------------------------
# Pause laut Zettel jeweils 15 Minuten. Leere Tage = frei.
# Alle Tageswerte wurden gegen die handschriftliche Stunden-Spalte des Zettels
# gegengeprüft und stimmen überein (z. B. 21.05.: Ende 12:15 -> 4,00 h).
saida = MitarbeiterMonat(
    name="Saida",
    jahr=2026,
    monat=5,
    eintraege=[
        Tageseintrag(1, "08:00", "14:15", 15),
        Tageseintrag(2, "08:00", "13:45", 15),
        Tageseintrag(3, "08:00", "15:15", 15),
        Tageseintrag(4, bemerkung="frei"),
        Tageseintrag(5, bemerkung="frei"),
        Tageseintrag(6, bemerkung="frei"),
        Tageseintrag(7, "08:00", "14:30", 15),
        Tageseintrag(8, "08:00", "12:45", 15),
        Tageseintrag(9, "08:00", "14:00", 15),
        Tageseintrag(10, "08:00", "14:30", 15),
        Tageseintrag(11, "08:00", "13:00", 15),
        Tageseintrag(12, "08:00", "13:30", 15),
        Tageseintrag(13, "08:00", "13:30", 15),
        Tageseintrag(14, "08:00", "14:15", 15),
        Tageseintrag(15, "08:00", "14:45", 15),
        Tageseintrag(16, "08:00", "14:45", 15),
        Tageseintrag(17, "08:00", "14:45", 15),
        Tageseintrag(18, bemerkung="frei"),
        Tageseintrag(19, bemerkung="frei"),
        Tageseintrag(20, bemerkung="frei"),
        Tageseintrag(21, "08:00", "12:15", 15),
        Tageseintrag(22, "08:00", "13:30", 15),
        Tageseintrag(23, "08:00", "14:30", 15),
        Tageseintrag(24, "08:00", "14:00", 15),
        Tageseintrag(25, "08:00", "14:45", 15),
        Tageseintrag(26, bemerkung="frei"),
        Tageseintrag(27, "08:00", "13:15", 15),
        Tageseintrag(28, "08:00", "13:45", 15),
        Tageseintrag(29, "08:00", "13:45", 15),
        Tageseintrag(30, "08:00", "14:00", 15),
        Tageseintrag(31, bemerkung="frei"),
    ],
)


if __name__ == "__main__":
    alle = [saida]
    ziel = schreibe_auswertung(alle)
    print(f"Auswertung geschrieben: {ziel}")
    for ma in alle:
        print(
            f"  {ma.name}: {ma.arbeitstage()} Arbeitstage, "
            f"Gesamt {ma.gesamt_minuten() // 60}:{ma.gesamt_minuten() % 60:02d} h"
        )
