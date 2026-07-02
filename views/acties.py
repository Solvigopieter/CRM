from datetime import date, timedelta

import streamlit as st

import db
import helpers as h


def toon():
    st.title("✅ Actieblad")

    # snelle nieuwe taak
    with st.expander("➕ Nieuwe actie", expanded=False):
        organisaties = db.organisatie_opties()
        partners = db.organisatie_opties(alleen_partners=True)
        sitelijst = db.site_opties()
        deals = db.deal_opties()
        with st.form("nieuwe_actie", clear_on_submit=True):
            actie = st.text_input("Actie *")
            c1, c2, c3 = st.columns(3)
            datum = c1.date_input("Datum", date.today() + timedelta(days=1))
            prioriteit = c2.selectbox("Prioriteit", h.PRIORITEITEN, index=1)
            verantwoordelijke = c3.selectbox("Verantwoordelijke", h.VERANTWOORDELIJKEN)
            c4, c5 = st.columns(2)
            organisatie_id = c4.selectbox("Klant", organisaties.keys(), format_func=organisaties.get)
            partner_id = c5.selectbox("Partner", partners.keys(), format_func=partners.get)
            c6, c7 = st.columns(2)
            site_id = c6.selectbox("Site", sitelijst.keys(), format_func=sitelijst.get)
            deal_id = c7.selectbox("Deal", deals.keys(), format_func=deals.get)
            herinnering = st.checkbox("➕ Ook automatische herinnering «opvolgen binnen 7 dagen» aanmaken")
            if st.form_submit_button("💾 Actie toevoegen", type="primary"):
                if not actie.strip():
                    st.error("Omschrijving is verplicht.")
                else:
                    basis = dict(prioriteit=prioriteit, organisatie_id=organisatie_id or None,
                                 partner_id=partner_id or None, site_id=site_id or None,
                                 deal_id=deal_id or None, verantwoordelijke=verantwoordelijke, status="Open")
                    db.voeg_toe("acties", dict(basis, datum=datum.isoformat(), actie=actie.strip()))
                    if herinnering:
                        db.voeg_toe("acties", dict(
                            basis, datum=(datum + timedelta(days=7)).isoformat(),
                            actie=f"Opvolgen: {actie.strip()}"))
                    st.success("Actie toegevoegd.")
                    st.rerun()

    f1, f2, f3 = st.columns(3)
    f_status = f1.multiselect("Status", h.ACTIE_STATUSSEN, default=["Open", "Bezig", "Wacht op klant", "Wacht op partner"])
    f_prior = f2.multiselect("Prioriteit", h.PRIORITEITEN)
    alleen_telaat = f3.checkbox("Alleen te laat")

    df = db.query_df("""
        SELECT a.id, a.datum, a.prioriteit, o.naam AS klant, s.naam AS site,
               p.naam AS partner, d.titel AS deal, a.actie, a.verantwoordelijke, a.status
        FROM acties a
        LEFT JOIN organisaties o ON o.id = a.organisatie_id
        LEFT JOIN organisaties p ON p.id = a.partner_id
        LEFT JOIN sites s ON s.id = a.site_id
        LEFT JOIN deals d ON d.id = a.deal_id
        ORDER BY a.datum""")

    if f_status:
        df = df[df["status"].isin(f_status)]
    if f_prior:
        df = df[df["prioriteit"].isin(f_prior)]
    df["te_laat"] = df.apply(lambda r: h.te_laat(r["datum"]) and r["status"] in ("Open", "Bezig"), axis=1)
    if alleen_telaat:
        df = df[df["te_laat"]]

    telaat_n = int(df["te_laat"].sum())
    if telaat_n:
        st.error(f"🔴 {telaat_n} actie(s) zijn te laat.")

    weergave = df.copy()
    weergave["datum"] = weergave.apply(lambda r: f"🔴 {r['datum']}" if r["te_laat"] else r["datum"], axis=1)
    weergave = weergave[["id", "datum", "prioriteit", "klant", "site", "partner",
                         "deal", "actie", "verantwoordelijke", "status"]]
    weergave.columns = ["ID", "Datum", "Prioriteit", "Klant", "Site", "Partner",
                        "Deal", "Actie", "Verantwoordelijke", "Status"]
    st.dataframe(weergave, use_container_width=True, hide_index=True)
    h.export_knop(weergave, "solvigo_acties.xlsx")

    st.subheader("Status wijzigen / actie verwijderen")
    if df.empty:
        st.info("Geen acties in deze selectie.")
        return
    keuzes = {int(r["id"]): f"#{r['id']} · {r['datum']} · {r['actie']}" for _, r in df.iterrows()}
    actie_id = st.selectbox("Kies actie", keuzes.keys(), format_func=keuzes.get)
    c1, c2, c3 = st.columns(3)
    nieuwe_status = c1.selectbox("Nieuwe status", h.ACTIE_STATUSSEN)
    with c2:
        st.write("")
        if st.button("💾 Status opslaan", use_container_width=True):
            db.werk_bij("acties", actie_id, {"status": nieuwe_status})
            st.success("Status bijgewerkt.")
            st.rerun()
    with c3:
        st.write("")
        if st.button("🗑️ Verwijder actie", use_container_width=True):
            db.verwijder("acties", actie_id)
            st.warning("Actie verwijderd.")
            st.rerun()
