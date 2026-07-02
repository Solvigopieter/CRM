"""
Solvigo CRM – Google Drive helper

Upload bestanden (PDF's) naar Google Drive via het service-account.
Bestanden komen in de map  Solvigo CRM > Offertes  op de Drive van het
service-account. Ze worden publiek leesbaar gemaakt zodat je ze kan openen
via een link.
"""
from __future__ import annotations

import io
from typing import Any

import streamlit as st

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.service_account import Credentials

    DRIVE_BESCHIKBAAR = True
except ImportError:
    DRIVE_BESCHIKBAAR = False

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

_DRIVE_SERVICE = None


def _credentials_dict() -> dict:
    """Lees de service-account-gegevens uit Streamlit secrets."""
    sa = st.secrets.get("gcp_service_account")
    if sa is None:
        raise RuntimeError("gcp_service_account ontbreekt in Streamlit secrets.")
    return dict(sa)


@st.cache_resource
def _drive_service():
    if not DRIVE_BESCHIKBAAR:
        raise RuntimeError(
            "google-api-python-client is niet geïnstalleerd. "
            "Voer uit: pip install google-api-python-client"
        )
    creds = Credentials.from_service_account_info(_credentials_dict(), scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _zoek_of_maak_map(naam: str, parent_id: str | None = None) -> str:
    """Zoek een map op naam (onder parent), of maak ze aan. Geeft folder-id terug."""
    service = _drive_service()
    query = f"name = '{naam}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    resultaat = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
    bestanden = resultaat.get("files", [])
    if bestanden:
        return bestanden[0]["id"]
    # Map aanmaken
    meta: dict[str, Any] = {
        "name": naam,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _offerte_map_id() -> str:
    """Geeft het id van de map 'Solvigo CRM/Offertes' op Drive."""
    root = _zoek_of_maak_map("Solvigo CRM")
    return _zoek_of_maak_map("Offertes", root)


def upload_pdf(bestandsnaam: str, inhoud: bytes) -> tuple[str, str]:
    """
    Upload een PDF naar Google Drive.

    Returns:
        (drive_file_id, web_view_link)
    """
    service = _drive_service()
    folder_id = _offerte_map_id()

    meta: dict[str, Any] = {
        "name": bestandsnaam,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(io.BytesIO(inhoud), mimetype="application/pdf", resumable=True)
    bestand = (
        service.files()
        .create(body=meta, media_body=media, fields="id, webViewLink")
        .execute()
    )
    file_id = bestand["id"]
    link = bestand.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

    # Maak het bestand leesbaar voor iedereen met de link.
    try:
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
    except Exception:
        pass  # Als permissie niet lukt, is de link alleen via service-account bereikbaar.

    return file_id, link


def verwijder_bestand(drive_file_id: str):
    """Verwijder een bestand van Google Drive."""
    try:
        service = _drive_service()
        service.files().delete(fileId=drive_file_id).execute()
    except Exception:
        pass


def drive_link(drive_file_id: str) -> str:
    """Maak een view-link van een Drive file-id."""
    return f"https://drive.google.com/file/d/{drive_file_id}/view"
