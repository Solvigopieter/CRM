"""
Solvigo CRM – helpers
Pipelinestadia, automatische volgende acties, Excel-export en UI-hulpjes.
"""
import io
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db

VERANTWOORDELIJKEN = ["Pieter", "Extern", "Onbepaald"]

# (stadium, voorgestelde volgende actie, standaard aantal dagen)
STADIA = [
    ("Nieuwe lead",                 "Klant contacteren",                      2),
    ("Te kwalificeren",             "Lead kwalificeren (behoefte + budget)",  3),
    ("Info opgevraagd",             "Technische gegevens opvragen",           5),
    ("Plaatsbezoek gepland",        "Verslag plaatsbezoek invullen",          1),
    ("Plaatsbezoek uitgevoerd",     "Offerte voorbereiden",                   3),
    ("Offerte maken",               "Offerte opstellen en versturen",         3),
    ("Offerte verstuurd",           "Offerte opvolgen",                       7),
    ("Opvolging offerte",           "Klant nabellen over offerte",            3),
    ("Goedgekeurd / in te plannen", "Uitvoeringsdatum plannen",               3),
    ("In uitvoering",               "Job opvolgen en werkverslag invullen",   1),
    ("Uitgevoerd",                  "Facturatie controleren",                 2),
    ("Facturatie",                  "Betaling opvolgen",                      14),
    ("Afgerond",                    "Jaarlijkse opvolging inplannen",         300),
    ("Verloren",                    None,                                     None),
]
STADIUM_NAMEN = [s[0] for s in STADIA]
VOLGENDE_ACTIE = {s[0]: (s[1], s[2]) for s in STADIA}

STADIUM_KLEUR = {
    "Nieuwe lead": "#2f6fb2", "Te kwalificeren": "#2f6fb2", "Info opgevraagd": "#2f6fb2",
    "Plaatsbezoek gepland": "#8a6d1f", "Plaatsbezoek uitgevoerd": "#8a6d1f",
    "Offerte maken": "#7a4fa3", "Offerte verstuurd": "#7a4fa3", "Opvolging offerte": "#7a4fa3",
    "Goedgekeurd / in te plannen": "#1d7a4f", "In uitvoering": "#1d7a4f",
    "Uitgevoerd": "#1d7a4f", "Facturatie": "#1d7a4f",
    "Afgerond": "#5a6472", "Verloren": "#a33c3c",
}

VERVUILINGEN = ["Stof", "Vogelpoep", "Korstmos", "Landbouwstof", "Industrie", "Cementstof", "Onbekend"]
FREQUENTIES = ["Eenmalig", "Jaarlijks", "Halfjaarlijks", "Kwartaal", "Na inspectie"]
ORG_TYPES = ["Eindklant", "Installateur", "O&M-bedrijf", "Partner", "Leverancier"]
ORG_STATUSSEN = ["Actief", "Prospect", "Partner", "Verloren", "Slapend"]
RELATIETYPES = ["Prospect", "Eenmalige klant", "Terugkerende klant", "Partner", "Strategische partner"]
CONTACT_ROLLEN = ["Beslisser", "Technisch contact", "Boekhouding", "Werfleider", "Installateur", "O&M-contact"]
ACTIE_STATUSSEN = ["Open", "Bezig", "Wacht op klant", "Wacht op partner", "Klaar", "Geannuleerd"]
PRIORITEITEN = ["Hoog", "Normaal", "Laag"]
BRONNEN = ["Eigen prospectie", "Partner / installateur", "Website", "Doorverwijzing", "LinkedIn", "Telefoon inbound", "Beurs", "Overig"]
COMM_TYPES = ["Telefoongesprek", "E-mail", "WhatsApp", "Plaatsbezoek", "Offerte", "Interne nota"]
OFFERTE_STATUSSEN = ["Concept", "Verstuurd", "Goedgekeurd", "Verloren", "Verlopen"]
JOB_STATUSSEN = ["Gepland", "Bezig", "Uitgevoerd", "Geannuleerd"]


# ---------- automatische acties ----------

