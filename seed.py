"""
Solvigo CRM – voorbeelddata
Wordt eenmalig geladen als de database leeg is.
"""
from datetime import date, timedelta

import db


def _d(dagen: int) -> str:
    return (date.today() + timedelta(days=dagen)).isoformat()


def seed_indien_leeg():
    if not db.moet_seed_demo_data():
        return
    if not db.query_df("SELECT id FROM organisaties LIMIT 1").empty:
        return

    # --- organisaties ---
    org = {}
    org["hoeve"] = db.voeg_toe("organisaties", dict(
        naam="Hoeve Van den Broeck", type="Eindklant", btw="BE 0456.789.123",
        adres="Zandstraat 12", gemeente="Geel", sector="Landbouw (melkvee)",
        status="Actief", relatietype="Terugkerende klant",
        notities="Stallen met veel landbouwstof. Jaarlijkse reiniging afgesproken."))
    org["logistiek"] = db.voeg_toe("organisaties", dict(
        naam="TransKempen Logistics", type="Eindklant", btw="BE 0678.123.456",
        adres="Industrieweg 45", gemeente="Westerlo", sector="Logistiek",
        status="Prospect", relatietype="Prospect",
        notities="Groot plat dak, 1.800 panelen. Lead via Argona."))
    org["serre"] = db.voeg_toe("organisaties", dict(
        naam="Tuinbouw Peeters bv", type="Eindklant", btw="BE 0789.456.123",
        adres="Kanaaldijk 8", gemeente="Hoogstraten", sector="Tuinbouw",
        status="Prospect", relatietype="Prospect",
        notities="Korstmos op oudere installatie, vraagt proefstuk."))
    org["particulier"] = db.voeg_toe("organisaties", dict(
        naam="Familie Janssens", type="Eindklant",
        adres="Lindelaan 3", gemeente="Herentals", sector="Particulier",
        status="Actief", relatietype="Eenmalige klant",
        notities="Reiniging uitgevoerd in mei, tevreden klant."))
    org["argona"] = db.voeg_toe("organisaties", dict(
        naam="Argona", type="Installateur", btw="BE 0555.222.111",
        adres="Nijverheidsstraat 20", gemeente="Turnhout", sector="PV-installatie",
        website="https://www.argona.be", status="Partner", relatietype="Strategische partner",
        notities="Geeft leads door voor industriële daken. Commissieafspraak 5%."))
    org["solora"] = db.voeg_toe("organisaties", dict(
        naam="Solora", type="O&M-bedrijf", btw="BE 0444.333.222",
        adres="Ambachtslaan 7", gemeente="Mol", sector="O&M zonneparken",
        status="Partner", relatietype="Partner",
        notities="Kadergesprek gehad, wacht op eerste concrete site."))

    # --- contacten ---
    con = {}
    con["bart"] = db.voeg_toe("contacten", dict(
        organisatie_id=org["hoeve"], naam="Bart Van den Broeck", functie="Zaakvoerder",
        email="bart@hoevevdb.be", telefoon="0475 12 34 56", rol="Beslisser",
        notities="Bellen na 18u, overdag in de stallen."))
    con["ilse"] = db.voeg_toe("contacten", dict(
        organisatie_id=org["logistiek"], naam="Ilse Mertens", functie="Facility Manager",
        email="ilse.mertens@transkempen.be", telefoon="014 55 66 77", rol="Beslisser",
        linkedin="linkedin.com/in/ilsemertens"))
    con["koen"] = db.voeg_toe("contacten", dict(
        organisatie_id=org["logistiek"], naam="Koen De Smet", functie="Technisch verantwoordelijke",
        email="koen.desmet@transkempen.be", telefoon="0498 11 22 33", rol="Technisch contact"))
    con["peeters"] = db.voeg_toe("contacten", dict(
        organisatie_id=org["serre"], naam="Jan Peeters", functie="Bedrijfsleider",
        email="jan@tuinbouwpeeters.be", telefoon="0477 88 99 00", rol="Beslisser"))
    con["tom"] = db.voeg_toe("contacten", dict(
        organisatie_id=org["argona"], naam="Tom Verhoeven", functie="Projectleider",
        email="tom@argona.be", telefoon="0468 44 55 66", rol="Installateur",
        notities="Vast aanspreekpunt voor doorverwijzingen."))
    con["sara"] = db.voeg_toe("contacten", dict(
        organisatie_id=org["solora"], naam="Sara Wouters", functie="O&M Manager",
        email="sara@solora.be", telefoon="0493 77 66 55", rol="O&M-contact"))

    # --- sites ---
    site = {}
    site["stal"] = db.voeg_toe("sites", dict(
        naam="Melkveestal Geel", adres="Zandstraat 12, Geel",
        organisatie_id=org["hoeve"], aantal_panelen=420, kwp=170.0,
        daktype="Golfplaten (asbestvrij)", hellingsgraad="15°",
        bereikbaarheid="Goed – verharde toegangsweg", waterpunt=1, hoogtewerker=0,
        veiligheid="Let op nok, valbeveiliging verplicht",
        vervuiling="Landbouwstof", frequentie="Jaarlijks",
        notities="Robot geschikt, vorige reiniging juni vorig jaar."))
    site["magazijn"] = db.voeg_toe("sites", dict(
        naam="Magazijn Westerlo", adres="Industrieweg 45, Westerlo",
        organisatie_id=org["logistiek"], partner_id=org["argona"],
        aantal_panelen=1800, kwp=740.0,
        daktype="Plat dak (EPDM)", hellingsgraad="10° opstelling",
        bereikbaarheid="Ladderpunt + intern trappenhuis", waterpunt=0, hoogtewerker=1,
        veiligheid="Randbeveiliging aanwezig",
        vervuiling="Industrie", frequentie="Jaarlijks",
        notities="Waterpunt ontbreekt – eigen watertank voorzien."))
    site["serre1"] = db.voeg_toe("sites", dict(
        naam="Serre Hoogstraten", adres="Kanaaldijk 8, Hoogstraten",
        organisatie_id=org["serre"], aantal_panelen=650, kwp=260.0,
        daktype="Schuin dak loods naast serres", hellingsgraad="20°",
        bereikbaarheid="Smalle doorgang, opletten met aanhanger", waterpunt=1, hoogtewerker=1,
        veiligheid="Breekbare lichtplaten in dak!",
        vervuiling="Korstmos", frequentie="Na inspectie",
        notities="Korstmos: LRA-voorbehandeling + hardere borstel nodig."))
    site["woning"] = db.voeg_toe("sites", dict(
        naam="Woning Herentals", adres="Lindelaan 3, Herentals",
        organisatie_id=org["particulier"], aantal_panelen=24, kwp=9.6,
        daktype="Pannen", hellingsgraad="35°",
        bereikbaarheid="Vanaf ladder", waterpunt=1, hoogtewerker=0,
        veiligheid="Standaard", vervuiling="Stof", frequentie="Eenmalig"))

    # --- deals ---
    deal = {}
    deal["trans"] = db.voeg_toe("deals", dict(
        titel="Reiniging magazijn TransKempen (1.800 panelen)",
        organisatie_id=org["logistiek"], partner_id=org["argona"],
        site_id=site["magazijn"], contact_id=con["ilse"],
        waarde=5400, kans=60, bron="Partner / installateur", deadline=_d(21),
        stadium="Plaatsbezoek gepland", prioriteit="Hoog"))
    deal["serre"] = db.voeg_toe("deals", dict(
        titel="Korstmosbehandeling Tuinbouw Peeters",
        organisatie_id=org["serre"], site_id=site["serre1"], contact_id=con["peeters"],
        waarde=3250, kans=45, bron="Eigen prospectie", deadline=_d(30),
        stadium="Offerte verstuurd", prioriteit="Normaal"))
    deal["hoeve"] = db.voeg_toe("deals", dict(
        titel="Jaarlijkse reiniging Hoeve Van den Broeck",
        organisatie_id=org["hoeve"], site_id=site["stal"], contact_id=con["bart"],
        waarde=1150, kans=90, bron="Doorverwijzing", deadline=_d(14),
        stadium="Goedgekeurd / in te plannen", prioriteit="Normaal"))
    deal["solora"] = db.voeg_toe("deals", dict(
        titel="Kaderafspraak O&M-sites Solora",
        organisatie_id=org["solora"], partner_id=org["solora"], contact_id=con["sara"],
        waarde=8000, kans=25, bron="Eigen prospectie", deadline=_d(45),
        stadium="Te kwalificeren", prioriteit="Hoog"))
    deal["part"] = db.voeg_toe("deals", dict(
        titel="Reiniging woning Familie Janssens",
        organisatie_id=org["particulier"], site_id=site["woning"],
        waarde=280, kans=100, bron="Website", deadline=_d(-20),
        stadium="Afgerond", prioriteit="Laag"))

    # --- acties ---
    db.voeg_toe("acties", dict(
        datum=_d(1), prioriteit="Hoog", organisatie_id=org["logistiek"],
        site_id=site["magazijn"], partner_id=org["argona"], deal_id=deal["trans"],
        actie="Plaatsbezoek uitvoeren + verslag invullen", status="Open"))
    db.voeg_toe("acties", dict(
        datum=_d(-2), prioriteit="Normaal", organisatie_id=org["serre"],
        deal_id=deal["serre"], actie="Offerte opvolgen (verstuurd op " + _d(-9) + ")",
        status="Open"))
    db.voeg_toe("acties", dict(
        datum=_d(3), prioriteit="Normaal", organisatie_id=org["hoeve"],
        deal_id=deal["hoeve"], actie="Uitvoeringsdatum plannen met Bart", status="Open"))
    db.voeg_toe("acties", dict(
        datum=_d(7), prioriteit="Laag", partner_id=org["solora"], deal_id=deal["solora"],
        actie="Sitelijst opvragen bij Sara (Solora)", status="Wacht op partner"))
    db.voeg_toe("acties", dict(
        datum=_d(-30), prioriteit="Laag", organisatie_id=org["particulier"],
        deal_id=deal["part"], actie="Factuur versturen", status="Klaar"))

    # --- plaatsbezoek ---
    db.voeg_toe("plaatsbezoeken", dict(
        deal_id=deal["serre"], site_id=site["serre1"], datum=_d(-14),
        aanwezigen="Pieter, Jan Peeters",
        technische_opmerkingen="Zware korstmosvorming op noordzijde. Panelen 2014, geen microscheuren zichtbaar.",
        bereikbaarheid="Smalle toegang, hoogtewerker 16 m nodig aan achterzijde",
        wateraansluiting="Waterpunt in loods aanwezig, debiet ok",
        veiligheid="Lichtplaten markeren, niet betreden",
        materialen="LRA-voorbehandeling, borstel 0,5 mm, watertank reserve",
        hoogtewerker=1, reinigingstijd="1,5 dag", panelen_gecontroleerd=650,
        vervuilingsgraad="Zwaar (korstmos 40% oppervlak)",
        conclusie="Chemische voorbehandeling noodzakelijk, twee werkgangen.",
        advies="Behandeling in droge periode plannen, nadien jaarlijks onderhoud aanraden."))

    # --- offertes ---
    db.voeg_toe("offertes", dict(
        deal_id=deal["serre"], site_id=site["serre1"], nummer="OFF-2026-014",
        aantal_panelen=650, oppervlakte=1300, prijs_per_paneel=4.2, totaalprijs=3250,
        transport=90, waterkost=60, hoogtewerker_kost=350,
        speciale_vervuiling="Korstmos – LRA-voorbehandeling", coating=0,
        opmerkingen="Prijs incl. tweede werkgang.", status="Verstuurd", datum=_d(-9)))
    db.voeg_toe("offertes", dict(
        deal_id=deal["hoeve"], site_id=site["stal"], nummer="OFF-2026-011",
        aantal_panelen=420, oppervlakte=840, prijs_per_paneel=2.6, totaalprijs=1150,
        transport=40, waterkost=0, hoogtewerker_kost=0,
        speciale_vervuiling="Landbouwstof", coating=0,
        status="Goedgekeurd", datum=_d(-20)))

    # --- jobs ---
    db.voeg_toe("jobs", dict(
        deal_id=deal["hoeve"], site_id=site["stal"], datum=_d(10),
        team="Pieter", materiaal="Tailai L1, borstels standaard, osmosewater 1.000 l",
        water="Waterpunt klant + osmose", robot=1, hoogtewerker=0,
        veiligheidsinstructies="Valbeveiliging nok, VCA-regels", status="Gepland"))
    db.voeg_toe("jobs", dict(
        deal_id=deal["part"], site_id=site["woning"], datum=_d(-25),
        team="Pieter", materiaal="Telescoopsteel + osmose", water="Waterpunt klant",
        robot=0, hoogtewerker=0, status="Uitgevoerd",
        werkverslag="24 panelen gereinigd, opbrengstverbetering zichtbaar op omvormer."))

    # --- communicatie ---
    db.voeg_toe("communicatie", dict(
        datum=_d(-3), type="Telefoongesprek", organisatie_id=org["logistiek"],
        partner_id=org["argona"], deal_id=deal["trans"], contact_id=con["ilse"],
        samenvatting="Ilse bevestigt interesse, wil plaatsbezoek volgende week.",
        volgende_stap="Plaatsbezoek uitvoeren en verslag maken."))
    db.voeg_toe("communicatie", dict(
        datum=_d(-9), type="Offerte", organisatie_id=org["serre"], deal_id=deal["serre"],
        contact_id=con["peeters"], samenvatting="Offerte OFF-2026-014 verstuurd per e-mail.",
        volgende_stap="Opvolgen binnen 7 dagen."))
    db.voeg_toe("communicatie", dict(
        datum=_d(-6), type="E-mail", partner_id=org["argona"], contact_id=con["tom"],
        samenvatting="Tom (Argona) geeft nieuwe lead door: TransKempen, contact Ilse Mertens.",
        volgende_stap="Lead omzetten naar deal – gebeurd."))
