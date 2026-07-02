# Solvigo CRM koppelen aan Google Sheets

Deze versie kan klantdata opslaan in Google Sheets in plaats van in de lokale `solvigo_crm.db`.

## 1. Maak een Google Sheet

Maak een lege Google Sheet, bijvoorbeeld: `Solvigo CRM database`.
Kopieer de Sheet-ID uit de URL:

```text
https://docs.google.com/spreadsheets/d/SHEET_ID_HIER/edit
```

## 2. Maak een Google Cloud service account

1. Ga naar Google Cloud Console.
2. Maak of kies een project.
3. Zet de **Google Sheets API** aan.
4. Zet eventueel ook de **Google Drive API** aan.
5. Maak een **Service Account**.
6. Maak een JSON key aan voor dat service account.
7. Kopieer het `client_email` uit de JSON.
8. Deel je Google Sheet met dat `client_email`, net zoals je een Sheet met een persoon deelt.
   Geef minstens **Editor**-rechten.

## 3. Zet de secrets in Streamlit Cloud

Ga in Streamlit Cloud naar:

```text
App → Settings → Secrets
```

Plak daar dit model en vul je eigen waarden in:

```toml
crm_storage = "google_sheets"
google_sheet_id = "PASTE_HIER_DE_ID_VAN_JE_GOOGLE_SHEET"
seed_demo_data = false

[gcp_service_account]
type = "service_account"
project_id = "jouw-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "jouw-service-account@jouw-project-id.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

Let op: zet je echte `secrets.toml` of JSON key nooit op GitHub.

## 4. Deploy opnieuw

Na redeploy maakt de app automatisch tabs/worksheets aan in je Google Sheet:

- `organisaties`
- `contacten`
- `sites`
- `deals`
- `acties`
- `plaatsbezoeken`
- `offertes`
- `jobs`
- `communicatie`
- `bestanden`

Vanaf dan worden nieuwe klanten, acties, deals enz. in Google Sheets opgeslagen.

## Belangrijke beperking

Foto's of documenten die je uploadt bij sites worden nog lokaal opgeslagen in de Streamlit-appmap. Dat is niet betrouwbaar blijvend op Streamlit Cloud. De klantgegevens en metadata staan wel in Google Sheets. Voor echte foto-opslag is later Google Drive, Google Cloud Storage of Supabase Storage beter.
