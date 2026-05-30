import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
from github import Github
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Podešavanje stranice i naslova aplikacije
st.set_page_config(page_title="Evidencija Putnika", layout="wide")

st.title("🧳 Zajednička Evidencija Putovanja")
st.write("Podaci su sinhronizovani uživo za sve uređaje preko centralne baze.")

# Povezivanje sa GitHub-om preko Secrets-a
try:
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    g = Github(token)
    repo = g.get_repo(repo_name)
except Exception as e:
    st.error("Problem sa Streamlit Secrets podešavanjima za GitHub. Proverite TOKEN i REPO_NAME.")

def ucitaj_podatke():
    try:
        # Pokušavamo da povučemo baza.csv sa GitHub-a
        file_content = repo.get_contents("baza.csv")
        data_str = file_content.decoded_content.decode("utf-8")
        df = pd.read_csv(StringIO(data_str))
        df = df.dropna(how="all")
        df["Datum"] = df["Datum"].astype(str)
        df["Imena putnika"] = df["Imena putnika"].astype(str)
        df["Polazak"] = df["Polazak"].astype(str)
        df["Odlazak"] = df["Odlazak"].astype(str)
        return df
    except:
        # Ako fajl još ne postoji, vraćamo praznu tabelu
        return pd.DataFrame(columns=["Datum", "Imena putnika", "Polazak", "Odlazak"])

def sacuvaj_podatke(df):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    try:
        # Ako fajl postoji, ažuriramo ga
        file_content = repo.get_contents("baza.csv")
        repo.update_file("baza.csv", "Automatsko osvežavanje baze putnika", csv_data, file_content.sha)
    except:
        # Ako fajl ne postoji, kreiramo ga prvi put
        repo.create_file("baza.csv", "Inicijalizacija baze putnika", csv_data)

# Učitavanje trenutnog stanja baze sa GitHub-a (ttl=0 efekat)
df_baza = ucitaj_podatke()

# Inicijalizacija LISTE PUTNIKA u sesiji
if "lista_putnika" not in st.session_state:
    st.session_state.lista_putnika = ["Ksenija", "Radislav", "Nikola", "Stefan", "Ivan", "Miroslav", "Branko", "Milica"]

st.subheader("📝 Unos podataka i upravljanje listom putnika")

kolona_levo, kolona_desno = st.columns([1, 2])

with kolona_levo:
    st.write("**Izaberite putnike:**")
    selektovani_putnici = []
    for putnik in st.session_state.lista_putnika:
        if st.checkbox(putnik, key=f"cb_{putnik}"):
            selektovani_putnici.append(putnik)

with kolona_desno:
    st.write("**⚙️ Upravljanje listom putnika (Trenutno: {}/15):**".format(len(st.session_state.lista_putnika)))
    kolona_dodaj, kolona_obrisi = st.columns(2)
    
    with kolona_dodaj:
        novo_ime = st.text_input("➕ Dodaj novog putnika:", placeholder="Upiši ime", key="txt_novo_ime")
        if st.button("Potvrdi dodavanje"):
            if not novo_ime.strip():
                st.error("Ime ne može biti prazno!")
            elif len(st.session_state.lista_putnika) >= 15:
                st.error("Dostignut je maksimalan broj od 15 putnika!")
            elif novo_ime.strip() in st.session_state.lista_putnika:
                st.warning(f"Putnik {novo_ime} već postoji na listi.")
            else:
                st.session_state.lista_putnika.append(novo_ime.strip())
                st.success(f"Putnik {novo_ime} je dodat na listu!")
                st.rerun()
                
    with kolona_obrisi:
        putnik_za_brisanje = st.selectbox("❌ Ukloni putnika sa liste:", ["-- Izaberi --"] + st.session_state.lista_putnika)
        if st.button("Potvrdi brisanje"):
            if putnik_za_brisanje != "-- Izaberi --":
                st.session_state.lista_putnika.remove(putnik_za_brisanje)
                st.success(f"Putnik {putnik_za_brisanje} je uspešno uklonjen sa liste!")
                st.rerun()
            else:
                st.error("Izaberite putnika kojeg želite da obrišete.")

    st.write("---") 
    st.write("**📅 Detalji putovanja:**")
    datum = st.date_input("Datum putovanja")
    
    polazak_cb = st.checkbox("Polazak realizovan?")
    odlazak_cb = st.checkbox("Odlazak realizovan?")
    polak_status = "Da" if polazak_cb else "Ne"
    odlazak_status = "Da" if odlazak_cb else "Ne"
    
    if st.button("Dodaj / Izmeni u tabeli", type="primary"):
        if not selektovani_putnici:
            st.error("Morate štiklirati barem jednog putnika!")
        else:
            datum_str = datum.strftime("%d.%m.%Y")
            spojena_imena = ", ".join(selektovani_putnici)
            
            novi_red = pd.DataFrame([{
                "Datum": datum_str,
                "Imena putnika": spojena_imena,
                "Polazak": polak_status,
                "Odlazak": odlazak_status
            }])
            
            if datum_str in df_baza["Datum"].values:
                tabela_bez_tog_dana = df_baza[df_baza["Datum"] != datum_str]
                df_baza = pd.concat([tabela_bez_tog_dana, novi_red], ignore_index=True)
            else:
                df_baza = pd.concat([df_baza, novi_red], ignore_index=True)
            
            df_baza = df_baza.sort_values(by="Datum").reset_index(drop=True)
            sacuvaj_podatke(df_baza)
            st.success("Podaci uspešno osveženi u zajedničkoj bazi!")
            st.rerun()

# --- PRIKAZ TABELE ---
st.subheader("📊 Tabela putovanja (Sinhronizovano uživo)")

if not df_baza.empty:
    st.dataframe(df_baza, use_container_width=True)
    
    st.write("**🛠️ Brzo izbacivanje putnika iz baze:**")
    col_izb_dan, col_izb_putnik, col_izb_dugme = st.columns([2, 2, 1])
    
    with col_izb_dan:
        sve_unete_pauze = df_baza["Datum"].tolist()
        izabran_dan_korekcija = st.selectbox("1) Izaberi datum:", ["-- Izaberi datum --"] + sve_unete_pauze, key="sb_izb_dan")
        
    with col_izb_putnik:
        lista_ljudi_tog_dana = ["-- Prvo izaberi datum --"]
        if izabran_dan_korekcija != "-- Izaberi datum --":
            trenutni_red = df_baza[df_baza["Datum"] == izabran_dan_korekcija].iloc[0]
            lista_ljudi_tog_dana = [p.strip() for p in str(trenutni_red["Imena putnika"]).split(",")]
            
        izabran_putnik_za_izbacivanje = st.selectbox("2) Izaberi putnika:", lista_ljudi_tog_dana, key="sb_izb_put")
        
    with col_izb_dugme:
        st.write("  \n") 
        if st.button("Izbaci", type="secondary", use_container_width=True):
            if izabran_dan_korekcija == "-- Izaberi datum --" or izabran_putnik_za_izbacivanje in ["-- Prvo izaberi datum --", "-- Izaberi putnika --"]:
                st.error("Izaberite ispravne podatke!")
            else:
                red_za_izmenu = df_baza[df_baza["Datum"] == izabran_dan_korekcija].iloc[0]
                trenutni_putnici = [p.strip() for p in str(red_za_izmenu["Imena putnika"]).split(",")]
                
                if izabran_putnik_za_izbacivanje in trenutni_putnici:
                    trenutni_putnici.remove(izabran_putnik_za_izbacivanje)
                
                if len(trenutni_putnici) == 0:
                    df_baza = df_baza[df_baza["Datum"] != izabran_dan_korekcija]
                else:
                    nova_imena_str = ", ".join(trenutni_putnici)
                    df_baza.loc[df_baza["Datum"] == izabales_dan_korekcija if 'izabales_dan_korekcija' in locals() else df_baza["Datum"] == izabran_dan_korekcija, "Imena putnika"] = nova_imena_str
                
                df_baza = df_baza.sort_values(by="Datum").reset_index(drop=True)
                sacuvaj_podatke(df_baza)
                st.rerun()

    # --- POTVRDA BRISANJA ---
    st.write("---")
    if "prikazi_potvrdu" not in st.session_state:
        st.session_state.prikazi_potvrdu = False

    if not st.session_state.prikazi_potvrdu:
        if st.button("💥 Isprazni celu tabelu", type="secondary"):
            st.session_state.prikazi_potvrdu = True
            st.rerun()
    else:
        st.warning("⚠️ Želite da obrišete celu zajedničku tabelu!")
        potvrda_cb = st.checkbox("Potvrđujem brisanje.")
        kol_potvrdi, kol_odustani = st.columns(2)
        with kol_potvrdi:
            if st.button("🔥 Obriši sve", type="primary", use_container_width=True):
                if potvrda_cb:
                    df_prazan = pd.DataFrame(columns=["Datum", "Imena putnika", "Polazak", "Odlazak"])
                    sacuvaj_podatke(df_prazan)
                    st.session_state.prikazi_potvrdu = False
                    st.rerun()
        with kol_odustani:
            if st.button("❌ Odustani", use_container_width=True):
                st.session_state.prikazi_potvrdu = False
                st.rerun()

    # --- EKSPORTOVANJE ---
    st.subheader("📥 Preuzimanje fajlova")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_baza.to_excel(writer, index=False, sheet_name='Putovanja')
        st.download_button("Preuzmi kao EXCEL (.xlsx)", excel_buffer.getvalue(), "evidencija_putovanja.xlsx", use_container_width=True)
    with col_exp2:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = [Paragraph("<b>Izveštaj o realizovanim putovanjima</b>", getSampleStyleSheet()['Title']), Spacer(1, 20)]
        t = Table([df_baza.columns.tolist()] + df_baza.values.tolist(), colWidths=[80, 260, 80, 80])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkblue), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        doc.build(elements)
        st.download_button("Preuzmi kao PDF (.pdf)", pdf_buffer.getvalue(), "evidencija_putovanja.pdf", use_container_width=True)
else:
    st.info("Zajednička tabela je trenutno prazna. Unesite podatke iznad.")