def maak_vervolgactie(deal_id: int, stadium: str):
    """Maakt automatisch de logische volgende actie aan bij een stadiumwissel."""
    actie, dagen = VOLGENDE_ACTIE.get(stadium, (None, None))
    if not actie:
        return None
    deal = db.haal_rij("deals", deal_id)
    if not deal:
        return None
    # geen dubbele open actie met dezelfde omschrijving voor deze deal
    bestaand = db.query_df(
        "SELECT id FROM acties WHERE deal_id = ? AND actie = ? AND status IN ('Open','Bezig')",
        (deal_id, actie),
    )
    if not bestaand.empty:
        return None
    db.voeg_toe("acties", {
        "datum": (date.today() + timedelta(days=dagen)).isoformat(),
        "prioriteit": deal.get("prioriteit") or "Normaal",
        "organisatie_id": deal.get("organisatie_id"),
        "site_id": deal.get("site_id"),
        "partner_id": deal.get("partner_id"),
        "deal_id": deal_id,
        "actie": actie,
        "verantwoordelijke": deal.get("verantwoordelijke") or "Pieter",
        "status": "Open",
    })
    return actie


def wijzig_stadium(deal_id: int, nieuw_stadium: str):
    db.werk_bij("deals", deal_id, {"stadium": nieuw_stadium, "gewijzigd": date.today().isoformat()})
    return maak_vervolgactie(deal_id, nieuw_stadium)


# ---------- Excel-export ----------

def excel_bytes(df: pd.DataFrame, bladnaam: str = "Export") -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as schrijver:
        df.to_excel(schrijver, index=False, sheet_name=bladnaam[:31])
        blad = schrijver.sheets[bladnaam[:31]]
        for kolom in blad.columns:
            breedte = max((len(str(cel.value)) for cel in kolom if cel.value is not None), default=8)
            blad.column_dimensions[kolom[0].column_letter].width = min(breedte + 2, 45)
    return buffer.getvalue()


def export_knop(df: pd.DataFrame, bestandsnaam: str, label: str = "⬇️ Exporteer naar Excel"):
    if df.empty:
        return
    st.download_button(
        label, data=excel_bytes(df, bestandsnaam.replace(".xlsx", "")),
        file_name=bestandsnaam,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"export_{bestandsnaam}",
    )


# ---------- UI-hulpjes ----------

def euro(bedrag) -> str:
    if bedrag is None or pd.isna(bedrag):
        return "€ 0"
    return f"€ {bedrag:,.0f}".replace(",", ".")


def prioriteit_badge(p: str) -> str:
    kleur = {"Hoog": "#a33c3c", "Normaal": "#2f6fb2", "Laag": "#5a6472"}.get(p, "#5a6472")
    return f'<span style="background:{kleur};color:#fff;border-radius:10px;padding:1px 8px;font-size:0.72rem;">{p}</span>'


def te_laat(datum_str: str) -> bool:
    try:
        return date.fromisoformat(str(datum_str)) < date.today()
    except (ValueError, TypeError):
        return False


def sleutel_uit_opties(opties_dict: dict, huidige_id) -> int:
    """Index van huidige_id binnen opties_dict (voor selectbox-index)."""
    sleutels = list(opties_dict.keys())
    try:
        return sleutels.index(huidige_id if huidige_id else 0)
    except ValueError:
        return 0


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Sora', sans-serif !important; letter-spacing: -0.02em; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d2137 0%, #123a57 100%);
}
section[data-testid="stSidebar"] * { color: #eaf2f8 !important; }
section[data-testid="stSidebar"] .stRadio label:hover { opacity: 0.85; }

div.kanban-kaart {
    background: #ffffff;
    border: 1px solid #dde5ec;
    border-left: 4px solid var(--kaartkleur, #2f6fb2);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 8px;
    font-size: 0.8rem;
    line-height: 1.35;
    box-shadow: 0 1px 2px rgba(13,33,55,0.06);
}
div.kanban-kaart b { font-size: 0.85rem; }
div.kolomkop {
    font-family: 'Sora', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    color: #fff;
    background: var(--kaartkleur, #2f6fb2);
    border-radius: 6px;
    padding: 4px 8px;
    margin-bottom: 8px;
    text-align: center;
}
div.telaat { color: #a33c3c; font-weight: 600; }

.stat-tegel {
    background: #ffffff;
    border: 1px solid #dde5ec;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(13,33,55,0.07);
}
.stat-tegel .waarde { font-family:'Sora',sans-serif; font-size: 1.6rem; font-weight: 700; color: #0d2137; }
.stat-tegel .label { font-size: 0.75rem; color: #5a6472; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
"""


def stat_tegel(kolom, waarde, label):
    kolom.markdown(
        f'<div class="stat-tegel"><div class="waarde">{waarde}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )
