from datetime import date, timedelta

import streamlit as st

import db
import helpers as h


def _volgnummer() -> str:
    n = db.query_df("SELECT COUNT(*) n FROM offertes")["n"][0]
    return f"OFF-{date.today().year}-{n + 1:03d}"


def _maak_opvolging(offerte_id: int):
    """Na versturen automatisch opvolgtaak binnen 7 dagen."""
    off = db.haal_rij("offertes", offerte_id)
    deal = db.haal_rij("deals", off["deal_id"]) if off.get("deal_id") else None
    db.voeg_toe("acties", dict(
        datum=(date.today() + timedelta(days=7)).isoformat(),
        prioriteit="Normaal",
        organisatie_id=deal.get("organisatie_id") if deal else None,
        partner_id=deal.get("partner_id") if deal else None,
        site_id=off.get("site_id"),
        deal_id=off.get("deal_id"),
        actie=f"Offerte {off.get('nummer') or offerte_id} opvolgen",
        status="Open"))


def _formulier(off: dict | None = None):
    off = off or {}
    deals = db.deal_opties()
    sitelijst = db.site_opties()
    with st.form(f"off_form_{off.get('id', 'nieuw')}"):
        c1, c2, c3 = st.columns(3)
        nummer = c1.text_input("Offertenummer", off.get("nummer") or _volgnummer())
        deal_id = c2.selectbox("Deal", deals.keys(),
                               index=h.sleutel_uit_opties(deals, off.get("deal_id")),
                               format_func=deals.get)
        site_id = c3.selectbox("PV-site", sitelijst.keys(),
                               index=h.sleutel_uit_opties(sitelijst, off.get("site_id")),
                               format_func=sitelijst.get)
        c4, c5, c6 = st.columns(3)
        panelen = c4.number_input("Aantal panelen", min_value=0, value=int(off.get("aantal_panelen") or 0))
        oppervlakte = c5.number_input("Oppervlakte (m²)", min_value=0.0, value=float(off.get("oppervlakte") or 0))
        prijs_paneel = c6.number_input("Prijs per paneel (€)", min_value=0.0,
                                       value=float(off.get("prijs_per_paneel") or 0), step=0.1)
        c7, c8, c9 = st.columns(3)
        transport = c7.number_input("Transport (€)", min_value=0.0, value=float(off.get("transport") or 0))
        waterkost = c8.number_input("Waterkost (€)", min_value=0.0, value=float(off.get("waterkost") or 0))
        hoogtewerker = c9.number_input("Hoogtewerker (€)", min_value=0.0,
                                       value=float(off.get("hoogtewerker_kost") or 0))
        c10, c11 = st.columns(2)
        speciale = c10.text_input("Speciale vervuiling", off.get("speciale_vervuiling") or "")
        coating = c11.checkbox("Coating inbegrepen", bool(off.get("coating")))
        voorstel = panelen * prijs_paneel + transport + waterkost + hoogtewerker
        totaal = st.number_input("Totaalprijs (€)", min_value=0.0,
                                 value=float(off.get("totaalprijs") or voorstel), step=10.0,
                                 help=f"Berekend voorstel: € {voorstel:,.2f}")
        opmerkingen = st.text_area("Opmerkingen", off.get("opmerkingen") or "")
        status = st.selectbox("Status", h.OFFERTE_STATUSSEN,
                              index=h.OFFERTE_STATUSSEN.index(off.get("status", "Concept")))
        if st.form_submit_button("💾 Opslaan", type="primary"):
            data = dict(nummer=nummer, deal_id=deal_id or None, site_id=site_id or None,
                        aantal_panelen=panelen, oppervlakte=oppervlakte,
                        prijs_per_paneel=prijs_paneel, totaalprijs=totaal,
                        transport=transport, waterkost=waterkost, hoogtewerker_kost=hoogtewerker,
                        speciale_vervuiling=speciale, coating=int(coating),
                        opmerkingen=opmerkingen, status=status)
            oud_status = off.get("status")
            if off.get("id"):
                db.werk_bij("offertes", off["id"], data)
                offerte_id = off["id"]
            else:
                offerte_id = db.voeg_toe("offertes", dict(data, datum=date.today().isoformat()))
            if status == "Verstuurd" and oud_status != "Verstuurd":
                _maak_opvolging(offerte_id)
                st.toast("Opvolgtaak aangemaakt (over 7 dagen).")
            st.success("Offerte opgeslagen.")
            st.rerun()


def toon():
    st.title("🧾 Offertes")

    with st.expander("➕ Nieuwe offerte"):
        _formulier()

    df = db.query_df("""
        SELECT o.id, o.nummer AS Nummer, o.datum AS Datum, d.titel AS Deal, s.naam AS Site,
               o.aantal_panelen AS Panelen, o.prijs_per_paneel AS 'Prijs/paneel',
               o.transport AS Transport, o.waterkost AS Waterkost,
               o.hoogtewerker_kost AS Hoogtewerker, o.totaalprijs AS 'Totaal (€)',
               o.speciale_vervuiling AS 'Speciale vervuiling',
               CASE o.coating WHEN 1 THEN 'Ja' ELSE 'Nee' END AS Coating,
               o.status AS Status
        FROM offertes o
        LEFT JOIN deals d ON d.id = o.deal_id
        LEFT JOIN sites s ON s.id = o.site_id
        ORDER BY o.datum DESC""")
    f_status = st.multiselect("Filter op status", h.OFFERTE_STATUSSEN)
    if f_status:
        df = df[df["Status"].isin(f_status)]
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    h.export_knop(df.drop(columns=["id"]), "solvigo_offertes.xlsx")

    if df.empty:
        return
    keuzes = {int(r["id"]): f"{r['Nummer']} · {r['Deal'] or '—'}" for _, r in df.iterrows()}
    st.subheader("Offerte bewerken")
    offerte_id = st.selectbox("Kies offerte", keuzes.keys(), format_func=keuzes.get)
    _formulier(db.haal_rij("offertes", offerte_id))
    if st.button("🗑️ Verwijder offerte"):
        db.verwijder("offertes", offerte_id)
        st.warning("Offerte verwijderd.")
        st.rerun()
