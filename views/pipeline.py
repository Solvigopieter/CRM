from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db
import helpers as h


def _deal_formulier(deal: dict | None = None):
    """Formulier voor nieuwe deal of bewerken van bestaande deal."""
    deal = deal or {}
    klanten = db.organisatie_opties()
    partners = db.organisatie_opties(alleen_partners=True)
    sitelijst = db.site_opties()

    with st.form(f"deal_form_{deal.get('id', 'nieuw')}"):
        titel = st.text_input("Titel *", deal.get("titel", ""))
        c1, c2, c3 = st.columns(3)
        organisatie_id = c1.selectbox("Eindklant", klanten.keys(),
                                      index=h.sleutel_uit_opties(klanten, deal.get("organisatie_id")),
                                      format_func=klanten.get)
        partner_id = c2.selectbox("Partner (indien via installateur/O&M)", partners.keys(),
                                  index=h.sleutel_uit_opties(partners, deal.get("partner_id")),
                                  format_func=partners.get)
        site_id = c3.selectbox("PV-site", sitelijst.keys(),
                               index=h.sleutel_uit_opties(sitelijst, deal.get("site_id")),
                               format_func=sitelijst.get)

        contacten = db.contact_opties(organisatie_id or None) if organisatie_id else db.contact_opties()
        c4, c5, c6 = st.columns(3)
        contact_id = c4.selectbox("Contactpersoon", contacten.keys(),
                                  index=h.sleutel_uit_opties(contacten, deal.get("contact_id")),
                                  format_func=contacten.get)
        waarde = c5.number_input("Waarde (€)", min_value=0.0, value=float(deal.get("waarde") or 0), step=50.0)
        kans = c6.slider("Kans (%)", 0, 100, int(deal.get("kans") or 50), 5)

        c7, c8, c9 = st.columns(3)
        bron = c7.selectbox("Bron", h.BRONNEN,
                            index=h.BRONNEN.index(deal["bron"]) if deal.get("bron") in h.BRONNEN else 0)
        deadline = c8.date_input("Deadline", value=date.fromisoformat(deal["deadline"])
                                 if deal.get("deadline") else date.today() + timedelta(days=21))
        prioriteit = c9.selectbox("Prioriteit", h.PRIORITEITEN,
                                  index=h.PRIORITEITEN.index(deal.get("prioriteit", "Normaal")))

        c10, c11 = st.columns(2)
        stadium = c10.selectbox("Stadium", h.STADIUM_NAMEN,
                                index=h.STADIUM_NAMEN.index(deal.get("stadium", "Nieuwe lead")))
        verantwoordelijke = c11.selectbox("Verantwoordelijke", h.VERANTWOORDELIJKEN,
                                          index=h.VERANTWOORDELIJKEN.index(deal.get("verantwoordelijke"))
                                          if deal.get("verantwoordelijke") in h.VERANTWOORDELIJKEN else 0)

        opslaan = st.form_submit_button("Opslaan", type="primary")
        if opslaan:
            if not titel.strip():
                st.error("Titel is verplicht.")
                return
            data = dict(
                titel=titel.strip(), organisatie_id=organisatie_id or None,
                partner_id=partner_id or None, site_id=site_id or None,
                contact_id=contact_id or None, waarde=waarde, kans=kans, bron=bron,
                deadline=deadline.isoformat(), prioriteit=prioriteit,
                verantwoordelijke=verantwoordelijke, stadium=stadium,
                gewijzigd=date.today().isoformat(),
            )
            if deal.get("id"):
                oud_stadium = deal.get("stadium")
                db.werk_bij("deals", deal["id"], data)
                if stadium != oud_stadium:
                    actie = h.maak_vervolgactie(deal["id"], stadium)
                    if actie:
                        st.toast(f"Volgende actie aangemaakt: {actie}")
            else:
                nieuw_id = db.voeg_toe("deals", data)
                actie = h.maak_vervolgactie(nieuw_id, stadium)
                if actie:
                    st.toast(f"Volgende actie aangemaakt: {actie}")
            st.success("Deal opgeslagen.")
            st.rerun()


def _kaart(rij):
    kleur = h.STADIUM_KLEUR.get(rij["stadium"], "#2338B0")
    deadline_html = ""
    if rij["deadline"]:
        klasse = "telaat" if h.te_laat(rij["deadline"]) else "kaart-meta"
        deadline_html = f'<div class="{klasse}">Deadline: {rij["deadline"]}</div>'
    regels = [f'<div class="kaart-meta">{rij["klant"] or "—"}</div>']
    if rij["partner"]:
        regels.append(f'<div class="kaart-meta">via {rij["partner"]}</div>')
    if rij["site"]:
        regels.append(f'<div class="kaart-meta">{rij["site"]}</div>')
    actie_html = (f'<div class="kaart-meta">Volgende: {rij["volgende_actie"]}</div>'
                  if rij["volgende_actie"]
                  else '<div class="telaat">Geen open actie</div>')
    st.markdown(
        f'<div class="kanban-kaart" style="--kaartkleur:{kleur}">'
        f'<b>{rij["titel"]}</b>'
        f'{"".join(regels)}'
        f'<div><span class="kaart-waarde">{h.euro(rij["waarde"])}</span> '
        f'&nbsp;{h.prioriteit_badge(rij["prioriteit"])}</div>'
        f'{actie_html}{deadline_html}</div>',
        unsafe_allow_html=True,
    )


