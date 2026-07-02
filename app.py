"""
Solvigo CRM – hoofdapp
Start met:  streamlit run app.py
"""
import streamlit as st

import db
import seed
import helpers
from views import (
    dashboard, pipeline, acties, organisaties, contacten, sites,
    plaatsbezoeken, partners, offertes, jobs, communicatie,
)

st.set_page_config(
    page_title="Solvigo CRM",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()
seed.seed_indien_leeg()

st.markdown(helpers.CSS, unsafe_allow_html=True)

PAGINAS = {
    "Dashboard": dashboard.toon,
    "Pipeline": pipeline.toon,
    "Actieblad": acties.toon,
    "Organisaties": organisaties.toon,
    "Contactpersonen": contacten.toon,
    "PV-sites": sites.toon,
    "Plaatsbezoeken": plaatsbezoeken.toon,
    "Partners": partners.toon,
    "Offertes": offertes.toon,
    "Uitvoering / Jobs": jobs.toon,
    "Communicatielog": communicatie.toon,
}

with st.sidebar:
    from pathlib import Path as _Path
    _logo = _Path(__file__).parent / "logo.png"
    if _logo.exists():
        st.image(str(_logo), width=130)
    else:
        st.markdown("## Solvigo CRM")
    st.caption("PV-cleaning · leads, deals & opvolging")
    st.divider()
    keuze = st.radio("Navigatie", list(PAGINAS.keys()), label_visibility="collapsed")
    st.divider()

    # snelle indicatoren in de zijbalk
    open_deals = db.query_df(
        "SELECT COUNT(*) n FROM deals WHERE stadium NOT IN ('Afgerond','Verloren')")["n"][0]
    telaat = db.query_df(
        "SELECT COUNT(*) n FROM acties WHERE status IN ('Open','Bezig') AND datum < date('now')")["n"][0]
    st.markdown(f"**{int(open_deals)}** open deals")
    if telaat:
        st.markdown(
            f'<span style="color:#B4443C;font-weight:600;">{int(telaat)} acties te laat</span>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#1E8E5A;">Geen achterstallige acties</span>',
            unsafe_allow_html=True)
    st.caption(f"Opslag: {db.opslag_label()}")

PAGINAS[keuze]()
