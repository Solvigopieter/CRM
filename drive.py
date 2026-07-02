"""
Solvigo CRM – PDF-opslag via Google Sheets

Slaat offerte-PDF's op als base64-data in een apart tabblad ('pdf_bestanden')
in dezelfde Google Sheet. Geen extra API's of Drive-rechten nodig.

Limiet: ±5 MB per PDF (ruim voldoende voor offertes).
"""
from __future__ import annotations

import base64
import io

import streamlit as st

DRIVE_BESCHIKBAAR = True  # altijd beschikbaar, want gebruikt alleen Sheets


def _pdf_sheet():
    """Geeft het worksheet 'pdf_bestanden' terug, maakt het aan als het niet bestaat."""
    import db
    ss = db._spreadsheet()
    try:
        ws = ss.worksheet("pdf_bestanden")
    except Exception:
        ws = ss.add_worksheet(title="pdf_bestanden", rows=500, cols=4)
        ws.update(values=[["offerte_id", "bestandsnaam", "chunk_nr", "data"]], range_name="A1")
    return ws


def upload_pdf(bestandsnaam: str, inhoud: bytes, offerte_id: int) -> str:
    """
    Sla een PDF op in de Google Sheet als base64-chunks.

    Returns:
        bestandsnaam (ter bevestiging)
    """
    # Eerst oude PDF verwijderen als die er was
    verwijder_bestand(offerte_id)

    # Base64-coderen
    b64 = base64.b64encode(inhoud).decode("ascii")

    # Splits in chunks van 40.000 tekens (ruim binnen de 50K cel-limiet)
    CHUNK = 40_000
    chunks = [b64[i:i + CHUNK] for i in range(0, len(b64), CHUNK)]

    ws = _pdf_sheet()
    rijen = []
    for nr, chunk in enumerate(chunks):
        rijen.append([str(offerte_id), bestandsnaam, str(nr), chunk])

    # Voeg alle chunks toe in één API-call
    ws.append_rows(rijen, value_input_option="RAW")

    return bestandsnaam


def haal_pdf_op(offerte_id: int) -> tuple[str, bytes] | None:
    """
    Haal een opgeslagen PDF op uit de Google Sheet.

    Returns:
        (bestandsnaam, pdf_bytes) of None als er geen PDF is.
    """
    ws = _pdf_sheet()
    alle = ws.get_all_records()

    chunks = []
    bestandsnaam = ""
    for rij in alle:
        try:
            if str(rij.get("offerte_id", "")) == str(offerte_id):
                chunks.append((int(rij.get("chunk_nr", 0)), rij.get("data", "")))
                bestandsnaam = rij.get("bestandsnaam", "offerte.pdf")
        except (ValueError, TypeError):
            continue

    if not chunks:
        return None

    # Sorteer op chunk_nr en voeg samen
    chunks.sort(key=lambda x: x[0])
    b64 = "".join(c[1] for c in chunks)

    try:
        pdf_bytes = base64.b64decode(b64)
    except Exception:
        return None

    return bestandsnaam, pdf_bytes


def verwijder_bestand(offerte_id: int):
    """Verwijder alle chunks van een offerte-PDF."""
    try:
        ws = _pdf_sheet()
        alle = ws.get_all_values()
        # Verwijder rijen van achter naar voor (zodat indices niet verschuiven)
        te_verwijderen = []
        for idx, rij in enumerate(alle[1:], start=2):  # skip header
            if rij and str(rij[0]) == str(offerte_id):
                te_verwijderen.append(idx)

        for idx in reversed(te_verwijderen):
            ws.delete_rows(idx)
    except Exception:
        pass


def drive_link(drive_file_id: str) -> str:
    """Niet meer gebruikt (was voor Drive-versie), maar behouden voor compatibiliteit."""
    return ""
