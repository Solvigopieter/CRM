from datetime import date

import streamlit as st

import db
import helpers as h
from views.sites import bestanden_blok


def _formulier(bezoek: dict | None = None):
    bezoek = bezoek or {}
    deals = db.deal_opties()
    sitelijst = db.site_opties()
    with st.form(f"bezoek_form_{bezoek.get('id', 'nieuw')}"):
        c1, c2, c3 = st.columns(3)
        deal_id = c1.selectbox("Deal", deals.keys(),
                               index=h.sleutel_uit_opties(deals, bezoek.get("deal_id")),
                               format_func=deals.get)
        site_id = c2.selectbox("PV-site", sitelijst.keys(),
                               index=h.sleutel_uit_opties(sitelijst, bezoek.get("site_id")),
                               format_func=sitelijst.get)
        datum = c3.date_input("Datum bezoek", date.fromisoformat(bezoek["datum"])
                              if bezoek.get("datum") else date.today())
        aanwezigen = st.text_input("Aanwezige personen", bezoek.get("aanwezigen") or "")
        technisch = st.text_area("Technische opmerkingen", bezoek.get("technische_opmerkingen") or "")
        c4, c5 = st.columns(2)
        bereikbaarheid = c4.text_input("Bereikbaarheid dak", bezoek.get("bereikbaarheid") or "")
        water = c5.text_input("Wateraansluiting", bezoek.get("wateraansluiting") or "")
        c6, c7 = st.columns(2)
        veiligheid = c6.text_input("Veiligheid", bezoek.get("veiligheid") or "")
        materialen = c7.text_input("Benodigde materialen", bezoek.get("materialen") or "")
        c8, c9, c10, c11 = st.columns(4)
        hoogtewerker = c8.checkbox("Hoogtewerker nodig", bool(bezoek.get("hoogtewerker")))
        reinigingstijd = c9.text_input("Geschatte reinigingstijd", bezoek.get("reinigingstijd") or "")
        panelen = c10.number_input("Panelen gecontroleerd", min_value=0,
                                   value=int(bezoek.get("panelen_gecontroleerd") or 0))
        graad = c11.text_input("Vervuilingsgraad", bezoek.get("vervuilingsgraad") or "")
        conclusie = st.text_area("Interne conclusie", bezoek.get("conclusie") or "")
        advies = st.text_area("Advies voor klant", bezoek.get("advies") or "")
        if st.form_submit_button("Opslaan", type="primary"):
            data = dict(deal_id=deal_id or None, site_id=site_id or None, datum=datum.isoformat(),
                        aanwezigen=aanwezigen, technische_opmerkingen=technisch,
                        bereikbaarheid=bereikbaarheid, wateraansluiting=water,
                        veiligheid=veiligheid, materialen=materialen,
                        hoogtewerker=int(hoogtewerker), reinigingstijd=reinigingstijd,
                        panelen_gecontroleerd=panelen, vervuilingsgraad=graad,
                        conclusie=conclusie, advies=advies)
            if bezoek.get("id"):
                db.werk_bij("plaatsbezoeken", bezoek["id"], data)
            else:
                db.voeg_toe("plaatsbezoeken", data)
            st.success("Plaatsbezoek opgeslagen.")
            st.rerun()


def _verslag(bezoek: dict):
    """Gestructureerd verslag, bruikbaar voor offerte of uitvoering."""
    sitenaam = ""
    if bezoek.get("site_id"):
        site = db.haal_rij("sites", bezoek["site_id"])
        sitenaam = site["naam"] if site else ""
    dealtitel = ""
    if bezoek.get("deal_id"):
        deal = db.haal_rij("deals", bezoek["deal_id"])
        dealtitel = deal["titel"] if deal else ""
    st.markdown(f"""
### Verslag plaatsbezoek — {bezoek.get('datum', '')}
**Deal:** {dealtitel or '—'} · **Site:** {sitenaam or '—'}

| Onderdeel | Vaststelling |
|---|---|
| Aanwezigen | {bezoek.get('aanwezigen') or '—'} |
| Bereikbaarheid dak | {bezoek.get('bereikbaarheid') or '—'} |
| Wateraansluiting | {bezoek.get('wateraansluiting') or '—'} |
| Veiligheid | {bezoek.get('veiligheid') or '—'} |
| Benodigde materialen | {bezoek.get('materialen') or '—'} |
| Hoogtewerker nodig | {'Ja' if bezoek.get('hoogtewerker') else 'Nee'} |
| Geschatte reinigingstijd | {bezoek.get('reinigingstijd') or '—'} |
| Panelen gecontroleerd | {bezoek.get('panelen_gecontroleerd') or '—'} |
| Vervuilingsgraad | {bezoek.get('vervuilingsgraad') or '—'} |

**Technische opmerkingen:** {bezoek.get('technische_opmerkingen') or '—'}

**Interne conclusie:** {bezoek.get('conclusie') or '—'}

**Advies voor klant:** {bezoek.get('advies') or '—'}
""")


def toon():
    st.title("Plaatsbezoeken")

    with st.expander("+ Nieuw plaatsbezoek"):
        _formulier()

    df = db.query_df("""
        SELECT b.id, b.datum AS Datum, d.titel AS Deal, s.naam AS Site,
               b.vervuilingsgraad AS Vervuilingsgraad,
               CASE b.hoogtewerker WHEN 1 THEN 'Ja' ELSE 'Nee' END AS Hoogtewerker,
               b.reinigingstijd AS Reinigingstijd
        FROM plaatsbezoeken b
        LEFT JOIN deals d ON d.id = b.deal_id
        LEFT JOIN sites s ON s.id = b.site_id
        ORDER BY b.datum DESC""")
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

    if df.empty:
        return
    keuzes = {int(r["id"]): f"{r['Datum']} · {r['Site'] or r['Deal'] or '—'}" for _, r in df.iterrows()}
    bezoek_id = st.selectbox("Open plaatsbezoek", keuzes.keys(), format_func=keuzes.get)
    bezoek = db.haal_rij("plaatsbezoeken", bezoek_id)

    tab_verslag, tab_bewerken, tab_fotos = st.tabs(["Verslag", "Bewerken", "Foto's"])
    with tab_verslag:
        _verslag(bezoek)
    with tab_bewerken:
        _formulier(bezoek)
        if st.button("Verwijder plaatsbezoek"):
            db.verwijder("plaatsbezoeken", bezoek_id)
            st.warning("Plaatsbezoek verwijderd.")
            st.rerun()
    with tab_fotos:
        bestanden_blok("plaatsbezoek", bezoek_id, ("Foto voor", "Foto na", "Document"))
