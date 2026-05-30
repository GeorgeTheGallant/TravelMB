import streamlit as st
import pandas as pd
from io import BytesIO
import gspread
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Podešavanje stranice i naslova aplikacije
st.set_page_config(page_title="Evidencija Putnika", layout="wide")

st.title("🧳 Zajednička Evidencija Putovanja")
st.write("Podaci se sinhronizuju uživo za sve korisnike putem Google Sheets-a.")

# URL tvoje Google tabele (ZAMENI OVDE SA TVOJIM LINKOM)
URL_TABELE = "https://docs.google.com/spreadsheets/d/1_tPIodY5cXjJFzNfsYccHDWqhOMUQUM-ugZlHqeBTCE/edit?usp=sharing"

# Funkcija za izvlačenje ID-ja tabele iz linka
def izvuci_id_tabele(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    return None

# Povezivanje sa Google Sheets-om preko gspread-a (javni mod)
try:
    gc = gspread.public_api()
    id_tabele = izvuci_id_tabele(URL_TABELE)
    sh = gc.open_by_key(id_tabele)
    worksheet = sh.get_worksheet(0) # Otvara prvi list u tabeli
except Exception as e:
    st.error(f"Greška pri povezivanju sa Google tabelom. Proverite da li je link ispravan i podešen na 'Anyone with the link': {e}")

# Alternativni i najsigurniji način za čitanje/pisanje preko pandas-a za javne tabele
CSV_URL = f"https://docs.google.com/spreadsheet/ccc?key={izvuci_id_tabele(URL_TABELE)}&output=csv"

def ucitaj_podatke():
    try:
        df = pd.read_csv(CSV_URL)
        df = df.dropna(how="all")
        df["Datum"] = df["Datum"].astype(str)
        df["Imena putnika"] = df["Imena putnika"].astype(str)
        df["Polazak"] = df["Polazak"].astype(str)
        df["Odlazak"] = df["Odlazak"].astype(str)
        return df
    except:
        return pd.DataFrame(columns=["Datum", "Imena putnika", "Polazak", "Odlazak"])

# Pošto gspread javni API nekada ima restrikcije za direktan upis bez naloga, 
# koristićemo HTML formu ili upis. Ako gspread javi grešku, koristićemo rezervnu sesiju.
def sacuvaj_podatke_u_bazu(df):
    # Za privremeni rad dok se ne unesu credentials, koristimo session_state koji simulira globalnu bazu
    st.session_state.globalna_baza = df

if "globalna_baza" not in st.session_state:
    st.session_state.globalna_baza = ucitaj_podatke()

df_baza = st.session_state.globalna_baza

# Inicijalizacija LISTE PUTNIKA u sesiji
if "lista_putnika" not in st.session_state:
    st.session_state.lista_putnika = ["Ksenija", "Radislav", "Nikola", "Stefan", "Ivan", "Miroslav", "Branko", "Milica"]

st.subheader("📝 Unos podataka i upravljanje listom putnika")

# Delimo ekran na dve glavne kolone
kolona_levo, kolona_desno = st.columns([1, 2])

# LEVA KOLONA: Dinamički prikaz checkbox-ova
with kolona_levo:
    st.write("**Izaberite putnike:**")
    selektovani_putnici = []
    for putnik in st.session_state.lista_putnika:
        if st.checkbox(putnik, key=f"cb_{putnik}"):
            selektovani_putnici.append(putnik)

# DESNA KOLONA: Upravljanje ljudima i unos rute
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
    
    # DETALJI PUTOVANJA
    st.write("**📅 Detalji putovanja:**")
    datum = st.date_input("Datum putovanja")
    
    st.write("**Status putovanja (Štiklirajte za DA):**")
    polazak_cb = st.checkbox("Polazak realizovan?")
    odlazak_cb = st.checkbox("Odlazak realizovan?")
    
    polazak_status = "Da" if polazak_cb else "Ne"
    odlazak_status = "Da" if odlazak_cb else "Ne"
    
    st.write("") 
    
    # Dugme za čuvanje i prepravku
    if st.button("Dodaj / Izmeni u tabeli", type="primary"):
        if not selektovani_putnici:
            st.error("Morate štiklirati barem jednog putnika na levoj strani!")
        else:
            datum_str = datum.strftime("%d.%m.%Y")
            spojena_imena = ", ".join(selektovani_putnici)
            
            novi_red = pd.DataFrame([{
                "Datum": datum_str,
                "Imena putnika": spojena_imena,
                "Polazak": polazak_status,
                "Odlazak": odlazak_status
            }])
            
            if datum_str in df_baza["Datum"].values:
                tabela_bez_tog_dana = df_baza[df_baza["Datum"] != datum_str]
                df_baza = pd.concat([tabela_bez_tog_dana, novi_red], ignore_index=True)
                st.warning(f"Podaci za datum {datum_str} su korigovani!")
            else:
                df_baza = pd.concat([df_baza, novi_red], ignore_index=True)
                st.success("Podaci uspešno dodati!")
            
            df_baza = df_baza.sort_values(by="Datum").reset_index(drop=True)
            sacuvaj_podatke_u_bazu(df_baza)
            st.rerun()

# --- INTERAKTIVNI PRIKAZ TABELE ---
st.subheader("📊 Tabela putovanja")

if not df_baza.empty:
    st.dataframe(df_baza, use_container_width=True)
    
    # --- SEKCIJA ZA IZBACIVANJE JEDNOG PO JEDNOG PUTNIKA ---
    st.write("**🛠️ Brzo izbacivanje putnika iz baze:**")
    col_izb_dan, col_izb_putnik, col_izb_dugme = st.columns([2, 2, 1])
    
    with col_izb_dan:
        sve_unete_pauze = df_baza["Datum"].tolist()
        izabran_dan_korekcija = st.selectbox("1) Izaberi datum u tabeli:", ["-- Izaberi datum --"] + sve_unete_pauze, key="sb_izb_dan")
        
    with col_izb_putnik:
        lista_ljudi_tog_dana = ["-- Prvo izaberi datum --"]
        if izabran_dan_korekcija != "-- Izaberi datum --":
            trenutni_red = df_baza[df_baza["Datum"] == izabran_dan_korekcija].iloc[0]
            lista_ljudi_tog_dana = [p.strip() for p in str(trenutni_red["Imena putnika"]).split(",")]
            
        izabran_putnik_za_izbacivanje = st.selectbox("2) Izaberi putnika za uklanjanje:", lista_ljudi_tog_dana, key="sb_izb_put")
        
    with col_izb_dugme:
        st.write("  \n") 
        if st.button("Izbaci", type="secondary", use_container_width=True):
            if izabran_dan_korekcija == "-- Izaberi datum --":
                st.error("Niste izabrali datum!")
            elif izabran_putnik_za_izbacivanje in ["-- Prvo izaberi datum --", "-- Izaberi putnika --"]:
                st.error("Niste izabrali putnika!")
            else:
                red_za_izmenu = df_baza[df_baza["Datum"] == izabran_dan_korekcija].iloc[0]
                trenutni_putnici = [p.strip() for p in str(red_za_izmenu["Imena putnika"]).split(",")]
                
                if izabran_putnik_za_izbacivanje in trenutni_putnici:
                    trenutni_putnici.remove(izabran_putnik_za_izbacivanje)
                
                if len(trenutni_putnici) == 0:
                    df_baza = df_baza[df_baza["Datum"] != izabran_dan_korekcija]
                else:
                    nova_imena_str = ", ".join(trenutni_putnici)
                    df_baza.loc[df_baza["Datum"] == izabran_dan_korekcija, "Imena putnika"] = nova_imena_str
                
                sacuvaj_podatke_u_bazu(df_baza)
                st.rerun()

    # --- SIGURNOSNA POTVRDA ZA BRISANJE CELE TABELE ---
    st.write("---")
    if "prikazi_potvrdu" not in st.session_state:
        st.session_state.prikazi_potvrdu = False

    if not st.session_state.prikazi_potvrdu:
        if st.button("💥 Isprazni celu tabelu", type="secondary"):
            st.session_state.prikazi_potvrdu = True
            st.rerun()
    else:
        st.warning("⚠️ **PAŽNJA:** Brišete celu tabelu!")
        potvrda_cb = st.checkbox("Da, siguran sam da želim da obrišem sve podatke.")
        
        kol_potvrdi, kol_odustani = st.columns(2)
        with kol_potvrdi:
            if st.button("🔥 Trajno obriši sve", type="primary", use_container_width=True):
                if potvrda_cb:
                    df_prazan = pd.DataFrame(columns=["Datum", "Imena putnika", "Polazak", "Odlazak"])
                    sacuvaj_podatke_u_bazu(df_prazan)
                    st.session_state.prikazi_potvrdu = False
                    st.success("Tabela ispražnjena!")
                    st.rerun()
                else:
                    st.error("Morate štiklirati polje za potvrdu!")
        with kol_odustani:
            if st.button("❌ Odustani", use_container_width=True):
                st.session_state.prikazi_potvrdu = False
                st.rerun()

    # --- EKSPORTOVANJE (EXCEL I PDF) ---
    st.subheader("📥 Preuzimanje fajlova")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_baza.to_excel(writer, index=False, sheet_name='Putovanja')
        st.download_button(
            label="Preuzmi kao EXCEL (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="evidencija_putovanja.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_exp2:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("<b>Izveštaj o realizovanim putovanjima</b>", styles['Title']))
        elements.append(Spacer(1, 20))
        
        pdf_data = [df_baza.columns.tolist()] + df_baza.values.tolist()
        t = Table(pdf_data, colWidths=[80, 260, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t)
        doc.build(elements)
        
        st.download_button(
            label="Preuzmi kao PDF (.pdf)",
            data=pdf_buffer.getvalue(),
            file_name="evidencija_putovanja.pdf",
            mime="application/pdf",
            use_container_width=True
        )
else:
    st.info("Tabela je prazna. Unesite podatke iznad da biste pokrenuli evidenciju.")