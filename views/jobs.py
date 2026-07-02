from datetime import date, timedelta

import streamlit as st

import db
import helpers as h
from views.sites import bestanden_blok


def _maak_facturatietaak(job_id: int):
    job = db.haal_rij("jobs", job_id)
    deal = db.haal_rij("deals", job["deal_id"]) if job.get("deal_id") else None
    bestaand = db.query_df(
        "SELECT id FROM acties WHERE deal_id IS ? AND actie = 'Facturatie controleren' "
        "AND status IN ('Open','Bezig')", (job.get("deal_id"),))
    if not bestaand.empty:
        return
    db.voeg_toe("acties", dict(
        datum=(date.today() + timedelta(days=2)).isoformat(),
        prioriteit="Hoog",
        organisatie_id=deal.get("organisatie_id") if deal else None,
        partner_id=deal.get("partner_id") if deal else None,
        site_id=job.get("site_id"), deal_id=job.get("deal_id"),
        actie="Facturatie controleren", status="Open"))


def _formulier(job: dict | None = None):
    job = job or {}
    # jobs worden gemaakt vanuit gewonnen deals
    deals_gewonnen = db.query_df("""
        SELECT id, titel FROM deals
        WHERE stadium IN ('Goedgekeurd / in te plannen','In uitvoering','Uitgevoerd','Facturatie','Afgerond')
        ORDER BY id DESC""")
    deals = {0: "— geen —"}
    deals.update(dict(zip(deals_gewonnen["id"], deals_gewonnen["titel"])))
    sitelijst = db.site_opties()
    with st.form(f"job_form_{job.get('id', 'nieuw')}"):
        c1, c2, c3 = st.columns(3)
        deal_id = c1.selectbox("Deal (gewonnen)", deals.keys(),
                               index=h.sleutel_uit_opties(deals, job.get("deal_id")),
                               format_func=deals.get)
        site_id = c2.selectbox("PV-site", sitelijst.keys(),
                               index=h.sleutel_uit_opties(sitelijst, job.get("site_id")),
                               format_func=sitelijst.get)
        datum = c3.date_input("Uitvoeringsdatum", date.fromisoformat(job["datum"])
                              if job.get("datum") else date.today() + timedelta(days=7))
        c4, c5 = st.columns(2)
        team = c4.text_input("Team", job.get("team") or "Pieter")
        water = c5.text_input("Water nodig", job.get("water") or "")
        materiaal = st.text_input("Materiaal", job.get("materiaal") or "")
        c6, c7, c8 = st.columns(3)
        robot = c6.checkbox("Robot nodig", bool(job.get("robot", 1)))
        hoogtewerker = c7.checkbox("Hoogtewerker nodig", bool(job.get("hoogtewerker")))
        status = c8.selectbox("Status", h.JOB_STATUSSEN,
                              index=h.JOB_STATUSSEN.index(job.get("status", "Gepland")))
        veiligheid = st.text_area("Veiligheidsinstructies", job.get("veiligheidsinstructies") or "")
        werkverslag = st.text_area("Werkverslag", job.get("werkverslag") or "")
        if st.form_submit_button("💾 Opslaan", type="primary"):
            data = dict(deal_id=deal_id or None, site_id=site_id or None,
                        datum=datum.isoformat(), team=team, water=water, materiaal=materiaal,
                        robot=int(robot), hoogtewerker=int(hoogtewerker),
                        veiligheidsinstructies=veiligheid, status=status, werkverslag=werkverslag)
            oud_status = job.get("status")
            if job.get("id"):
                db.werk_bij("jobs", job["id"], data)
                job_id = job["id"]
            else:
                job_id = db.voeg_toe("jobs", data)
            if status == "Uitgevoerd" and oud_status != "Uitgevoerd":
                _maak_facturatietaak(job_id)
                if deal_id:
                    h.wijzig_stadium(deal_id, "Uitgevoerd")
                st.toast("Taak «Facturatie controleren» aangemaakt.")
            st.success("Job opgeslagen.")
            st.rerun()


def toon():
    st.title("🛠️ Uitvoering / Jobs")

    with st.expander("➕ Nieuwe job (vanuit gewonnen deal)"):
        _formulier()

    df = db.query_df("""
        SELECT j.id, j.datum AS Datum, d.titel AS Deal, s.naam AS Site, j.team AS Team,
               CASE j.robot WHEN 1 THEN 'Ja' ELSE 'Nee' END AS Robot,
               CASE j.hoogtewerker WHEN 1 THEN 'Ja' ELSE 'Nee' END AS Hoogtewerker,
               j.water AS Water, j.status AS Status
        FROM jobs j
        LEFT JOIN deals d ON d.id = j.deal_id
        LEFT JOIN sites s ON s.id = j.site_id
        ORDER BY j.datum DESC""")
    f_status = st.multiselect("Filter op status", h.JOB_STATUSSEN)
    if f_status:
        df = df[df["Status"].isin(f_status)]
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    h.export_knop(df.drop(columns=["id"]), "solvigo_jobs.xlsx")

    if df.empty:
        return
    keuzes = {int(r["id"]): f"#{r['id']} · {r['Datum']} · {r['Site'] or r['Deal'] or '—'}"
              for _, r in df.iterrows()}
    st.subheader("Job bewerken")
    job_id = st.selectbox("Kies job", keuzes.keys(), format_func=keuzes.get)
    _formulier(db.haal_rij("jobs", job_id))
    bestanden_blok("job", job_id, ("Foto voor", "Foto na", "Document"))
    if st.button("🗑️ Verwijder job"):
        db.verwijder("jobs", job_id)
        st.warning("Job verwijderd.")
        st.rerun()