def toon():
    st.title("Pipeline")

    boven1, boven2 = st.columns([3, 1])
    zoek = boven1.text_input("Zoek op deal, klant, partner of site", "")
    with boven2:
        st.write("")
        nieuwe_lead = st.button("+ Nieuwe lead", type="primary", use_container_width=True)
    if nieuwe_lead:
        st.session_state["toon_nieuwe_deal"] = True
    if st.session_state.get("toon_nieuwe_deal"):
        with st.expander("Nieuwe deal aanmaken", expanded=True):
            _deal_formulier()
            if st.button("Sluiten", key="sluit_nieuw"):
                st.session_state["toon_nieuwe_deal"] = False
                st.rerun()

    # filters
    with st.expander("Filters"):
        f1, f2, f3, f4 = st.columns(4)
        partners = db.organisatie_opties(alleen_partners=True)
        f_stadia = f1.multiselect("Stadium", h.STADIUM_NAMEN)
        f_partner = f2.selectbox("Partner", partners.keys(), format_func=partners.get)
        f_prior = f3.multiselect("Prioriteit", h.PRIORITEITEN)
        f_verantw = f4.multiselect("Verantwoordelijke", h.VERANTWOORDELIJKEN)
        f5, f6, f7 = st.columns(3)
        f_vervuiling = f5.multiselect("Vervuilingstype (site)", h.VERVUILINGEN)
        f_regio = f6.text_input("Regio / gemeente bevat")
        f_minwaarde = f7.number_input("Minimale dealwaarde (€)", min_value=0, value=0, step=100)

    df = db.query_df("""
        SELECT d.*, o.naam AS klant, o.gemeente AS gemeente, p.naam AS partner,
               s.naam AS site, s.vervuiling AS vervuiling,
               (SELECT a.actie FROM acties a WHERE a.deal_id = d.id
                AND a.status IN ('Open','Bezig') ORDER BY a.datum LIMIT 1) AS volgende_actie
        FROM deals d
        LEFT JOIN organisaties o ON o.id = d.organisatie_id
        LEFT JOIN organisaties p ON p.id = d.partner_id
        LEFT JOIN sites s ON s.id = d.site_id
        ORDER BY d.deadline""")

    if zoek:
        z = zoek.lower()
        df = df[df.apply(lambda r: z in " ".join(
            str(r[k] or "").lower() for k in ("titel", "klant", "partner", "site")), axis=1)]
    if f_stadia:
        df = df[df["stadium"].isin(f_stadia)]
    if f_partner:
        df = df[df["partner_id"] == f_partner]
    if f_prior:
        df = df[df["prioriteit"].isin(f_prior)]
    if f_verantw:
        df = df[df["verantwoordelijke"].isin(f_verantw)]
    if f_vervuiling:
        df = df[df["vervuiling"].isin(f_vervuiling)]
    if f_regio:
        df = df[df["gemeente"].fillna("").str.lower().str.contains(f_regio.lower())]
    if f_minwaarde:
        df = df[df["waarde"].fillna(0) >= f_minwaarde]

    tab_kanban, tab_lijst, tab_beheer = st.tabs(["Kanban", "Lijst & export", "Deal bewerken"])

    with tab_kanban:
        toon_stadia = f_stadia or [s for s in h.STADIUM_NAMEN if s not in ("Afgerond", "Verloren")]
        # kolommen in rijen van 5 zodat het leesbaar blijft
        for start in range(0, len(toon_stadia), 5):
            rij_stadia = toon_stadia[start:start + 5]
            kolommen = st.columns(len(rij_stadia))
            for kolom, stadium in zip(kolommen, rij_stadia):
                sub = df[df["stadium"] == stadium]
                kleur = h.STADIUM_KLEUR.get(stadium, "#2338B0")
                with kolom:
                    st.markdown(
                        f'<div class="kolomkop" style="--kaartkleur:{kleur}">'
                        f'{stadium}<br><span class="kolom-som">{len(sub)} · {h.euro(sub["waarde"].sum())}</span></div>',
                        unsafe_allow_html=True)
                    for _, r in sub.iterrows():
                        _kaart(r)

    with tab_lijst:
        lijst = df[["id", "titel", "klant", "partner", "site", "stadium", "waarde",
                    "kans", "prioriteit", "deadline", "verantwoordelijke", "volgende_actie", "bron"]]
        lijst.columns = ["ID", "Titel", "Klant", "Partner", "Site", "Stadium", "Waarde (€)",
                         "Kans %", "Prioriteit", "Deadline", "Verantwoordelijke", "Volgende actie", "Bron"]
        st.dataframe(lijst, use_container_width=True, hide_index=True)
        h.export_knop(lijst, "solvigo_deals.xlsx")

    with tab_beheer:
        dealkeuzes = db.deal_opties()
        deal_id = st.selectbox("Kies deal", dealkeuzes.keys(), format_func=dealkeuzes.get)
        if deal_id:
            deal = db.haal_rij("deals", deal_id)
            st.markdown(f"### {deal['titel']}")

            # snelle stadiumwissel met automatische vervolgactie
            s1, s2 = st.columns([2, 1])
            nieuw_stadium = s1.selectbox("Verplaats naar stadium", h.STADIUM_NAMEN,
                                         index=h.STADIUM_NAMEN.index(deal["stadium"]))
            with s2:
                st.write("")
                if st.button("Verplaats", use_container_width=True) and nieuw_stadium != deal["stadium"]:
                    actie = h.wijzig_stadium(deal_id, nieuw_stadium)
                    st.success(f"Deal verplaatst naar «{nieuw_stadium}»."
                               + (f" Volgende actie: {actie}" if actie else ""))
                    st.rerun()

            _deal_formulier(deal)

            if st.button("Verwijder deze deal"):
                db.verwijder("deals", deal_id)
                st.warning("Deal verwijderd.")
                st.rerun()
