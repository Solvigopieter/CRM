# 🔆 Solvigo CRM

Sales-CRM op maat van PV-cleaning, gebouwd in Streamlit. De app heeft een Pipedrive-achtige workflow: Kanban-pipeline, klantenfiches, actieblad, plaatsbezoeken, partners, offertes en jobs.

## Opslag

De app ondersteunt twee opslagmodi:

1. **SQLite lokaal** – standaardmodus, handig om lokaal te testen.
2. **Google Sheets** – aanbevolen voor Streamlit Cloud als eenvoudige online opslag van klanten, deals, acties en opvolging.

Zonder Streamlit secrets gebruikt de app automatisch SQLite. Met de juiste secrets schakelt ze automatisch over naar Google Sheets. Zie `GOOGLE_SHEETS_SETUP.md`.

## Starten

```bash
cd solvigo_crm
pip install -r requirements.txt
streamlit run app.py
```

Bij lokale SQLite-start wordt `solvigo_crm.db` automatisch aangemaakt met voorbeelddata, zodat je meteen kan testen. Bij Google Sheets-opslag wordt standaard géén demo-data toegevoegd.

## Bestandsstructuur

```text
solvigo_crm/
├── app.py
├── db.py                     # SQLite + Google Sheets backend
├── helpers.py
├── seed.py
├── requirements.txt
├── GOOGLE_SHEETS_SETUP.md
├── README_DEPLOY.md
├── .streamlit/
│   └── secrets.toml.example  # voorbeeld, geen echte secrets
└── views/
    ├── dashboard.py
    ├── pipeline.py
    ├── acties.py
    ├── organisaties.py
    ├── contacten.py
    ├── sites.py
    ├── plaatsbezoeken.py
    ├── partners.py
    ├── offertes.py
    ├── jobs.py
    └── communicatie.py
```

## Kernlogica

**Twee klantenstromen.** Elke deal en elke site heeft zowel een eindklant als optioneel een partner zoals installateur of O&M-bedrijf. Een lead van een installateur toont dus altijd wie de partner is, wie de eindklant is, welke site het betreft en wie het contact is.

**Automatische volgende actie.** Bij elke stadiumwissel maakt de app de logische vervolgtaak aan, bijvoorbeeld `Offerte verstuurd` → `Offerte opvolgen` over 7 dagen. Dubbele open taken worden vermeden.

**Excel-export.** Deals, klanten, acties, partners, sites, offertes en jobs zijn exporteerbaar als `.xlsx`.

## Belangrijke beperking

Google Sheets bewaart de CRM-tabellen. Foto's of documenten die je uploadt bij sites worden nog lokaal opgeslagen in de Streamlit-appmap. Voor blijvende foto-opslag is later Google Drive, Google Cloud Storage of Supabase Storage beter.
