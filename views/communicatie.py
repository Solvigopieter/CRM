from datetime import date

import streamlit as st

import db
import helpers as h


def toon():
    st.title("💬 Communicatielog")

    with st.expander("➕ Nieuwe notitie", expanded=False):
        organisaties = db.organisatie_opties()
        partners = db.organisatie_opties(alleen_partners=True)
        deals = db.deal_opties()
        sitelijst = db.site_opties()
        contacten = db.contact_opties()
        with st.form("nieuwe_comm", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            datum = c1.date_input("Datum", date.today())
            type_ = c2.selectbox("Type", h.COMM_TYPES)
            contact_id = c3.selectbox("Contactpersoon", contacten.keys(), format_func=contacten.get)
            c4, c5 = st.columns(2)
            organisatie_id = c4.selectbox("Klant", organisaties.keys(), format_func=organisaties.get)
            partner_id = c5.selectbox("Partner", partners.keys(), format_func=partners.get)
            c6, c7 = st.columns(2)
            deal_id = c6.selectbox("Deal", deals.keys(), format_func=deals.get)
            site_id = c7.selectbox("Site", sitelijst.keys(), format_func=sitelijst.get)
            samenvatting = st.text_area("Korte samenvatting *")
            volgende_stap = st.text_input("Volgende stap")
            if st.form_submit_button("💾 Opslaan", type="primary"):
                if not samenvatting.strip():
                    st.error("Samenvatting is verplicht.")
                else:
                    db.voeg_toe("communicatie", dict(
                        datum=datum.isoformat(), type=type_,
                        organisatie_id=organisatie_id or None, partner_id=partner_id or None,
                        deal_id=deal_id or None, site_id=site_id or None,
                        contact_id=contact_id or None,
                        samenvatting=samenvatting.strip(), volgende_stap=volgende_stap))
                    st.success("Notitie opgeslagen.")
                    st.rerun()

    df = db.query_df("""
        SELECT c.id, c.datum AS Datum, c.type AS Type, o.naam AS Klant,
               p.naam AS Partner, d.titel AS Deal, s.naam AS Site, ct.naam AS Contact,
               c.samenvatting AS Samenvatting, c.volgende_stap AS 'Volgende stap'
        FROM communicatie c
        LEFT JOIN organisaties o ON o.id = c.organisatie_id
        LEFT JOIN organisaties p ON p.id = c.partner_id
        LEFT JOIN deals d ON d.id = c.deal_id
        LEFT JOIN sites s ON s.id = c.site_id
        LEFT JOIN contacten ct ON ct.id = c.contact_id
        ORDER BY c.datum DESC""")

    f1, f2 = st.columns(2)
    f_type = f1.multiselect("Type", h.COMM_TYPES)
    zoek = f2.text_input("🔍 Zoek in samenvattingen")
    if f_type:
        df = df[df["Type"].isin(f_type)]
    if zoek:
        df = df[df["Samenvatting"].fillna("").str.lower().str.contains(zoek.lower())]

    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

    if not df.empty:
        keuzes = {int(r["id"]): f"{r['Datum']} · {r['Type']} · {str(r['Samenvatting'])[:50]}"
                  for _, r in df.iterrows()}
        comm_id = st.selectbox("Notitie verwijderen", keuzes.keys(), format_func=keuzes.get)
        if st.button("🗑️ Verwijder notitie"):
            db.verwijder("communicatie", comm_id)
            st.warning("Notitie verwijderd.")
            st.rerun()
