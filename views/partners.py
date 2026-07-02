from datetime import date, timedelta

import streamlit as st

import db
import helpers as h


def toon():
    st.title("Partners")
    st.caption("Installateurs, O&M-bedrijven en andere tussenpersonen. "
               "Een partner is nooit automatisch de eindklant.")

    partners = db.query_df("""
        SELECT o.id, o.naam, o.type, o.gemeente, o.notities,
               (SELECT COUNT(*) FROM deals d WHERE d.partner_id = o.id) AS leads,
               (SELECT COUNT(*) FROM deals d WHERE d.partner_id = o.id
                AND d.stadium IN ('Goedgekeurd / in te plannen','In uitvoering','Uitgevoerd','Facturatie','Afgerond')) AS gewonnen,
               (SELECT COALESCE(SUM(d.waarde),0) FROM deals d WHERE d.partner_id = o.id
                AND d.stadium IN ('Goedgekeurd / in te plannen','In uitvoering','Uitgevoerd','Facturatie','Afgerond')) AS omzet,
               (SELECT COUNT(*) FROM deals d WHERE d.partner_id = o.id
                AND d.stadium NOT IN ('Afgerond','Verloren')) AS open_deals,
               (SELECT MAX(c.datum) FROM communicatie c WHERE c.partner_id = o.id) AS laatste_contact,
               (SELECT a.actie || ' (' || a.datum || ')' FROM acties a
                WHERE a.partner_id = o.id AND a.status IN ('Open','Bezig')
                ORDER BY a.datum LIMIT 1) AS volgende_actie
        FROM organisaties o
        WHERE o.type IN ('Installateur','O&M-bedrijf','Partner')
        ORDER BY omzet DESC""")

    weergave = partners.rename(columns={
        "naam": "Partner", "type": "Type", "gemeente": "Gemeente", "leads": "Leads",
        "gewonnen": "Gewonnen deals", "omzet": "Omzet via partner (€)",
        "open_deals": "Open deals", "laatste_contact": "Laatste contact",
        "volgende_actie": "Volgende actie"})
    st.dataframe(weergave.drop(columns=["id", "notities"]), use_container_width=True, hide_index=True)
    h.export_knop(weergave.drop(columns=["id", "notities"]), "solvigo_partners.xlsx")

    if partners.empty:
        st.info("Nog geen partners. Voeg een organisatie toe met type Installateur, O&M-bedrijf of Partner.")
        return

    keuzes = dict(zip(partners["id"], partners["naam"]))
    partner_id = st.selectbox("Open partner", keuzes.keys(), format_func=keuzes.get)
    partner = partners[partners["id"] == partner_id].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    h.stat_tegel(c1, int(partner["leads"]), "Aangebrachte leads")
    h.stat_tegel(c2, int(partner["gewonnen"]), "Gewonnen deals")
    h.stat_tegel(c3, h.euro(partner["omzet"]), "Omzet via partner")
    h.stat_tegel(c4, int(partner["open_deals"]), "Open deals")

    if partner["notities"]:
        st.info(f"Afspraken: {partner['notities']}")

    st.subheader("Contactpersonen")
    st.dataframe(db.query_df(
        "SELECT naam AS Naam, functie AS Functie, rol AS Rol, email AS 'E-mail', telefoon AS Telefoon "
        "FROM contacten WHERE organisatie_id = ?", (int(partner_id),)),
        use_container_width=True, hide_index=True)

    st.subheader("Deals via deze partner")
    st.dataframe(db.query_df("""
        SELECT d.titel AS Deal, o.naam AS Eindklant, s.naam AS Site, d.stadium AS Stadium,
               d.waarde AS 'Waarde (€)', d.deadline AS Deadline
        FROM deals d
        LEFT JOIN organisaties o ON o.id = d.organisatie_id
        LEFT JOIN sites s ON s.id = d.site_id
        WHERE d.partner_id = ? ORDER BY d.gewijzigd DESC""", (int(partner_id),)),
        use_container_width=True, hide_index=True)

    # snelle lead-conversie: partner geeft eindklant + site door → in één keer aanmaken
    st.subheader("Lead van partner omzetten naar eindklant + site + deal")
    st.caption("Bijv.: de installateur zegt «neem contact op met die persoon». "
               "Vul hieronder in wie de eindklant is en welke site gereinigd moet worden.")
    with st.form("lead_conversie"):
        c1, c2 = st.columns(2)
        klantnaam = c1.text_input("Naam eindklant *")
        gemeente = c2.text_input("Gemeente")
        c3, c4 = st.columns(2)
        contactnaam = c3.text_input("Contactpersoon eindklant")
        telefoon = c4.text_input("Telefoon contactpersoon")
        c5, c6, c7 = st.columns(3)
        sitenaam = c5.text_input("Naam PV-site *")
        panelen = c6.number_input("Aantal panelen (schatting)", min_value=0, value=0)
        waarde = c7.number_input("Geschatte dealwaarde (€)", min_value=0.0, value=0.0, step=100.0)
        omschrijving = st.text_input("Omschrijving deal", "Reiniging zonnepanelen")
        if st.form_submit_button("Lead aanmaken", type="primary"):
            if not klantnaam.strip() or not sitenaam.strip():
                st.error("Naam eindklant en naam site zijn verplicht.")
            else:
                klant_id = db.voeg_toe("organisaties", dict(
                    naam=klantnaam.strip(), type="Eindklant", gemeente=gemeente,
                    status="Prospect", relatietype="Prospect",
                    notities=f"Lead aangebracht door {partner['naam']}."))
                contact_id = None
                if contactnaam.strip():
                    contact_id = db.voeg_toe("contacten", dict(
                        organisatie_id=klant_id, naam=contactnaam.strip(),
                        telefoon=telefoon, rol="Beslisser"))
                site_id = db.voeg_toe("sites", dict(
                    naam=sitenaam.strip(), organisatie_id=klant_id,
                    partner_id=int(partner_id), aantal_panelen=panelen or None,
                    vervuiling="Onbekend", frequentie="Eenmalig"))
                deal_id = db.voeg_toe("deals", dict(
                    titel=f"{omschrijving} – {klantnaam.strip()}",
                    organisatie_id=klant_id, partner_id=int(partner_id),
                    site_id=site_id, contact_id=contact_id, waarde=waarde,
                    bron="Partner / installateur", stadium="Nieuwe lead",
                    deadline=(date.today() + timedelta(days=14)).isoformat()))
                h.maak_vervolgactie(deal_id, "Nieuwe lead")
                db.voeg_toe("communicatie", dict(
                    type="Interne nota", partner_id=int(partner_id),
                    organisatie_id=klant_id, deal_id=deal_id,
                    samenvatting=f"Lead doorgekregen van {partner['naam']}: {klantnaam.strip()} / {sitenaam.strip()}.",
                    volgende_stap="Klant contacteren."))
                st.success("Eindklant, site en deal aangemaakt. Actie «Klant contacteren» staat op het actieblad.")
                st.rerun()
