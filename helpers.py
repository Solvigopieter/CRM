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
    "Nieuwe lead": "#8A94A6", "Te kwalificeren": "#8A94A6", "Info opgevraagd": "#8A94A6",
    "Plaatsbezoek gepland": "#5B6B8C", "Plaatsbezoek uitgevoerd": "#5B6B8C",
    "Offerte maken": "#2338B0", "Offerte verstuurd": "#2338B0", "Opvolging offerte": "#2338B0",
    "Goedgekeurd / in te plannen": "#1E8E5A", "In uitvoering": "#1E8E5A",
    "Uitgevoerd": "#1E8E5A", "Facturatie": "#1E8E5A",
    "Afgerond": "#9CA3AF", "Verloren": "#B4443C",
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


def export_knop(df: pd.DataFrame, bestandsnaam: str, label: str = "Exporteer naar Excel"):
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
    stijl = {
        "Hoog": ("#FBE9E7", "#B4443C"),
        "Normaal": ("#E8ECFB", "#2338B0"),
        "Laag": ("#F1F3F5", "#6B7280"),
    }.get(p, ("#F1F3F5", "#6B7280"))
    return (f'<span style="background:{stijl[0]};color:{stijl[1]};border-radius:4px;'
            f'padding:1px 7px;font-size:0.7rem;font-weight:600;">{p}</span>')


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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, label { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.01em;
                 color: #16204E !important; font-weight: 700 !important; }
h1 { font-size: 1.6rem !important; }
h2 { font-size: 1.25rem !important; }
h3 { font-size: 1.05rem !important; }

/* App-achtergrond: wit met heel lichte grijstint */
.stApp { background: #FAFBFC; }
.block-container { padding-top: 2.2rem; }

/* Zijbalk: wit, strak, blauwe accenten */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E8EAEE;
}
section[data-testid="stSidebar"] * { color: #374151; }
section[data-testid="stSidebar"] .stRadio label {
    padding: 2px 0;
    font-size: 0.92rem;
}
section[data-testid="stSidebar"] .stRadio label:hover { color: #2338B0; }
section[data-testid="stSidebar"] hr { border-color: #E8EAEE; }

/* Knoppen */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    border-radius: 6px;
    font-weight: 600;
    border: 1px solid #D8DCE3;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: #2338B0;
    border-color: #2338B0;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background: #1B2C8E;
    border-color: #1B2C8E;
}

/* Kanban-kaarten: wit, subtiele rand, dun kleuraccent links */
div.kanban-kaart {
    background: #FFFFFF;
    border: 1px solid #E8EAEE;
    border-left: 3px solid var(--kaartkleur, #2338B0);
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-size: 0.8rem;
    line-height: 1.5;
    color: #4B5563;
    box-shadow: 0 1px 2px rgba(22,32,78,0.04);
}
div.kanban-kaart:hover { box-shadow: 0 2px 6px rgba(22,32,78,0.10); }
div.kanban-kaart b { font-size: 0.85rem; color: #16204E; }
div.kanban-kaart .kaart-waarde { color: #16204E; font-weight: 600; }
div.kanban-kaart .kaart-meta { color: #6B7280; font-size: 0.75rem; }

/* Kolomkoppen: licht, met kleuraccent als stip */
div.kolomkop {
    font-size: 0.75rem;
    font-weight: 700;
    color: #374151;
    background: #F1F3F6;
    border: 1px solid #E8EAEE;
    border-top: 3px solid var(--kaartkleur, #2338B0);
    border-radius: 6px;
    padding: 6px 8px;
    margin-bottom: 8px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
div.kolomkop .kolom-som { color: #6B7280; font-weight: 500; text-transform: none; }

div.telaat { color: #B4443C; font-weight: 600; }

/* KPI-tegels */
.stat-tegel {
    background: #FFFFFF;
    border: 1px solid #E8EAEE;
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(22,32,78,0.04);
}
.stat-tegel .waarde { font-size: 1.5rem; font-weight: 700; color: #16204E; }
.stat-tegel .label { font-size: 0.7rem; color: #8A94A6; text-transform: uppercase;
                     letter-spacing: 0.06em; font-weight: 600; margin-top: 2px; }
.stat-tegel .waarde.alert { color: #B4443C; }

/* Tabellen strakker */
[data-testid="stDataFrame"] { border: 1px solid #E8EAEE; border-radius: 8px; }

/* Tabs in blauw */
.stTabs [data-baseweb="tab-highlight"] { background-color: #2338B0; }
.stTabs [aria-selected="true"] { color: #2338B0 !important; font-weight: 600; }

/* Expanders */
[data-testid="stExpander"] {
    border: 1px solid #E8EAEE;
    border-radius: 8px;
    background: #FFFFFF;
}

/* Geel accent voor kleine details */
.accent-geel { color: #C99E00; }
</style>
"""


def stat_tegel(kolom, waarde, label, alert: bool = False):
    klasse = "waarde alert" if alert else "waarde"
    kolom.markdown(
        f'<div class="stat-tegel"><div class="{klasse}">{waarde}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )
