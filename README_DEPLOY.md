# Solvigo CRM deployen via GitHub naar Streamlit Community Cloud

## 1. GitHub

1. Maak een nieuwe repository, bijvoorbeeld `solvigo-crm`.
2. Upload alle bestanden uit deze map naar de repository.
3. Controleer dat `app.py` en `requirements.txt` in dezelfde map staan.
4. Zet nooit echte secrets of service-account JSON-bestanden op GitHub.

## 2. Google Sheets voorbereiden

Volg eerst `GOOGLE_SHEETS_SETUP.md`.

Kort samengevat:

1. Maak een lege Google Sheet.
2. Maak een Google Cloud service account.
3. Activeer de Google Sheets API.
4. Deel de Google Sheet met het `client_email` van je service account.
5. Zet je credentials in Streamlit Cloud bij **App → Settings → Secrets**.

## 3. Streamlit Community Cloud

1. Ga naar Streamlit Community Cloud en log in met GitHub.
2. Klik op **Create app**.
3. Kies je GitHub repo.
4. Kies branch `main`.
5. Kies als main file path: `app.py`.
6. Vul de secrets in voor Google Sheets.
7. Klik op **Deploy**.

## 4. Controle

Na de eerste start maakt de app automatisch deze tabs aan in je Google Sheet:

```text
organisaties
contacten
sites
deals
acties
plaatsbezoeken
offertes
jobs
communicatie
bestanden
```

Zie je in de zijbalk `Opslag: Google Sheets`, dan schrijft de CRM naar je Google Sheet.
Zie je `Opslag: SQLite lokaal`, dan ontbreken de secrets of staat `crm_storage` niet op `google_sheets`.

## Belangrijk over uploads

Klantdata wordt in Google Sheets bewaard. Uploads zoals foto's/documenten worden nog lokaal opgeslagen en zijn op Streamlit Cloud niet geschikt als permanente opslag.
