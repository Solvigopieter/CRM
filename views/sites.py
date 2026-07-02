from pathlib import Path

import streamlit as st

import db
import helpers as h


def _formulier(site: dict | None = None):
    site = site or {}
    klanten = db.organisatie_opties(alleen_klanten=True)
    partners = db.organisatie_opties(alleen_partners=True)
    with st.form(f"site_form_{site.get('id', 'nieuw')}"):
        naam = st.text_input("Naam site *", site.get("naam", ""))
        adres = st.text_input("Adres", site.get("adres") or "")
        c1, c2 = st.columns(2)
        organisatie_id = c1.selectbox("Eindklant / eigenaar", klanten.keys(),
                                      index=h.sleutel_uit_opties(klanten, site.get("organisatie_id")),
                                      format_func=klanten.get)
        partner_id = c2.selectbox("Gekoppelde partner", partners.keys(),
                                  index=h.sleutel_uit_opties(partners, site.get("partner_id")),
                                  format_func=partners.get)
        c3, c4, c5 = st.columns(3)
        aantal = c3.number_input("Aantal panelen", min_value=0, value=int(site.get("aantal_panelen") or 0))
        kwp = c4.number_input("Totaal vermogen (kWp)", min_value=0.0, value=float(site.get("kwp") or 0), step=1.0)
        hellingsgraad = c5.text_input("Hellingsgraad", site.get("hellingsgraad") or "")
        c6, c7 = st.columns(2)
        daktype = c6.text_input("Daktype", site.get("daktype") or "")
        bereikbaarheid = c7.text_input("Bereikbaarheid", site.get("bereikbaarheid") or "")
        c8, c9, c10 = st.columns(3)
        waterpunt = c8.checkbox("Waterpunt aanwezig", bool(site.get("waterpunt")))
        hoogtewerker = c9.checkbox("Hoogtewerker nodig", bool(site.get("hoogtewerker")))
        vervuiling = c10.selectbox("Vervuilingstype", h.VERVUILINGEN,
                                   index=h.VERVUILINGEN.index(site["vervuiling"])
                                   if site.get("vervuiling") in h.VERVUILINGEN else len(h.VERVUILINGEN) - 1)
        c11, c12 = st.columns(2)
        frequentie = c11.selectbox("Reinigingsfrequentie", h.FREQUENTIES,
                                   index=h.FREQUENTIES.index(site["frequentie"])
                                   if site.get("frequentie") in h.FREQUENTIES else 0)
        veiligheid = c12.text_input("Veiligheidsrisico's", site.get("veiligheid") or "")
        notities = st.text_area("Notities", site.get("notities") or "")
        if st.form_submit_button("Opslaan", type="primary"):
            if not naam.strip():
                st.error("Naam is verplicht.")
                return
            data = dict(naam=naam.strip(), adres=adres, organisatie_id=organisatie_id or None,
                        partner_id=partner_id or None, aantal_panelen=aantal, kwp=kwp,
                        daktype=daktype, hellingsgraad=hellingsgraad, bereikbaarheid=bereikbaarheid,
                        waterpunt=int(waterpunt), hoogtewerker=int(hoogtewerker),
                        veiligheid=veiligheid, vervuiling=vervuiling,
                        frequentie=frequentie, notities=notities)
            if site.get("id"):
                db.werk_bij("sites", site["id"], data)
            else:
                db.voeg_toe("sites", data)
            st.success("Site opgeslagen.")
            st.rerun()


def bestanden_blok(entiteit: str, entiteit_id: int, categorien=("Document", "Foto voor", "Foto na")):
    """Herbruikbaar upload- en weergaveblok voor foto's/documenten."""
    st.markdown("**Foto's & documenten**")
    c1, c2 = st.columns([2, 1])
    upload = c1.file_uploader("Bestand toevoegen", key=f"up_{entiteit}_{entiteit_id}",
                              accept_multiple_files=False)
    categorie = c2.selectbox("Categorie", categorien, key=f"cat_{entiteit}_{entiteit_id}")
    if upload is not None and st.button("Uploaden", key=f"btn_{entiteit}_{entiteit_id}"):
        doelmap = db.UPLOAD_MAP / entiteit / str(entiteit_id)
        doelmap.mkdir(parents=True, exist_ok=True)
        pad = doelmap / upload.name
        pad.write_bytes(upload.getbuffer())
        db.voeg_toe("bestanden", dict(entiteit=entiteit, entiteit_id=entiteit_id,
                                      categorie=categorie, bestandsnaam=upload.name, pad=str(pad)))
        st.success("Bestand opgeslagen.")
        st.rerun()

    df = db.query_df("SELECT * FROM bestanden WHERE entiteit = ? AND entiteit_id = ?",
                     (entiteit, entiteit_id))
    for _, rij in df.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.write(f"· {rij['categorie']} — {rij['bestandsnaam']} ({rij['datum']})")
        pad = Path(rij["pad"])
        if pad.exists() and pad.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            c1.image(str(pad), width=260)
        if c2.button("Verwijder", key=f"delb_{rij['id']}"):
            db.verwijder("bestanden", int(rij["id"]))
            st.rerun()


def toon():
    st.title("PV-sites")

    with st.expander("+ Nieuwe PV-site"):
        _formulier()

    df = db.query_df("""
        SELECT s.id, s.naam AS Site, o.naam AS Eindklant, COALESCE(p.naam,'') AS Partner,
               s.adres AS Adres, s.aantal_panelen AS Panelen, s.kwp AS kWp,
               s.vervuiling AS Vervuiling, s.frequentie AS Frequentie,
               CASE s.waterpunt WHEN 1 THEN 'Ja' ELSE 'Nee' END AS Waterpunt,
               CASE s.hoogtewerker WHEN 1 THEN 'Ja' ELSE 'Nee' END AS Hoogtewerker
        FROM sites s
        LEFT JOIN organisaties o ON o.id = s.organisatie_id
        LEFT JOIN organisaties p ON p.id = s.partner_id
        ORDER BY s.naam""")
    zoek = st.text_input("Zoek site")
    if zoek:
        z = zoek.lower()
        df = df[df.apply(lambda r: z in str(r["Site"]).lower()
                         or z in str(r["Eindklant"] or "").lower(), axis=1)]
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    h.export_knop(df.drop(columns=["id"]), "solvigo_sites.xlsx")

    keuzes = db.site_opties()
    keuzes.pop(0, None)
    if keuzes:
        st.subheader("Site bekijken / bewerken")
        site_id = st.selectbox("Kies site", keuzes.keys(), format_func=keuzes.get)
        _formulier(db.haal_rij("sites", site_id))
        bestanden_blok("site", site_id)
        if st.button("Verwijder site"):
            db.verwijder("sites", site_id)
            st.warning("Site verwijderd.")
            st.rerun()
