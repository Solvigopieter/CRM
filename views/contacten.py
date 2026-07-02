import streamlit as st

import db
import helpers as h


def _formulier(contact: dict | None = None):
    contact = contact or {}
    organisaties = db.organisatie_opties()
    with st.form(f"contact_form_{contact.get('id', 'nieuw')}"):
        naam = st.text_input("Naam *", contact.get("naam", ""))
        c1, c2 = st.columns(2)
        organisatie_id = c1.selectbox("Organisatie", organisaties.keys(),
                                      index=h.sleutel_uit_opties(organisaties, contact.get("organisatie_id")),
                                      format_func=organisaties.get)
        rol = c2.selectbox("Rol", h.CONTACT_ROLLEN,
                           index=h.CONTACT_ROLLEN.index(contact["rol"])
                           if contact.get("rol") in h.CONTACT_ROLLEN else 0)
        c3, c4 = st.columns(2)
        functie = c3.text_input("Functie", contact.get("functie") or "")
        email = c4.text_input("E-mail", contact.get("email") or "")
        c5, c6 = st.columns(2)
        telefoon = c5.text_input("Telefoon", contact.get("telefoon") or "")
        linkedin = c6.text_input("LinkedIn", contact.get("linkedin") or "")
        notities = st.text_area("Notities / voorkeuren", contact.get("notities") or "")
        if st.form_submit_button("Opslaan", type="primary"):
            if not naam.strip():
                st.error("Naam is verplicht.")
                return
            data = dict(naam=naam.strip(), organisatie_id=organisatie_id or None, rol=rol,
                        functie=functie, email=email, telefoon=telefoon,
                        linkedin=linkedin, notities=notities)
            if contact.get("id"):
                db.werk_bij("contacten", contact["id"], data)
            else:
                db.voeg_toe("contacten", data)
            st.success("Contactpersoon opgeslagen.")
            st.rerun()


def toon():
    st.title("Contactpersonen")

    with st.expander("+ Nieuwe contactpersoon"):
        _formulier()

    df = db.query_df("""
        SELECT c.id, c.naam AS Naam, o.naam AS Organisatie, c.functie AS Functie,
               c.rol AS Rol, c.email AS 'E-mail', c.telefoon AS Telefoon,
               c.linkedin AS LinkedIn, c.notities AS Notities
        FROM contacten c LEFT JOIN organisaties o ON o.id = c.organisatie_id
        ORDER BY c.naam""")
    zoek = st.text_input("Zoek contact")
    if zoek:
        z = zoek.lower()
        df = df[df.apply(lambda r: z in str(r["Naam"]).lower()
                         or z in str(r["Organisatie"] or "").lower(), axis=1)]
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

    keuzes = {int(r["id"]): f"{r['Naam']} ({r['Organisatie'] or '—'})" for _, r in df.iterrows()}
    if keuzes:
        st.subheader("Bewerken of verwijderen")
        contact_id = st.selectbox("Kies contact", keuzes.keys(), format_func=keuzes.get)
        _formulier(db.haal_rij("contacten", contact_id))
        if st.button("Verwijder contactpersoon"):
            db.verwijder("contacten", contact_id)
            st.warning("Contactpersoon verwijderd.")
            st.rerun()
