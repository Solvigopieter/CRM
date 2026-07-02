import streamlit as st

import db
import helpers as h


def _formulier(org: dict | None = None):
    org = org or {}
    with st.form(f"org_form_{org.get('id', 'nieuw')}"):
        naam = st.text_input("Naam *", org.get("naam", ""))
        c1, c2, c3 = st.columns(3)
        type_ = c1.selectbox("Type", h.ORG_TYPES,
                             index=h.ORG_TYPES.index(org.get("type", "Eindklant")))
        status = c2.selectbox("Status", h.ORG_STATUSSEN,
                              index=h.ORG_STATUSSEN.index(org.get("status", "Prospect")))
        relatietype = c3.selectbox("Relatietype", h.RELATIETYPES,
                                   index=h.RELATIETYPES.index(org.get("relatietype", "Prospect")))
        c4, c5, c6 = st.columns(3)
        btw = c4.text_input("BTW-nummer", org.get("btw") or "")
        sector = c5.text_input("Sector", org.get("sector") or "")
        website = c6.text_input("Website", org.get("website") or "")
        c7, c8 = st.columns(2)
        adres = c7.text_input("Adres", org.get("adres") or "")
        gemeente = c8.text_input("Gemeente", org.get("gemeente") or "")
        notities = st.text_area("Notities", org.get("notities") or "")
        if st.form_submit_button("💾 Opslaan", type="primary"):
            if not naam.strip():
                st.error("Naam is verplicht.")
                return
            data = dict(naam=naam.strip(), type=type_, status=status, relatietype=relatietype,
                        btw=btw, sector=sector, website=website, adres=adres,
                        gemeente=gemeente, notities=notities)
            if org.get("id"):
                db.werk_bij("organisaties", org["id"], data)
            else:
                db.voeg_toe("organisaties", data)
            st.success("Organisatie opgeslagen.")
            st.rerun()


def _klantenfiche(org_id: int):
    org = db.haal_rij("organisaties", org_id)
    st.markdown(f"## 🏢 {org['naam']}")
    terugkerend = " · 🔁 **Actieve terugkerende klant**" if org["relatietype"] in (
        "Terugkerende klant", "Strategische partner") else ""
    st.markdown(
        f"**{org['type']}** · status **{org['status']}** · relatietype **{org['relatietype']}**{terugkerend}")
    c1, c2, c3 = st.columns(3)
    c1.write(f"📍 {org['adres'] or '—'}, {org['gemeente'] or ''}")
    c2.write(f"🧾 BTW: {org['btw'] or '—'}")
    c3.write(f"🌐 {org['website'] or '—'}")
    if org["notities"]:
        st.info(org["notities"])

    tabs = st.tabs(["Contactpersonen", "Sites", "Deals", "Offertes", "Taken",
                    "Plaatsbezoeken", "Communicatie", "Reinigingshistoriek", "Bewerken"])

    with tabs[0]:
        st.dataframe(db.query_df(
            "SELECT naam AS Naam, functie AS Functie, rol AS Rol, email AS 'E-mail', "
            "telefoon AS Telefoon, notities AS Notities FROM contacten WHERE organisatie_id = ?",
            (org_id,)), use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(db.query_df("""
            SELECT s.naam AS Site, s.adres AS Adres, s.aantal_panelen AS Panelen,
                   s.kwp AS kWp, s.vervuiling AS Vervuiling, s.frequentie AS Frequentie,
                   COALESCE(p.naam,'') AS Partner
            FROM sites s LEFT JOIN organisaties p ON p.id = s.partner_id
            WHERE s.organisatie_id = ?""", (org_id,)), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.dataframe(db.query_df("""
            SELECT titel AS Deal, stadium AS Stadium, waarde AS 'Waarde (€)',
                   kans AS 'Kans %', deadline AS Deadline
            FROM deals WHERE organisatie_id = ? ORDER BY gewijzigd DESC""", (org_id,)),
            use_container_width=True, hide_index=True)

    with tabs[3]:
        st.dataframe(db.query_df("""
            SELECT o.nummer AS Nummer, o.datum AS Datum, o.totaalprijs AS 'Totaal (€)',
                   o.status AS Status, d.titel AS Deal
            FROM offertes o LEFT JOIN deals d ON d.id = o.deal_id
            WHERE d.organisatie_id = ?""", (org_id,)), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.dataframe(db.query_df("""
            SELECT datum AS Datum, actie AS Actie, prioriteit AS Prioriteit, status AS Status
            FROM acties WHERE organisatie_id = ? ORDER BY datum""", (org_id,)),
            use_container_width=True, hide_index=True)

    with tabs[5]:
        st.dataframe(db.query_df("""
            SELECT b.datum AS Datum, s.naam AS Site, b.vervuilingsgraad AS Vervuilingsgraad,
                   b.conclusie AS Conclusie, b.advies AS Advies
            FROM plaatsbezoeken b
            LEFT JOIN sites s ON s.id = b.site_id
            LEFT JOIN deals d ON d.id = b.deal_id
            WHERE d.organisatie_id = ? OR s.organisatie_id = ?""", (org_id, org_id)),
            use_container_width=True, hide_index=True)

    with tabs[6]:
        st.dataframe(db.query_df("""
            SELECT c.datum AS Datum, c.type AS Type, ct.naam AS Contact,
                   c.samenvatting AS Samenvatting, c.volgende_stap AS 'Volgende stap'
            FROM communicatie c LEFT JOIN contacten ct ON ct.id = c.contact_id
            WHERE c.organisatie_id = ? ORDER BY c.datum DESC""", (org_id,)),
            use_container_width=True, hide_index=True)

    with tabs[7]:
        st.dataframe(db.query_df("""
            SELECT j.datum AS Datum, s.naam AS Site, j.status AS Status,
                   j.team AS Team, j.werkverslag AS Werkverslag
            FROM jobs j
            LEFT JOIN sites s ON s.id = j.site_id
            LEFT JOIN deals d ON d.id = j.deal_id
            WHERE d.organisatie_id = ? OR s.organisatie_id = ?
            ORDER BY j.datum DESC""", (org_id, org_id)),
            use_container_width=True, hide_index=True)

    with tabs[8]:
        _formulier(org)
        if st.button("🗑️ Verwijder organisatie", key=f"del_org_{org_id}"):
            db.verwijder("organisaties", org_id)
            st.warning("Organisatie verwijderd.")
            st.rerun()


def toon():
    st.title("🏢 Organisaties & klantenfiche")

    with st.expander("➕ Nieuwe organisatie"):
        _formulier()

    df = db.query_df("""
        SELECT id, naam AS Naam, type AS Type, gemeente AS Gemeente, sector AS Sector,
               status AS Status, relatietype AS Relatietype
        FROM organisaties ORDER BY naam""")
    zoek = st.text_input("🔍 Zoek organisatie")
    if zoek:
        df = df[df["Naam"].str.lower().str.contains(zoek.lower())]
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    h.export_knop(df.drop(columns=["id"]), "solvigo_klanten.xlsx")

    st.divider()
    keuzes = db.organisatie_opties()
    keuzes.pop(0, None)
    if keuzes:
        org_id = st.selectbox("Open klantenfiche", keuzes.keys(), format_func=keuzes.get)
        _klantenfiche(org_id)
