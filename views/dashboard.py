import pandas as pd
import streamlit as st

import db
import helpers as h


def toon():
    st.title("📊 Dashboard")

    open_deals = db.query_df(
        "SELECT COUNT(*) n, COALESCE(SUM(waarde),0) w, COALESCE(SUM(waarde*kans/100.0),0) v "
        "FROM deals WHERE stadium NOT IN ('Afgerond','Verloren')")
    acties_vandaag = db.query_df(
        "SELECT COUNT(*) n FROM acties WHERE status IN ('Open','Bezig') AND datum = date('now')")["n"][0]
    acties_telaat = db.query_df(
        "SELECT COUNT(*) n FROM acties WHERE status IN ('Open','Bezig') AND datum < date('now')")["n"][0]
    bezoeken = db.query_df(
        "SELECT COUNT(*) n FROM plaatsbezoeken WHERE datum >= date('now')")["n"][0]

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    h.stat_tegel(k1, int(open_deals["n"][0]), "Open deals")
    h.stat_tegel(k2, h.euro(open_deals["w"][0]), "Pipelinewaarde")
    h.stat_tegel(k3, h.euro(open_deals["v"][0]), "Verwachte omzet (gewogen)")
    h.stat_tegel(k4, acties_vandaag, "Acties vandaag")
    h.stat_tegel(k5, f"🔴 {acties_telaat}" if acties_telaat else "🟢 0", "Achterstallige acties")
    h.stat_tegel(k6, bezoeken, "Plaatsbezoeken gepland")

    st.write("")
    links, rechts = st.columns(2)

    with links:
        st.subheader("Deals per stadium")
        per_stadium = db.query_df(
            "SELECT stadium, COUNT(*) aantal, COALESCE(SUM(waarde),0) waarde FROM deals GROUP BY stadium")
        per_stadium["volgorde"] = per_stadium["stadium"].apply(
            lambda s: h.STADIUM_NAMEN.index(s) if s in h.STADIUM_NAMEN else 99)
        per_stadium = per_stadium.sort_values("volgorde")
        st.bar_chart(per_stadium.set_index("stadium")["aantal"])

        st.subheader("Leads per bron")
        per_bron = db.query_df("SELECT COALESCE(bron,'Onbekend') bron, COUNT(*) aantal FROM deals GROUP BY bron")
        st.bar_chart(per_bron.set_index("bron")["aantal"])

    with rechts:
        st.subheader("Omzet per partner")
        per_partner = db.query_df("""
            SELECT p.naam AS partner, COALESCE(SUM(d.waarde),0) omzet, COUNT(*) deals
            FROM deals d JOIN organisaties p ON p.id = d.partner_id
            GROUP BY p.naam ORDER BY omzet DESC""")
        if per_partner.empty:
            st.info("Nog geen deals via partners.")
        else:
            st.bar_chart(per_partner.set_index("partner")["omzet"])

        st.subheader("Conversie offerte → opdracht")
        off = db.query_df("SELECT status, COUNT(*) n FROM offertes GROUP BY status")
        verstuurd = int(off.loc[off["status"].isin(["Verstuurd", "Goedgekeurd", "Verloren", "Verlopen"]), "n"].sum())
        goedgekeurd = int(off.loc[off["status"] == "Goedgekeurd", "n"].sum())
        conversie = f"{goedgekeurd / verstuurd * 100:.0f}%" if verstuurd else "—"
        c1, c2, c3 = st.columns(3)
        h.stat_tegel(c1, verstuurd, "Offertes verstuurd")
        h.stat_tegel(c2, goedgekeurd, "Goedgekeurd")
        h.stat_tegel(c3, conversie, "Conversie")

    st.subheader("🏆 Top 10 grootste open opportuniteiten")
    top = db.query_df("""
        SELECT d.titel AS Deal, o.naam AS Klant, COALESCE(p.naam,'') AS Partner,
               d.stadium AS Stadium, d.waarde AS Waarde, d.kans AS 'Kans %', d.deadline AS Deadline
        FROM deals d
        LEFT JOIN organisaties o ON o.id = d.organisatie_id
        LEFT JOIN organisaties p ON p.id = d.partner_id
        WHERE d.stadium NOT IN ('Afgerond','Verloren')
        ORDER BY d.waarde DESC LIMIT 10""")
    st.dataframe(top, use_container_width=True, hide_index=True)
