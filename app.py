import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Podešavanje stranice i naslova aplikacije
st.set_page_config(page_title="Evidencija Putnika", layout="wide")

st.title("🧳 Pametna Aplikacija za Evidenciju Putovanja")
st.write("Upravljajte putovanjima bez straha od grešaka. Jednim klikom izbacite putnika iz bilo kog dana.")

# 1) Inicijalizacija baze podataka (tabela putovanja)
if "podaci_o_putovanjima" not in st.session_state:
    st.session_state.podaci_o_putovanjima = pd.DataFrame(
        columns=["Datum", "Imena putnika", "Polazak", "Odlazak"]
    )

# 2) Inicijalizacija LISTE PUTNIKA u sesiji
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
            postojeca_tabela = st.session_state.podaci_o_putovanjima
            spojena_imena = ", ".join(selektovani_putnici)
            
            novi_red = pd.DataFrame([{
                "Datum": datum_str,
                "Imena putnika": spojena_imena,
                "Polazak": polazak_status,
                "Odlazak": odlazak_status
            }])
            
            if datum_str in postojeca_tabela["Datum"].values:
                tabela_bez_tog_dana = postojeca_tabela[postojeca_tabela["Datum"] != datum_str]
                st.session_state.podaci_o_putovanjima = pd.concat([tabela_bez_tog_dana, novi_red], ignore_index=True)
                st.warning(f"Podaci za datum {datum_str} su uspešno korigovani!")
            else:
                st.session_state.podaci_o_putovanjima = pd.concat([postojeca_tabela, novi_red], ignore_index=True)
                st.success("Podaci uspešno dodati u tabelu!")
            
            # Sortiranje po datumu
            st.session_state.podaci_o_putovanjima = st.session_state.podaci_o_putovanjima.sort_values(by="Datum").reset_index(drop=True)
            st.rerun()

# --- INTERAKTIVNI PRIKAZ TABELE ---
st.subheader("📊 Tabela putovanja")
df = st.session_state.podaci_o_putovanjima

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    # --- SEKCIJA ZA IZBACIVANJE JEDNOG PO JEDNOG PUTNIKA (Sada ispravljeno) ---
    st.write("**🛠️ Brzo izbacivanje putnika iz tabele:**")
    
    col_izb_dan, col_izb_putnik, col_izb_dugme = st.columns([2, 2, 1])
    
    with col_izb_dan:
        sve_unete_pauze = df["Datum"].tolist()
        izabran_dan_korekcija = st.selectbox("1) Izaberi datum u tabeli:", ["-- Izaberi datum --"] + sve_unete_pauze, key="sb_izb_dan")
        
    with col_izb_putnik:
        lista_ljudi_tog_dana = ["-- Prvo izaberi datum --"]
        
        if izabran_dan_korekcija != "-- Izaberi datum --":
            trenutni_red = df[df["Datum"] == izabran_dan_korekcija].iloc[0]
            lista_ljudi_tog_dana = [p.strip() for p in trenutni_red["Imena putnika"].split(",")]
            
        izabran_putnik_za_izbacivanje = st.selectbox("2) Izaberi putnika za uklanjanje:", lista_ljudi_tog_dana, key="sb_izb_put")
        
    with col_izb_dugme:
        st.write("  \n") 
        if st.button("Izbaci", type="secondary", use_container_width=True):
            if izabran_dan_korekcija == "-- Izaberi datum --":
                st.error("Niste izabrali datum!")
            elif izabran_putnik_za_izbacivanje in ["-- Prvo izaberi datum --", "-- Izaberi putnika --"]:
                st.error("Niste izabrali putnika!")
            else:
                red_za_izmenu = df[df["Datum"] == izabran_dan_korekcija].iloc[0]
                trenutni_putnici = [p.strip() for p in red_za_izmenu["Imena putnika"].split(",")]
                
                trenutni_putnici.remove(izabran_putnik_za_izbacivanje)
                
                if len(trenutni_putnici) == 0:
                    st.session_state.podaci_o_putovanjima = df[df["Datum"] != izabran_dan_korekcija]
                    st.warning(f"Izbačen je poslednji putnik. Red za datum {izabran_dan_korekcija} je obrisan.")
                else:
                    nova_imena_str = ", ".join(trenutni_putnici)
                    df.loc[df["Datum"] == izabran_dan_korekcija, "Imena putnika"] = nova_imena_str
                    st.session_state.podaci_o_putovanjima = df
                    st.success(f"Putnik {izabran_putnik_za_izbacivanje} je uspešno izbačen iz datuma {izabran_dan_korekcija}!")
                
                st.rerun()

    # --- KOMPLETNO BRISANJE TABELE ---
    st.write("  \n")
    if st.button("💥 Isprazni celu tabelu", type="secondary"):
        st.session_state.podaci_o_putovanjima = pd.DataFrame(
            columns=["Datum", "Imena putnika", "Polazak", "Odlazak"]
        )
        st.rerun()

    # --- EKSPORTOVANJE (EXCEL I PDF) ---
    st.subheader("📥 Preuzimanje fajlova")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Putovanja')
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
        
        pdf_data = [df.columns.tolist()] + df.values.tolist()
        
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
    st.info("Tabela je trenutno prazna. Selektujte podatke iznad da biste započeli evidenciju.")